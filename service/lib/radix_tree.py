"""
Radix tree implementation for efficient Longest Prefix Match (LPM) lookups.

This implementation uses a binary radix tree (Patricia trie) optimized for
IPv4 and IPv6 prefix matching with O(prefix_length) lookup complexity.
"""

import ipaddress
from typing import Optional, List, Dict, Any


class RouteInfo:
    """Container for route information stored in the radix tree."""
    
    def __init__(self, prefix: str, next_hop: str, metric: int, prefix_len: int, version: int):
        self.prefix = prefix
        self.next_hop = next_hop
        self.metric = metric
        self.prefix_len = prefix_len
        self.version = version
        self.nhn = 0  # Next hop as integer for tie-breaking
    
    def __repr__(self):
        return f"RouteInfo({self.prefix}, {self.next_hop}, metric={self.metric})"


class RadixNode:
    """Node in the radix tree."""
    
    def __init__(self):
        self.left: Optional[RadixNode] = None  # 0 bit
        self.right: Optional[RadixNode] = None  # 1 bit
        self.routes: List[RouteInfo] = []  # Routes at this prefix
    
    def has_routes(self) -> bool:
        return len(self.routes) > 0


class RadixTree:
    """
    Binary radix tree for IPv4 and IPv6 routing table lookups.
    
    Supports efficient LPM (Longest Prefix Match) with O(prefix_length) complexity.
    Maintains separate trees for IPv4 (32-bit) and IPv6 (128-bit).
    """
    
    def __init__(self):
        self.ipv4_root = RadixNode()
        self.ipv6_root = RadixNode()
        self.route_count = 0
    
    def insert(self, prefix: str, next_hop: str, metric: int = 32768):
        """
        Insert a route into the radix tree.
        
        Args:
            prefix: Network prefix in CIDR notation (e.g., "192.168.1.0/24")
            next_hop: Next hop IP address
            metric: Route metric (lower is preferred)
        """
        try:
            network = ipaddress.ip_network(prefix)
        except (ValueError, ipaddress.AddressValueError) as e:
            raise ValueError(f"Invalid prefix {prefix}: {e}")
        
        # Create route info
        route = RouteInfo(
            prefix=prefix,
            next_hop=next_hop,
            metric=metric,
            prefix_len=network.prefixlen,
            version=network.version
        )
        
        # Calculate next hop as integer for tie-breaking
        try:
            nh_addr = ipaddress.ip_address(next_hop)
            route.nhn = int(nh_addr)
        except (ValueError, ipaddress.AddressValueError):
            route.nhn = 0
        
        # Select appropriate tree
        root = self.ipv4_root if network.version == 4 else self.ipv6_root
        
        # Convert network address to integer for bit operations
        addr_int = int(network.network_address)
        prefix_len = network.prefixlen
        max_bits = 32 if network.version == 4 else 128
        
        # Navigate/create tree nodes based on prefix bits
        current = root
        for bit_pos in range(max_bits - 1, max_bits - prefix_len - 1, -1):
            bit = (addr_int >> bit_pos) & 1
            
            if bit == 0:
                if current.left is None:
                    current.left = RadixNode()
                current = current.left
            else:
                if current.right is None:
                    current.right = RadixNode()
                current = current.right
        
        # Add route to this node
        current.routes.append(route)
        self.route_count += 1
    
    def lookup(self, ip_address: str) -> List[RouteInfo]:
        """
        Perform LPM lookup for an IP address.
        
        Returns all matching routes (all prefixes that contain this IP).
        Caller should select best route based on prefix length, metric, and next hop.
        
        Args:
            ip_address: IP address to lookup (e.g., "192.168.1.100")
        
        Returns:
            List of matching RouteInfo objects (may be empty)
        """
        try:
            addr = ipaddress.ip_address(ip_address)
        except (ValueError, ipaddress.AddressValueError) as e:
            raise ValueError(f"Invalid IP address {ip_address}: {e}")
        
        # Select appropriate tree
        root = self.ipv4_root if addr.version == 4 else self.ipv6_root
        
        # Convert address to integer
        addr_int = int(addr)
        max_bits = 32 if addr.version == 4 else 128
        
        # Traverse tree and collect all matching routes
        matching_routes = []
        current = root
        
        # Check root node (default route 0.0.0.0/0 or ::/0)
        if current.has_routes():
            matching_routes.extend(current.routes)
        
        # Traverse based on address bits
        for bit_pos in range(max_bits - 1, -1, -1):
            bit = (addr_int >> bit_pos) & 1
            
            if bit == 0:
                if current.left is None:
                    break
                current = current.left
            else:
                if current.right is None:
                    break
                current = current.right
            
            # Collect routes at this node
            if current.has_routes():
                matching_routes.extend(current.routes)
        
        return matching_routes
    
    def update_metric(self, prefix: str, next_hop: str, metric: int, match_type: str = "orlonger") -> int:
        """
        Update metric for matching routes.
        
        Args:
            prefix: Network prefix in CIDR notation
            next_hop: Next hop IP address to match
            metric: New metric value
            match_type: "exact" for exact prefix match, "orlonger" for prefix and subnets
        
        Returns:
            Number of routes updated
        """
        try:
            network = ipaddress.ip_network(prefix)
        except (ValueError, ipaddress.AddressValueError) as e:
            raise ValueError(f"Invalid prefix {prefix}: {e}")
        
        root = self.ipv4_root if network.version == 4 else self.ipv6_root
        addr_int = int(network.network_address)
        prefix_len = network.prefixlen
        max_bits = 32 if network.version == 4 else 128
        
        updated_count = 0
        
        if match_type == "exact":
            # Navigate to exact prefix
            current = root
            for bit_pos in range(max_bits - 1, max_bits - prefix_len - 1, -1):
                bit = (addr_int >> bit_pos) & 1
                current = current.left if bit == 0 else current.right
                if current is None:
                    return 0
            
            # Update matching routes at this node
            for route in current.routes:
                if route.next_hop == next_hop and route.prefix == network.with_prefixlen:
                    route.metric = metric
                    updated_count += 1
        else:
            # "orlonger" - update prefix and all subnets
            # Recursively traverse subtree starting from prefix
            current = root
            for bit_pos in range(max_bits - 1, max_bits - prefix_len - 1, -1):
                bit = (addr_int >> bit_pos) & 1
                current = current.left if bit == 0 else current.right
                if current is None:
                    return 0
            
            # Recursively update all routes in subtree
            updated_count = self._update_subtree(current, next_hop, metric)
        
        return updated_count
    
    def _update_subtree(self, node: RadixNode, next_hop: str, metric: int) -> int:
        """Recursively update all routes in subtree that match next_hop."""
        if node is None:
            return 0
        
        count = 0
        
        # Update routes at current node
        for route in node.routes:
            if route.next_hop == next_hop:
                route.metric = metric
                count += 1
        
        # Recursively update children
        count += self._update_subtree(node.left, next_hop, metric)
        count += self._update_subtree(node.right, next_hop, metric)
        
        return count
    
    def get_all_routes(self) -> List[RouteInfo]:
        """Get all routes in the tree (for debugging/testing)."""
        routes = []
        self._collect_routes(self.ipv4_root, routes)
        self._collect_routes(self.ipv6_root, routes)
        return routes
    
    def _collect_routes(self, node: Optional[RadixNode], routes: List[RouteInfo]):
        """Recursively collect all routes from tree."""
        if node is None:
            return
        
        routes.extend(node.routes)
        self._collect_routes(node.left, routes)
        self._collect_routes(node.right, routes)
