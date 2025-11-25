import pytest
from django.test import Client

from apps.accounts.models import CustomUser
from apps.agenda.events.models import Event
from apps.matters.models import Matter


@pytest.fixture
def user():
    user = CustomUser.objects.create(
        username="Ollie", email="ollie@gmail.com", user_rate=100
    )
    user.set_password("clawboy")
    user.save()

    return user


@pytest.fixture
def client(user):
    client = Client()
    client.login(username="Ollie", password="clawboy")
    return client


@pytest.fixture
def event(user, matter):
    event = Event.objects.create(
        user=user,
        matter=matter,
        date="2022-12-28",
        party="Client",
        description="File Answer",
        status="Pending",
    )
    event.save()
    return event


@pytest.fixture
def event_data(event):
    exclude_keys = {"_state", "id", "google_id", "user_id", "matter_id"}
    event_data = {
        key: value
        for key, value in event.__dict__.items()
        if key not in exclude_keys and value is not None
    }
    event_data["matter"] = event.matter_id
    return event_data


@pytest.fixture
def matter():
    matter = Matter.objects.create(
        name="Sample Test Matter",
        work_status="Awaiting response from OC",
        status="Open",
        practice_area="General",
    )
    matter.save()
    return matter
