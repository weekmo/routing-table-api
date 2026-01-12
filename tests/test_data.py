"""Tests for data processing utilities."""

import pytest
import pandas as pd
import ipaddress
import tempfile
import os

from service.utils.data import (
    get_df_polars,
    get_df_pandas,
    lpm_map,
    lpm_update,
    lpm_itr,
)


@pytest.fixture
def routes_file():
    """Create a temporary test routes file."""
    content = """192.168.1.0/24;10.0.0.1
192.168.2.0/24;10.0.0.2
192.168.1.128/25;10.0.0.3
10.0.0.0/8;172.16.0.1
2001:db8::/32;2001:db8::1
2001:db8:1::/48;2001:db8::2
"""
    fd, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    yield path
    os.unlink(path)


@pytest.fixture
def routing_df(routes_file):
    """Load test routing table."""
    return get_df_polars(routes_file, proc_num=2)


def test_get_df_polars(routes_file):
    """Test loading routes with Polars."""
    df = get_df_polars(routes_file, proc_num=2)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 6
    assert all(col in df.columns for col in ["prefix", "next_hop", "addr", "mask", "v", "prefixlen"])


def test_get_df_pandas(routes_file):
    """Test loading routes with Pandas."""
    df = get_df_pandas(routes_file, proc_num=2)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 6


def test_lpm_map_ipv4(routing_df):
    """Test LPM lookup for IPv4."""
    prefix = ipaddress.ip_network("192.168.1.0/24")
    result = lpm_map(routing_df, prefix)
    assert len(result) >= 1
    assert all(result["v"] == 4)


def test_lpm_map_ipv6(routing_df):
    """Test LPM lookup for IPv6."""
    prefix = ipaddress.ip_network("2001:db8::/32")
    result = lpm_map(routing_df, prefix)
    assert len(result) >= 1
    assert all(result["v"] == 6)


def test_lpm_map_no_match(routing_df):
    """Test LPM with no matching route."""
    prefix = ipaddress.ip_network("1.1.1.0/24")
    result = lpm_map(routing_df, prefix)
    assert len(result) == 0


def test_lpm_itr_matches_map(routing_df):
    """Test that iterative and map-based LPM produce same results."""
    prefix = ipaddress.ip_network("192.168.1.0/24")
    result_map = lpm_map(routing_df, prefix)
    result_itr = lpm_itr(routing_df, prefix)
    
    # Sort both for comparison
    result_map_sorted = result_map.sort_index()
    result_itr_sorted = result_itr.sort_index()
    
    pd.testing.assert_frame_equal(result_map_sorted, result_itr_sorted)


def test_lpm_update_orlonger(routing_df):
    """Test route update with orlonger match."""
    prefix = ipaddress.ip_network("192.168.1.0/24")
    result = lpm_update(routing_df, prefix, "10.0.0.1", 500, matchd="orlonger")
    assert len(result) >= 1
    assert all(result["metric"] == 500)


def test_lpm_update_exact(routing_df):
    """Test route update with exact match."""
    prefix = ipaddress.ip_network("192.168.1.0/24")
    result = lpm_update(routing_df, prefix, "10.0.0.1", 500, matchd="exact")
    if len(result) > 0:
        assert all(result["prefix"] == "192.168.1.0/24")
        assert all(result["metric"] == 500)


def test_ipv4_hex_conversion(routing_df):
    """Test that IPv4 addresses are properly converted to hex."""
    v4_routes = routing_df[routing_df["v"] == 4]
    assert all(v4_routes["addr"].str.len() == 8)  # IPv4 hex is 8 chars
    assert all(v4_routes["mask"].str.len() == 8)


def test_ipv6_hex_conversion(routing_df):
    """Test that IPv6 addresses are properly converted to hex."""
    v6_routes = routing_df[routing_df["v"] == 6]
    assert all(v6_routes["addr"].str.len() == 32)  # IPv6 hex is 32 chars
    assert all(v6_routes["mask"].str.len() == 32)
