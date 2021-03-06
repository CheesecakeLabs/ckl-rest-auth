import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status


User = get_user_model()


@pytest.mark.django_db()
def test_password_reset_successful(client, mailoutbox):
    test_user = User.objects.create_user(
        email='test@mail.com',
        username='test',
        password='1234qwer'
    )

    request = client.post(
        path=reverse('cklauth:password-reset'),
        data=json.dumps({
            'email': test_user.email,
        }),
        content_type='application/json'
    )

    assert request.status_code == status.HTTP_200_OK

    # Test that one message has been sent.
    assert len(mailoutbox) == 1


@pytest.mark.django_db()
def test_password_reset_successful_non_existing_user(client, mailoutbox):
    request = client.post(
        path=reverse('cklauth:password-reset'),
        data=json.dumps({
            'email': 'nobody@mail.com',
        }),
        content_type='application/json'
    )

    assert request.status_code == status.HTTP_200_OK

    # Test that no message has been sent.
    assert len(mailoutbox) == 0


@pytest.mark.django_db()
def test_password_reset_failed_invalid_payload(client):
    request = client.post(
        path=reverse('cklauth:password-reset'),
        data=json.dumps({
            'username': 'username'
        }),
        content_type='application/json'
    )

    content = json.loads(request.content)

    assert request.status_code == status.HTTP_400_BAD_REQUEST
    assert content == {'email': ['This field is required.']}
