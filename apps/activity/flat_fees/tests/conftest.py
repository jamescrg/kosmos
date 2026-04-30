import pytest
from django.test import Client

from apps.accounts.models import CustomUser
from apps.activity.flat_fees.models import FlatFeeEntry
from apps.matters.models import Matter, PracticeArea


@pytest.fixture
def user():
    user = CustomUser.objects.create(
        username="Ollie", email="testuser@example.com", user_rate=100
    )
    user.set_password("clawboy")
    user.save()
    return user


@pytest.fixture
def client(user):
    client = Client()
    client.login(username="Ollie", password="clawboy")
    client.get("/dash/")
    return client


@pytest.fixture
def practice_area():
    return PracticeArea.objects.create(name="General", is_active=True)


@pytest.fixture
def hourly_matter(practice_area):
    return Matter.objects.create(
        name="Hourly Matter",
        status="Open",
        practice_area=practice_area,
        billing_type="HOURLY",
    )


@pytest.fixture
def flat_fee_matter(practice_area):
    return Matter.objects.create(
        name="Flat Fee Matter",
        status="Open",
        practice_area=practice_area,
        billing_type="FLAT_FEE",
        flat_fee_amount=5000,
    )


@pytest.fixture
def flat_fee_entry(user, flat_fee_matter):
    return FlatFeeEntry.objects.create(
        user_id=user.id,
        matter=flat_fee_matter,
        date="2026-04-01",
        description="April retainer",
        amount=5000,
        comp=False,
        entered=False,
    )
