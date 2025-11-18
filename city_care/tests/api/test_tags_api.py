from __future__ import annotations

import pytest
from django.urls import reverse

from core.reports.models import Tag


def _tag_payload(name: str) -> dict[str, str]:
    return {
        "name": name,
        "slug": name.lower().replace(" ", "-"),
    }


@pytest.mark.django_db
def test_tag_list_as_citizen(api_client, citizen_tokens, auth_header):
    Tag.objects.create(name="Saude", slug="saude")
    token_info = citizen_tokens()

    response = api_client.get(reverse("tag-list"), **auth_header(token_info["access"]))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "tags.list"
    assert isinstance(body["data"], list)


@pytest.mark.django_db
def test_tag_create_as_admin(api_client, admin_tokens, auth_header):
    token_info = admin_tokens()

    response = api_client.post(
        reverse("tag-list"),
        _tag_payload("Iluminacao Publica"),
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "tags.create"
    assert body["data"]["name"] == "Iluminacao Publica"


@pytest.mark.django_db
def test_tag_create_as_citizen_forbidden(api_client, citizen_tokens, auth_header):
    token_info = citizen_tokens()

    response = api_client.post(
        reverse("tag-list"),
        _tag_payload("Graffiti"),
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 403
    assert "detail" in response.json()["errors"]


@pytest.mark.django_db
def test_tag_update_as_admin(api_client, admin_tokens, auth_header):
    tag = Tag.objects.create(name="Buraco", slug="buraco")
    token_info = admin_tokens()

    response = api_client.patch(
        reverse("tag-detail", args=[tag.id]),
        {"name": "Buraco Nova"},
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Buraco Nova"


@pytest.mark.django_db
def test_tag_update_as_citizen_forbidden(api_client, citizen_tokens, auth_header):
    tag = Tag.objects.create(name="Arvore", slug="arvore")
    token_info = citizen_tokens()

    response = api_client.patch(
        reverse("tag-detail", args=[tag.id]),
        {"name": "Arvore Nova"},
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 403
    assert Tag.objects.get(id=tag.id).name == "Arvore"


@pytest.mark.django_db
def test_tag_delete_as_admin(api_client, admin_tokens, auth_header):
    tag = Tag.objects.create(name="Calcada", slug="calcada")
    token_info = admin_tokens()

    response = api_client.delete(reverse("tag-detail", args=[tag.id]), **auth_header(token_info["access"]))

    assert response.status_code == 204
    assert not Tag.objects.filter(id=tag.id).exists()


@pytest.mark.django_db
def test_tag_delete_as_citizen_forbidden(api_client, citizen_tokens, auth_header):
    tag = Tag.objects.create(name="Vandalismo", slug="vandalismo")
    token_info = citizen_tokens()

    response = api_client.delete(reverse("tag-detail", args=[tag.id]), **auth_header(token_info["access"]))

    assert response.status_code == 403
    assert Tag.objects.filter(id=tag.id).exists()

