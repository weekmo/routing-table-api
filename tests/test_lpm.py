"""Unit tests for LPM (Longest Prefix Match) algorithm."""

import pytest

from service.lib.radix_tree import RadixTree


class TestRadixTreeBasic:
    """Basic radix tree functionality tests."""

    def test_insert_and_lookup_ipv4(self):
        """Test basic IPv4 insert and lookup."""
        tree = RadixTree()
        tree.insert("192.168.1.0/24", "10.0.0.1", 100)

        routes = tree.lookup("192.168.1.100")
        assert len(routes) == 1
        assert routes[0].prefix == "192.168.1.0/24"
        assert routes[0].next_hop == "10.0.0.1"
        assert routes[0].metric == 100

    def test_insert_and_lookup_ipv6(self):
        """Test basic IPv6 insert and lookup."""
        tree = RadixTree()
        tree.insert("2001:db8::/32", "fe80::1", 100)

        routes = tree.lookup("2001:db8::100")
        assert len(routes) == 1
        assert routes[0].prefix == "2001:db8::/32"
        assert routes[0].next_hop == "fe80::1"

    def test_no_match(self):
        """Test lookup with no matching route."""
        tree = RadixTree()
        tree.insert("192.168.1.0/24", "10.0.0.1", 100)

        routes = tree.lookup("10.0.0.1")
        assert len(routes) == 0

    def test_route_count(self):
        """Test route counting."""
        tree = RadixTree()
        assert tree.route_count == 0

        tree.insert("192.168.1.0/24", "10.0.0.1", 100)
        assert tree.route_count == 1

        tree.insert("192.168.2.0/24", "10.0.0.1", 100)
        assert tree.route_count == 2


class TestLongestPrefixMatch:
    """Tests for longest prefix match behavior."""

    def test_lpm_multiple_matches(self):
        """Test that all matching prefixes are returned."""
        tree = RadixTree()
        tree.insert("0.0.0.0/0", "10.0.0.1", 300)  # Default route
        tree.insert("192.168.0.0/16", "10.0.0.2", 200)
        tree.insert("192.168.1.0/24", "10.0.0.3", 100)

        routes = tree.lookup("192.168.1.100")

        # Should return all 3 matching prefixes
        assert len(routes) == 3
        prefixes = [r.prefix for r in routes]
        assert "0.0.0.0/0" in prefixes
        assert "192.168.0.0/16" in prefixes
        assert "192.168.1.0/24" in prefixes

    def test_lpm_selection_by_prefix_length(self):
        """Test that longest prefix is preferred."""
        tree = RadixTree()
        tree.insert("10.0.0.0/8", "192.168.1.1", 100)
        tree.insert("10.1.0.0/16", "192.168.1.2", 100)
        tree.insert("10.1.1.0/24", "192.168.1.3", 100)

        routes = tree.lookup("10.1.1.100")

        # Sort by prefix length (longest first)
        routes_sorted = sorted(routes, key=lambda r: r.prefix_len, reverse=True)

        # Longest match should be /24
        assert routes_sorted[0].prefix == "10.1.1.0/24"
        assert routes_sorted[0].next_hop == "192.168.1.3"


class TestDefaultRoute:
    """Tests for default route (0.0.0.0/0) handling."""

    def test_default_route_ipv4(self):
        """Test default route matches everything."""
        tree = RadixTree()
        tree.insert("0.0.0.0/0", "10.0.0.1", 100)

        # Should match any IPv4 address
        for ip in ["1.1.1.1", "192.168.1.1", "255.255.255.255"]:
            routes = tree.lookup(ip)
            assert len(routes) == 1
            assert routes[0].prefix == "0.0.0.0/0"

    def test_default_route_ipv6(self):
        """Test IPv6 default route."""
        tree = RadixTree()
        tree.insert("::/0", "fe80::1", 100)

        routes = tree.lookup("2001:db8::1")
        assert len(routes) == 1
        assert routes[0].prefix == "::/0"


class TestHostRoutes:
    """Tests for host routes (/32 for IPv4, /128 for IPv6)."""

    def test_host_route_ipv4(self):
        """Test /32 host route."""
        tree = RadixTree()
        tree.insert("192.168.1.100/32", "10.0.0.1", 100)
        tree.insert("192.168.1.0/24", "10.0.0.2", 200)

        # Exact match
        routes = tree.lookup("192.168.1.100")
        prefixes = [r.prefix for r in routes]
        assert "192.168.1.100/32" in prefixes
        assert "192.168.1.0/24" in prefixes

        # Other address in subnet should only match /24
        routes = tree.lookup("192.168.1.101")
        prefixes = [r.prefix for r in routes]
        assert "192.168.1.100/32" not in prefixes
        assert "192.168.1.0/24" in prefixes

    def test_host_route_ipv6(self):
        """Test /128 host route."""
        tree = RadixTree()
        tree.insert("2001:db8::1/128", "fe80::1", 100)
        tree.insert("2001:db8::/64", "fe80::2", 200)

        routes = tree.lookup("2001:db8::1")
        prefixes = [r.prefix for r in routes]
        assert "2001:db8::1/128" in prefixes
        assert "2001:db8::/64" in prefixes


