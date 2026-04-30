import pytest

from apps.activity.flat_fees.models import FlatFeeEntry


@pytest.mark.django_db
def test_flat_fee_entry_str(flat_fee_entry):
    assert str(flat_fee_entry) == "April retainer"


@pytest.mark.django_db
def test_discounted_amount_when_comp(user, flat_fee_matter):
    entry = FlatFeeEntry.objects.create(
        user_id=user.id,
        matter=flat_fee_matter,
        date="2026-04-01",
        description="comp entry",
        amount=2500,
        comp=True,
    )
    assert entry.discounted_amount == 2500


@pytest.mark.django_db
def test_discounted_amount_when_not_comp(flat_fee_entry):
    assert flat_fee_entry.discounted_amount == 0


@pytest.mark.django_db
def test_matter_value_includes_flat_fees(flat_fee_matter, flat_fee_entry):
    val = flat_fee_matter.value
    assert val["total"]["net_flat_fees"] == 5000
    assert val["total"]["net_fees_and_expenses"] == 5000
    assert val["unbilled"]["net_flat_fees"] == 5000
