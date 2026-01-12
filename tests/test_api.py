"""Tests for routing table API."""

import pytest
from fastapi.testclient import TestClient
import pandas as pd
import tempfile
import os


def create_test_routes_file():
    """Create a temporary routes file for testing."""
    content = """192.168.1.0/24;10.0.0.1
192.168.2.0/24;10.0.0.2
10.0.0.0/8;172.16.0.1
2001:db8::/32;2001:db8::1
"""
    fd, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


@pytest.fixture
def routes_file():
    """Fixture to provide a test routes file."""
    path = create_test_routes_file()
    yield path
    os.unlink(path)


@pytest.fixture
def client(routes_file, monkeypatch):
    """Fixture to provide a test client."""
    # Set the routes file path before importing the app
    monkeypatch.setenv("ROUTES_FILE", routes_file)
    monkeypatch.setenv("PROC_NUM", "2")
    
    # Import after setting environment
    from service.main import app
    
    return TestClient(app)


def test_root_redirect(client):
    """Test that root redirects to docs."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert "/docs" in response.headers["location"]


def test_get_next_hop_ipv4(client):
    """Test IPv4 route lookup."""
    response = client.get("/destination/192.168.1.0/24")
    assert response.status_code == 200
    data = response.json()
    assert "destination" in data
    assert "next_hop" in data


def test_get_next_hop_invalid_prefix(client):
    """Test with invalid IP prefix."""
    response = client.get("/destination/invalid-prefix")
    assert response.status_code == 400


def test_get_next_hop_not_found(client):
    """Test with non-existent route."""
    response = client.get("/destination/1.1.1.0/24")
    assert response.status_code == 404


def test_update_route(client):
    """Test route metric update."""
    response = client.put("/prefix/192.168.1.0%2F24/nh/10.0.0.1/metric/100")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_update_route_invalid_metric(client):
    """Test update with invalid metric."""
    response = client.put("/prefix/192.168.1.0%2F24/nh/10.0.0.1/metric/99999")
    assert response.status_code == 400


def test_update_route_with_match_exact(client):
    """Test route update with exact match."""
    response = client.put("/prefix/192.168.1.0%2F24/nh/10.0.0.1/metric/100/match/exact")
    assert response.status_code == 200


def test_update_route_invalid_match_type(client):
    """Test update with invalid match type."""
    response = client.put("/prefix/192.168.1.0%2F24/nh/10.0.0.1/metric/100/match/invalid")
    assert response.status_code == 400
