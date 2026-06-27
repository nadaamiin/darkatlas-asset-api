import pytest
from tests.conftest import client, auth_headers


# CRUD Tests

def test_create_asset(client, auth_headers):
    response = client.post("/assets/", json={
        "type": "domain",
        "value": "example.com",
        "source": "scan",
        "tags": ["prod"],
        "metadata": {}
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["value"] == "example.com"
    assert data["type"] == "domain"
    assert "id" in data
    assert "first_seen" in data


def test_create_asset_without_auth(client):
    response = client.post("/assets/", json={
        "type": "domain",
        "value": "example.com",
        "source": "scan",
        "tags": [],
        "metadata": {}
    })
    assert response.status_code == 401


def test_get_asset(client, auth_headers):
    # Create first
    create = client.post("/assets/", json={
        "type": "domain",
        "value": "example.com",
        "source": "scan",
        "tags": [],
        "metadata": {}
    }, headers=auth_headers)
    asset_id = create.json()["id"]

    # Then get
    response = client.get(f"/assets/{asset_id}")
    assert response.status_code == 200
    assert response.json()["value"] == "example.com"


def test_get_asset_not_found(client):
    response = client.get("/assets/nonexistent-id")
    assert response.status_code == 404


def test_update_asset(client, auth_headers):
    # Create first
    create = client.post("/assets/", json={
        "type": "domain",
        "value": "example.com",
        "source": "scan",
        "tags": [],
        "metadata": {}
    }, headers=auth_headers)
    asset_id = create.json()["id"]

    # Update status
    response = client.patch(f"/assets/{asset_id}",
        json={"status": "stale"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "stale"


def test_delete_asset(client, auth_headers):
    # Create first
    create = client.post("/assets/", json={
        "type": "domain",
        "value": "example.com",
        "source": "scan",
        "tags": [],
        "metadata": {}
    }, headers=auth_headers)
    asset_id = create.json()["id"]

    # Delete
    response = client.delete(f"/assets/{asset_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's gone
    get = client.get(f"/assets/{asset_id}")
    assert get.status_code == 404


# Deduplication Tests

def test_deduplication(client, auth_headers):
    # Import same asset twice
    payload = [{
        "id": "a1",
        "type": "domain",
        "value": "example.com",
        "source": "scan",
        "tags": ["root"],
        "metadata": {}
    }]
    client.post("/assets/bulk", json=payload, headers=auth_headers)
    response = client.post("/assets/bulk", json=payload, headers=auth_headers)

    data = response.json()
    assert data["created"] == 0
    assert data["updated"] == 1
    assert data["failed"] == 0


def test_deduplication_merges_tags(client, auth_headers):
    # First import with tag "root"
    client.post("/assets/bulk", json=[{
        "id": "a1",
        "type": "domain",
        "value": "example.com",
        "source": "scan",
        "tags": ["root"],
        "metadata": {}
    }], headers=auth_headers)

    # Second import with tag "prod"
    client.post("/assets/bulk", json=[{
        "id": "a1",
        "type": "domain",
        "value": "example.com",
        "source": "scan",
        "tags": ["prod"],
        "metadata": {}
    }], headers=auth_headers)

    # Should have both tags
    response = client.get("/assets/a1")
    tags = response.json()["tags"]
    assert "root" in tags
    assert "prod" in tags


def test_stale_asset_reactivated(client, auth_headers):
    # Create asset
    client.post("/assets/bulk", json=[{
        "id": "a1",
        "type": "domain",
        "value": "example.com",
        "source": "scan",
        "tags": [],
        "metadata": {}
    }], headers=auth_headers)

    # Mark it stale
    client.patch("/assets/a1", json={"status": "stale"}, headers=auth_headers)

    # Re-import same asset
    client.post("/assets/bulk", json=[{
        "id": "a1",
        "type": "domain",
        "value": "example.com",
        "source": "scan",
        "tags": [],
        "metadata": {}
    }], headers=auth_headers)

    # Should be active again
    response = client.get("/assets/a1")
    assert response.json()["status"] == "active"


# Filtering Tests

def test_filter_by_type(client, auth_headers):
    # Create two different types
    client.post("/assets/bulk", json=[
        {"id": "a1", "type": "domain", "value": "example.com",
         "source": "scan", "tags": [], "metadata": {}},
        {"id": "a2", "type": "subdomain", "value": "api.example.com",
         "source": "scan", "tags": [], "metadata": {}}
    ], headers=auth_headers)

    response = client.get("/assets/?type=domain")
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["type"] == "domain"


def test_filter_by_tag(client, auth_headers):
    client.post("/assets/bulk", json=[
        {"id": "a1", "type": "domain", "value": "example.com",
         "source": "scan", "tags": ["prod"], "metadata": {}},
        {"id": "a2", "type": "subdomain", "value": "api.example.com",
         "source": "scan", "tags": ["dev"], "metadata": {}}
    ], headers=auth_headers)

    response = client.get("/assets/?tag=prod")
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == "a1"


def test_filter_by_value_contains(client, auth_headers):
    client.post("/assets/bulk", json=[
        {"id": "a1", "type": "domain", "value": "example.com",
         "source": "scan", "tags": [], "metadata": {}},
        {"id": "a2", "type": "subdomain", "value": "api.example.com",
         "source": "scan", "tags": [], "metadata": {}}
    ], headers=auth_headers)

    response = client.get("/assets/?value_contains=api")
    data = response.json()
    assert data["total"] == 1
    assert "api" in data["items"][0]["value"]


def test_pagination(client, auth_headers):
    # Create 3 assets
    client.post("/assets/bulk", json=[
        {"id": "a1", "type": "domain", "value": "example.com",
         "source": "scan", "tags": [], "metadata": {}},
        {"id": "a2", "type": "subdomain", "value": "api.example.com",
         "source": "scan", "tags": [], "metadata": {}},
        {"id": "a3", "type": "certificate", "value": "CN=example.com",
         "source": "scan", "tags": [], "metadata": {}}
    ], headers=auth_headers)

    # Get page 1 with page_size 2
    response = client.get("/assets/?page=1&page_size=2")
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2


#  Relationship Tests

def test_create_relationship(client, auth_headers):
    # Create two assets first
    client.post("/assets/bulk", json=[
        {"id": "a1", "type": "domain", "value": "example.com",
         "source": "scan", "tags": [], "metadata": {}},
        {"id": "a2", "type": "subdomain", "value": "api.example.com",
         "source": "scan", "tags": [], "metadata": {}}
    ], headers=auth_headers)

    # Create relationship
    response = client.post("/assets/relationships", json={
        "source_id": "a2",
        "target_id": "a1",
        "relationship_type": "subdomain_of"
    }, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "a2"
    assert data["target_id"] == "a1"
    assert data["relationship_type"] == "subdomain_of"


def test_get_asset_graph(client, auth_headers):
    # Create assets and relationship
    client.post("/assets/bulk", json=[
        {"id": "a1", "type": "domain", "value": "example.com",
         "source": "scan", "tags": [], "metadata": {}},
        {"id": "a2", "type": "subdomain", "value": "api.example.com",
         "source": "scan", "tags": [], "metadata": {}}
    ], headers=auth_headers)

    client.post("/assets/relationships", json={
        "source_id": "a2",
        "target_id": "a1",
        "relationship_type": "subdomain_of"
    }, headers=auth_headers)

    # Get graph
    response = client.get("/assets/a1/graph")
    assert response.status_code == 200
    data = response.json()
    assert data["asset"]["id"] == "a1"
    assert len(data["relationships"]) == 1
    assert len(data["related_assets"]) == 1


def test_relationship_asset_not_found(client, auth_headers):
    response = client.post("/assets/relationships", json={
        "source_id": "nonexistent",
        "target_id": "also-nonexistent",
        "relationship_type": "subdomain_of"
    }, headers=auth_headers)
    assert response.status_code == 404