class TestMetricHandling:
    """Tests for metric-based route selection."""

    def test_metric_tie_breaker_same_prefix(self):
        """Test metric as tie-breaker for same prefix length."""
        tree = RadixTree()
        tree.insert("192.168.1.0/24", "10.0.0.1", 200)  # Higher metric
        tree.insert("192.168.1.0/24", "10.0.0.2", 100)  # Lower metric (preferred)

        routes = tree.lookup("192.168.1.100")

        # Both routes should be returned
        assert len(routes) == 2

        # Sort by metric (lower is better)
        routes_sorted = sorted(routes, key=lambda r: r.metric)
        assert routes_sorted[0].next_hop == "10.0.0.2"
        assert routes_sorted[0].metric == 100

    def test_metric_update_exact(self):
        """Test exact metric update."""
        tree = RadixTree()
        tree.insert("192.168.1.0/24", "10.0.0.1", 100)

        # Update metric
        count = tree.update_metric("192.168.1.0/24", "10.0.0.1", 50, "exact")
        assert count == 1

        # Verify update
        routes = tree.lookup("192.168.1.100")
        assert routes[0].metric == 50

    def test_metric_update_orlonger(self):
        """Test orlonger metric update."""
        tree = RadixTree()
        tree.insert("10.0.0.0/8", "192.168.1.1", 100)
        tree.insert("10.1.0.0/16", "192.168.1.1", 100)
        tree.insert("10.1.1.0/24", "192.168.1.1", 100)

        # Update /16 and all subnets
        count = tree.update_metric("10.1.0.0/16", "192.168.1.1", 50, "orlonger")
        assert count == 2  # /16 and /24, not /8

        # Verify updates
        routes = tree.lookup("10.1.1.100")
        for route in routes:
            if route.prefix in ["10.1.0.0/16", "10.1.1.0/24"]:
                assert route.metric == 50
            elif route.prefix == "10.0.0.0/8":
                assert route.metric == 100


class TestNextHopTieBreaker:
    """Tests for next-hop IP address as final tie-breaker."""

    def test_next_hop_tie_breaker(self):
        """Test next-hop IP as tie-breaker when prefix and metric are same."""
        tree = RadixTree()
        tree.insert("192.168.1.0/24", "10.0.0.2", 100)  # Higher IP
        tree.insert("192.168.1.0/24", "10.0.0.1", 100)  # Lower IP (preferred)

        routes = tree.lookup("192.168.1.100")
        assert len(routes) == 2

        # Sort by next-hop integer value
        routes_sorted = sorted(routes, key=lambda r: r.nhn)

        # Lower IP should come first
        assert routes_sorted[0].next_hop == "10.0.0.1"
        assert routes_sorted[1].next_hop == "10.0.0.2"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_invalid_prefix_insert(self):
        """Test error handling for invalid prefix."""
        tree = RadixTree()

        with pytest.raises(ValueError):
            tree.insert("invalid", "10.0.0.1", 100)

    def test_invalid_ip_lookup(self):
        """Test error handling for invalid IP lookup."""
        tree = RadixTree()

        with pytest.raises(ValueError):
            tree.lookup("invalid")

    def test_ipv4_ipv6_isolation(self):
        """Test that IPv4 and IPv6 routes are isolated."""
        tree = RadixTree()
        tree.insert("192.168.1.0/24", "10.0.0.1", 100)
        tree.insert("2001:db8::/32", "fe80::1", 100)

        # IPv4 lookup should not return IPv6 routes
        routes = tree.lookup("192.168.1.100")
        assert all(r.version == 4 for r in routes)

        # IPv6 lookup should not return IPv4 routes
        routes = tree.lookup("2001:db8::100")
        assert all(r.version == 6 for r in routes)

    def test_empty_tree_lookup(self):
        """Test lookup on empty tree."""
        tree = RadixTree()
        routes = tree.lookup("192.168.1.1")
        assert len(routes) == 0

    def test_multiple_next_hops_different_routes(self):
        """Test multiple next-hops for different prefixes."""
        tree = RadixTree()
        tree.insert("192.168.1.0/24", "10.0.0.1", 100)
        tree.insert("192.168.2.0/24", "10.0.0.2", 100)
        tree.insert("192.168.3.0/24", "10.0.0.1", 100)

        # Lookup different addresses
        routes1 = tree.lookup("192.168.1.1")
        assert len(routes1) == 1
        assert routes1[0].next_hop == "10.0.0.1"

        routes2 = tree.lookup("192.168.2.1")
        assert len(routes2) == 1
        assert routes2[0].next_hop == "10.0.0.2"


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    def test_full_routing_table_simulation(self):
        """Simulate a complex routing table with multiple overlapping routes."""
        tree = RadixTree()

        # Add routes in various orders
        routes_to_add = [
            ("0.0.0.0/0", "192.168.1.1", 1000),  # Default
            ("10.0.0.0/8", "192.168.2.1", 500),
            ("10.1.0.0/16", "192.168.3.1", 400),
            ("10.1.1.0/24", "192.168.4.1", 300),
            ("10.1.1.128/25", "192.168.5.1", 200),
            ("10.1.1.192/26", "192.168.6.1", 100),
        ]

        for prefix, nh, metric in routes_to_add:
            tree.insert(prefix, nh, metric)

        # Test specific lookup
        routes = tree.lookup("10.1.1.200")

        # Should match all overlapping prefixes (10.1.1.200 is in 192-255 range, so all 6)
        assert len(routes) == 6

        # Most specific should be /26 (192-255)
        routes_sorted = sorted(routes, key=lambda r: r.prefix_len, reverse=True)
        assert routes_sorted[0].prefix == "10.1.1.192/26"
        assert routes_sorted[0].next_hop == "192.168.6.1"
