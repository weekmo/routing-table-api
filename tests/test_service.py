"""Integration tests for the routing table API service."""
import httpx
from time import sleep

HOSTNAME = "testservice"
PORT = 5000
API_URL = f"http://{HOSTNAME}:{PORT}"


def wait_for_service():
    """Wait for service to be ready (routes loading can take time)."""
    # import of routes at service startup is expected to take a while
    for i in range(100):
        try:
            httpx.get(f"{API_URL}/destination/1.0.167.0")
        except Exception:
            sleep(1)
            continue
        break


def test_destination_simple():
    """Test basic destination lookup."""
    wait_for_service()

    response = httpx.get(f"{API_URL}/destination/1.0.167.0")
    assert response.status_code == 200

    response_parsed = response.json()
    assert response_parsed["dst"] == "1.0.167.0/24"
    assert response_parsed["nh"] == "192.168.2.1"


def test_destination_full():
    """Test multiple destination lookups including default route."""
    for address, expected in {
        "12.1.5.0": ["12.1.5.0/24", "192.168.30.1"],
        "140.16.178.2": ["140.16.176.0/20", "192.168.40.1"],
        "12.3.81.23": ["12.3.80.0/22", "192.168.10.1"],
        "151.251.225.48": ["151.251.225.0/24", "192.168.3.1"],
        "10.16.0.17": ["0.0.0.0/0", "192.168.30.1"],    # adjust if we remove 0.0.0.0/0
        "198.14.34.1": ["198.14.32.0/19", "192.168.30.1"],
    }.items():
        response = httpx.get(f"{API_URL}/destination/{address}")
        if expected:
            assert response.status_code == 200
            response_parsed = response.json()

            assert response_parsed["dst"] == expected[0]
            assert response_parsed["nh"] == expected[1]
        else:
            assert response.status_code == 404


def test_prefix_metric_update_exact():
    """Test exact match metric updates."""
    # test lookup failures on metric update
    url = f"{API_URL}/prefix/10.0.0.0%2F16/nh/192.168.10.1/metric/10/match/exact"
    response = httpx.put(url)
    assert response.status_code == 404

    url = f"{API_URL}/prefix/64.150.140.0%2F24/nh/192.168.20.2/metric/10/match/exact"
    response = httpx.put(url)
    assert response.status_code == 404

    # test simple, successful metric update
    url = f"{API_URL}/prefix/64.150.140.0%2F24/nh/192.168.20.1/metric/32768/match/exact"
    response = httpx.put(url)

    url = f"{API_URL}/prefix/64.150.140.0%2F24/nh/192.168.20.1/metric/100/match/exact"
    response = httpx.put(url)
    assert response.status_code == 200

    # test complete successful update + lookup flow
    url = f"{API_URL}/prefix/82.150.104.0%2F24/nh/192.168.200.1/metric/32768/match/exact"
    response = httpx.put(url)

    response = httpx.get(f"{API_URL}/destination/82.150.104.23")
    assert response.status_code == 200
    response_parsed = response.json()
    assert response_parsed["dst"] == "82.150.104.0/24"
    assert response_parsed["nh"] == "192.168.30.1"

    url = f"{API_URL}/prefix/82.150.104.0%2F24/nh/192.168.200.1/metric/100/match/exact"
    response = httpx.put(url)
    assert response.status_code == 200

    response = httpx.get(f"{API_URL}/destination/82.150.104.23")
    assert response.status_code == 200
    response_parsed = response.json()
    assert response_parsed["dst"] == "82.150.104.0/24"
    assert response_parsed["nh"] == "192.168.200.1"


def test_prefix_metric_update_orlonger():
    """Test orlonger metric updates (implicit)."""
    # reset
    url = f"{API_URL}/prefix/1.2.224.0%2F21/nh/192.168.240.1/metric/32768"
    response = httpx.put(url)

    # test lookup before update
    response = httpx.get(f"{API_URL}/destination/1.2.224.16")
    assert response.status_code == 200

    response_parsed = response.json()
    assert response_parsed["dst"] == "1.2.224.0/24"
    assert response_parsed["nh"] == "192.168.10.1"

    # test metric update with classifier "orlonger"
    url = f"{API_URL}/prefix/1.2.224.0%2F21/nh/192.168.240.1/metric/10"
    response = httpx.put(url)
    assert response.status_code == 200

    # lookup after update
    response = httpx.get(f"{API_URL}/destination/1.2.224.16")
    assert response.status_code == 200

    response_parsed = response.json()
    assert response_parsed["dst"] == "1.2.224.0/24"
    assert response_parsed["nh"] == "192.168.240.1"


def test_prefix_metric_update_orlonger_explicit():
    """Test orlonger metric updates (explicit match parameter)."""
    # reset
    url = f"{API_URL}/prefix/199.127.184.0%2F21/nh/192.168.100.1/metric/32768/match/orlonger"
    response = httpx.put(url)

    # test lookup before update
    response = httpx.get(f"{API_URL}/destination/199.127.184.69")
    assert response.status_code == 200

    response_parsed = response.json()
    assert response_parsed["dst"] == "199.127.184.0/22"
    assert response_parsed["nh"] == "192.168.30.1"

    # test metric update with explicit classifier "orlonger"
    url = f"{API_URL}/prefix/199.127.184.0%2F21/nh/192.168.100.1/metric/10/match/orlonger"
    response = httpx.put(url)
    assert response.status_code == 200

    # lookup after update
    response = httpx.get(f"{API_URL}/destination/199.127.184.69")
    assert response.status_code == 200

    response_parsed = response.json()
    assert response_parsed["dst"] == "199.127.184.0/22"
    assert response_parsed["nh"] == "192.168.100.1"
