import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
def test_healthz(client):
    """
    GET /api/healthz/ should return 200 and JSON with status “ok”
    """
    resp = client.get(reverse("healthz"))
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data.get("status") == "ok"
    assert "elastic_status" in data

@pytest.mark.django_db
def test_search_returns_expected_structure(client):
    """
    GET /api/search/?q=<term> should return JSON with keys total and results
    """
    # Perform a search for something you know exists (e.g. “germany”)
    resp = client.get(reverse("search") + "?q=germany&page=1&size=5")
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert isinstance(data, dict)
    assert "total" in data and isinstance(data["total"], int)
    assert "results" in data and isinstance(data["results"], list)

    # If there are hits, each result must have id, score, source
    results = data["results"]
    if results:
        first = results[0]
        assert "id" in first
        assert "score" in first
        assert "source" in first and isinstance(first["source"], dict)

@pytest.mark.django_db
def test_doc_detail(client):
    """
    GET /api/doc/<id>/ should return the full document JSON if exists, or 404 otherwise.
    """
    # First, fetch search results to get a real ID
    search = client.get(reverse("search") + "?q=germany&page=1&size=1")
    assert search.status_code == status.HTTP_200_OK
    hits = search.json()["results"]
    if not hits:
        pytest.skip("No documents indexed; bulk_index must run before tests.")
    doc_id = hits[0]["id"]

    # Now get the detail endpoint
    detail = client.get(reverse("doc-detail", args=[doc_id]))
    assert detail.status_code == status.HTTP_200_OK
    payload = detail.json()
    assert payload.get("id") == doc_id
    assert "source" in payload and isinstance(payload["source"], dict)

    # And a non-existent ID returns 404
    missing = client.get(reverse("doc-detail", args=["does_not_exist"]))
    assert missing.status_code == status.HTTP_404_NOT_FOUND