from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.case.courtlistener import fetch_cluster, lookup_citation

from .courtlistener import count_forward_citations
from .jurisdictions import STATES
from .models import CitationVerification, ResearchQuery, ResearchResult
from .tasks import (
    assess_single_citation,
    process_research_query,
    refine_research_query,
    review_more_citations,
    review_result,
    sanitize_query,
)


def research_permission_required(view_func):
    """Check user has research permission."""

    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_admin or request.user.perm_research):
            return HttpResponse("Permission denied", status=403)
        return view_func(request, *args, **kwargs)

    wrapper.__name__ = view_func.__name__
    return wrapper


@research_permission_required
def research_index(request):
    return render(
        request,
        "research/search.html",
        {
            "app": "research",
            "subapp": "search",
            "states": STATES,
        },
    )


@research_permission_required
def research_search(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    query_text = request.POST.get("query_text", "").strip()
    state = request.POST.get("state", "")
    include_federal = request.POST.get("include_federal") == "on"

    if not query_text:
        return HttpResponse(
            '<div class="research-error">Please enter a search query.</div>'
        )

    query = ResearchQuery.objects.create(
        query_text=query_text,
        state=state,
        include_federal=include_federal,
        status="pending",
        created_by=request.user,
    )

    # Start background refinement (pauses for user review)
    refine_research_query(query.id)

    # Return the results shell with polling
    return render(
        request,
        "research/results.html",
        {"query": query},
    )


@research_permission_required
def research_results(request, query_id):
    query = get_object_or_404(ResearchQuery, pk=query_id, created_by=request.user)
    results = query.results.all()
    return render(
        request,
        "research/results.html",
        {"query": query, "results": results},
    )


@research_permission_required
def result_status(request, result_id):
    result = get_object_or_404(
        ResearchResult, pk=result_id, query__created_by=request.user
    )
    return render(request, "research/result-row.html", {"result": result})


@research_permission_required
def query_status(request, query_id):
    query = get_object_or_404(ResearchQuery, pk=query_id, created_by=request.user)
    results = query.results.all()
    return render(
        request,
        "research/results.html",
        {"query": query, "results": results},
    )


@research_permission_required
def research_detail(request, query_id):
    query = get_object_or_404(ResearchQuery, pk=query_id, created_by=request.user)
    results = query.results.all()
    return render(
        request,
        "research/search.html",
        {
            "app": "research",
            "subapp": "search",
            "states": STATES,
            "active_query": query,
            "results": results,
        },
    )


@research_permission_required
def research_history(request):
    queries = ResearchQuery.objects.filter(created_by=request.user)[:50]
    return render(
        request,
        "research/history.html",
        {
            "app": "research",
            "subapp": "history",
            "queries": queries,
        },
    )


# ── Review tab ──────────────────────────────────────────────────────────────


@research_permission_required
def research_review_tab(request):
    result_id = request.GET.get("result")
    context = {
        "app": "research",
        "subapp": "review",
    }
    if result_id:
        result = get_object_or_404(
            ResearchResult, pk=result_id, query__created_by=request.user
        )
        context["result"] = result
    else:
        reviewed_results = ResearchResult.objects.filter(
            query__created_by=request.user,
            verify_status="complete",
        ).select_related("query")
        context["reviewed_results"] = reviewed_results
    return render(request, "research/review.html", context)


@research_permission_required
def research_review_status(request, result_id):
    result = get_object_or_404(
        ResearchResult, pk=result_id, query__created_by=request.user
    )
    return render(request, "research/review-content.html", {"result": result})


@research_permission_required
def research_review(request, result_id):
    """Start review from a search result (POST)."""
    if request.method != "POST":
        return HttpResponse(status=405)

    result = get_object_or_404(
        ResearchResult, pk=result_id, query__created_by=request.user
    )

    # Start background review
    result.verify_status = "verifying"
    result.save(update_fields=["verify_status"])
    review_result(result.id)

    return HttpResponseRedirect(f"{reverse('research:review-tab')}?result={result.id}")


@research_permission_required
def research_review_lookup(request):
    """Look up a citation and start review (POST)."""
    if request.method != "POST":
        return HttpResponse(status=405)

    citation_text = request.POST.get("citation", "").strip()
    if not citation_text:
        return HttpResponseRedirect(reverse("research:review-tab"))

    # Look up citation on CourtListener
    lookup = lookup_citation(citation_text)
    if not lookup.found:
        context = {
            "app": "research",
            "subapp": "review",
            "lookup_error": lookup.error or "Citation not found.",
            "lookup_citation": citation_text,
        }
        return render(request, "research/review.html", context)

    # Get forward citation count
    fwd_count = None
    cluster = fetch_cluster(lookup.cluster_id)
    if cluster:
        sub_opinions = cluster.get("sub_opinions", [])
        if sub_opinions:
            try:
                opinion_id = int(sub_opinions[0].rstrip("/").split("/")[-1])
                fwd_count = count_forward_citations(opinion_id)
            except (ValueError, IndexError):
                pass

    # Build citation string
    citation_str = lookup.citation
    if lookup.date_filed:
        citation_str = f"{citation_str} ({lookup.date_filed.year})"

    # Create a query to own the result
    query = ResearchQuery.objects.create(
        query_text=citation_text,
        status="complete",
        created_by=request.user,
    )

    # Create result
    result = ResearchResult.objects.create(
        query=query,
        position=1,
        case_name=lookup.case_name,
        citation=citation_str,
        court=lookup.court,
        date_filed=str(lookup.date_filed) if lookup.date_filed else "",
        cluster_id=lookup.cluster_id,
        courtlistener_url=(
            f"https://www.courtlistener.com{lookup.absolute_url}"
            if lookup.absolute_url
            else ""
        ),
        forward_citation_count=fwd_count,
        relevance="high",
        verify_status="verifying",
    )

    # Start background review
    review_result(result.id)

    return HttpResponseRedirect(f"{reverse('research:review-tab')}?result={result.id}")


@research_permission_required
def research_review_more(request, result_id):
    """Evaluate more unevaluated forward citations (POST)."""
    if request.method != "POST":
        return HttpResponse(status=405)

    result = get_object_or_404(
        ResearchResult, pk=result_id, query__created_by=request.user
    )

    result.verify_status = "verifying"
    result.save(update_fields=["verify_status"])
    review_more_citations(result.id)

    return render(request, "research/review-content.html", {"result": result})


@research_permission_required
def research_assess_citation(request, verification_id):
    """Assess a single forward citation (POST). Returns the citation partial."""
    if request.method != "POST":
        return HttpResponse(status=405)

    verification = get_object_or_404(
        CitationVerification,
        pk=verification_id,
        result__query__created_by=request.user,
    )

    assess_single_citation(verification.id)

    return render(
        request,
        "research/citation-item.html",
        {"v": verification, "assessing": True},
    )


@research_permission_required
def research_citation_status(request, verification_id):
    """Poll for a single citation assessment status."""
    verification = get_object_or_404(
        CitationVerification,
        pk=verification_id,
        result__query__created_by=request.user,
    )
    return render(
        request,
        "research/citation-item.html",
        {"v": verification, "assessing": not verification.summary},
    )


# ── Confirm / Delete ────────────────────────────────────────────────────────


@research_permission_required
def research_confirm(request, query_id):
    if request.method != "POST":
        return HttpResponse(status=405)

    query = get_object_or_404(ResearchQuery, pk=query_id, created_by=request.user)

    # Update structured query with user's edits
    structured_query = request.POST.get("structured_query", "").strip()
    if structured_query:
        query.structured_query = sanitize_query(structured_query)
        query.save(update_fields=["structured_query"])

    # Mark as searching before starting background thread to avoid race condition
    query.status = "searching"
    query.save(update_fields=["status"])

    # Continue with search + processing
    process_research_query(query.id)

    results = query.results.all()
    return render(
        request,
        "research/results.html",
        {"query": query, "results": results},
    )


@research_permission_required
def research_delete(request, query_id):
    if request.method != "POST":
        return HttpResponse(status=405)

    query = get_object_or_404(ResearchQuery, pk=query_id, created_by=request.user)
    query.delete()

    response = HttpResponse(status=200)
    response["HX-Redirect"] = reverse("research:index")
    return response
