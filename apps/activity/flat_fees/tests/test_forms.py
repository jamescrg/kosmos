import pytest

from apps.activity.flat_fees.forms import FlatFeeEntryForm
from apps.activity.time.forms import TimeEntryForm


@pytest.mark.django_db
def test_flat_fee_form_accepts_flat_fee_matter(user, flat_fee_matter):
    form = FlatFeeEntryForm(
        data={
            "matter": flat_fee_matter.id,
            "date": "2026-04-01",
            "description": "Monthly retainer",
            "amount": "5000.00",
            "comp": False,
            "entered": False,
        },
        user=user,
    )
    user.role = "ADMIN"
    user.save()
    assert form.is_valid(), form.errors


@pytest.mark.django_db
def test_flat_fee_form_rejects_hourly_matter(user, hourly_matter):
    user.role = "ADMIN"
    user.save()
    form = FlatFeeEntryForm(
        data={
            "matter": hourly_matter.id,
            "date": "2026-04-01",
            "description": "Should fail",
            "amount": "5000.00",
            "comp": False,
            "entered": False,
        },
        user=user,
    )
    assert not form.is_valid()
    assert "matter" in form.errors


@pytest.mark.django_db
def test_time_form_rejects_flat_fee_matter(user, flat_fee_matter):
    user.role = "ADMIN"
    user.save()
    form = TimeEntryForm(
        data={
            "matter": flat_fee_matter.id,
            "date": "2026-04-01",
            "actions": "Should fail",
            "hours": "0.5",
            "rate": "100",
            "comp": False,
            "entered": False,
        },
        user=user,
    )
    assert not form.is_valid()
    assert "matter" in form.errors
