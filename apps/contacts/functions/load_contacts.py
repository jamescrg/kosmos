from apps.matters.models import Relationship


def load_contacts(matter):
    base_qs = Relationship.objects.select_related("contact", "role").filter(
        matter=matter
    )

    relationship_groups = {
        "Client": base_qs.filter(role__name__icontains="Client"),
        "Adversary": base_qs.filter(role__name__icontains="Adversary"),
        "Court": base_qs.filter(role__name__icontains="Court"),
        "Other": base_qs.exclude(role__name__icontains="Client")
        .exclude(role__name__icontains="Adversary")
        .exclude(role__name__icontains="Court"),
    }

    return relationship_groups
