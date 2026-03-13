from django.urls import path

from . import views

app_name = "research"

urlpatterns = [
    path("research/", views.research_index, name="index"),
    path("research/search/", views.research_search, name="search"),
    path("research/history/", views.research_history, name="history"),
    path("research/review/", views.research_review_tab, name="review-tab"),
    path("research/review/lookup/", views.research_review_lookup, name="review-lookup"),
    path(
        "research/review/<int:result_id>/status/",
        views.research_review_status,
        name="review-status",
    ),
    path(
        "research/review/<int:result_id>/more/",
        views.research_review_more,
        name="review-more",
    ),
    path(
        "research/review/citation/<int:verification_id>/assess/",
        views.research_assess_citation,
        name="assess-citation",
    ),
    path(
        "research/review/citation/<int:verification_id>/status/",
        views.research_citation_status,
        name="citation-status",
    ),
    path("research/results/<int:query_id>/", views.research_results, name="results"),
    path("research/result/<int:result_id>/", views.result_status, name="result-status"),
    path("research/status/<int:query_id>/", views.query_status, name="query-status"),
    path("research/<int:query_id>/", views.research_detail, name="detail"),
    path(
        "research/result/<int:result_id>/review/",
        views.research_review,
        name="review",
    ),
    path("research/<int:query_id>/confirm/", views.research_confirm, name="confirm"),
    path("research/<int:query_id>/delete/", views.research_delete, name="delete"),
]
