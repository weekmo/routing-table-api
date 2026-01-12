"""Concurrency tests for thread safety and data integrity."""

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from service.lib.radix_tree import RadixTree


class TestConcurrentReads:
    """Tests for concurrent read operations."""

    def test_concurrent_lookups(self):
        """Test multiple threads performing lookups simultaneously."""
        tree = RadixTree()

        # Populate tree
        for i in range(100):
            tree.insert(f"10.{i}.0.0/16", f"192.168.{i}.1", 100)

        results = []
        errors = []

        def lookup_worker(ip_suffix):
            try:
                routes = tree.lookup(f"10.{ip_suffix}.1.1")
                results.append((ip_suffix, len(routes)))
                return len(routes)
            except Exception as e:
                errors.append(e)
                raise

        # Run 100 concurrent lookups
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(lookup_worker, i) for i in range(100)]
            for future in as_completed(futures):
                future.result()  # Raise any exceptions

        # Verify all lookups succeeded
        assert len(errors) == 0
        assert len(results) == 100

        # Each lookup should find exactly 1 route
        for _, count in results:
            assert count == 1

    def test_concurrent_reads_no_corruption(self):
        """Verify that concurrent reads don't corrupt data."""
        tree = RadixTree()
        tree.insert("192.168.1.0/24", "10.0.0.1", 100)

        def verify_route():
            routes = tree.lookup("192.168.1.100")
            assert len(routes) == 1
            assert routes[0].prefix == "192.168.1.0/24"
            assert routes[0].next_hop == "10.0.0.1"
            assert routes[0].metric == 100

        # Run 1000 concurrent verifications
        threads = []
        for _ in range(1000):
            t = threading.Thread(target=verify_route)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Tree should still be intact
        assert tree.route_count == 1


class TestConcurrentWrites:
    """Tests for concurrent write operations."""

    def test_concurrent_inserts_different_prefixes(self):
        """Test concurrent inserts of different prefixes."""
        tree = RadixTree()
        errors = []

        def insert_worker(i):
            try:
                tree.insert(f"10.{i}.0.0/16", f"192.168.{i}.1", 100)
            except Exception as e:
                errors.append(e)

        # Insert 50 routes concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(insert_worker, i) for i in range(50)]
            for future in as_completed(futures):
                future.result()

        assert len(errors) == 0
        assert tree.route_count == 50

    def test_concurrent_metric_updates(self):
        """Test concurrent metric updates on same routes."""
        tree = RadixTree()

        # Pre-populate
        for i in range(10):
            tree.insert(f"10.{i}.0.0/16", "192.168.1.1", 100)

        update_counts = []

        def update_worker(i):
            # Update with different metrics
            count = tree.update_metric(f"10.{i}.0.0/16", "192.168.1.1", 50 + i, "exact")
            update_counts.append(count)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_worker, i) for i in range(10)]
            for future in as_completed(futures):
                future.result()

        # Each update should affect exactly 1 route
        assert all(count == 1 for count in update_counts)

        # Verify metrics were updated
        for i in range(10):
            routes = tree.lookup(f"10.{i}.1.1")
            assert len(routes) == 1
            assert routes[0].metric == 50 + i


class TestMixedReadWrite:
    """Tests for mixed concurrent read and write operations."""

    def test_read_while_writing(self):
        """Test reads while writes are happening."""
        tree = RadixTree()

        # Initial routes
        for i in range(20):
            tree.insert(f"10.{i}.0.0/16", f"192.168.{i}.1", 100)

        stop_flag = threading.Event()
        read_count = [0]
        write_count = [0]
        errors = []

        def reader():
            """Continuously read random routes."""
            while not stop_flag.is_set():
                try:
                    i = random.randint(0, 19)
                    routes = tree.lookup(f"10.{i}.1.1")
                    assert len(routes) >= 1
                    read_count[0] += 1
                except Exception as e:
                    errors.append(("read", e))
                time.sleep(0.001)

        def writer():
            """Add new routes while reads are happening."""
            for i in range(20, 40):
                try:
                    tree.insert(f"10.{i}.0.0/16", f"192.168.{i}.1", 100)
                    write_count[0] += 1
                    time.sleep(0.01)
                except Exception as e:
                    errors.append(("write", e))

        # Start readers and writers
        reader_threads = [threading.Thread(target=reader) for _ in range(3)]
        writer_thread = threading.Thread(target=writer)

        for t in reader_threads:
            t.start()
        writer_thread.start()

        # Let them run
        writer_thread.join()
        stop_flag.set()

        for t in reader_threads:
            t.join()

        # Verify no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert read_count[0] > 0
        assert write_count[0] == 20
        assert tree.route_count == 40


class TestStressTests:
    """Stress tests with high concurrency."""

    def test_high_concurrency_lookups(self):
        """Test with very high number of concurrent lookups."""
        tree = RadixTree()

        # Build a decent-sized tree
        for i in range(256):
            tree.insert(f"10.{i}.0.0/16", f"192.168.{i % 100}.1", 100)

        successful_lookups = [0]
        lock = threading.Lock()

        def lookup_random():
            for _ in range(100):
                i = random.randint(0, 255)
                routes = tree.lookup(f"10.{i}.50.50")
                assert len(routes) >= 1
                with lock:
                    successful_lookups[0] += 1

        # 20 threads each doing 100 lookups = 2000 total
        threads = [threading.Thread(target=lookup_random) for _ in range(20)]

        start = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.time() - start

        assert successful_lookups[0] == 2000
        print(
            f"\n2000 concurrent lookups completed in {elapsed:.2f}s "
            f"({successful_lookups[0] / elapsed:.0f} lookups/sec)"
        )

    def test_rapid_metric_updates(self):
        """Test rapid metric updates on same routes."""
        tree = RadixTree()
        tree.insert("192.168.1.0/24", "10.0.0.1", 100)

        def update_metric_rapidly():
            for _ in range(100):
                metric = random.randint(1, 32768)
                tree.update_metric("192.168.1.0/24", "10.0.0.1", metric, "exact")

        threads = [threading.Thread(target=update_metric_rapidly) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Tree should still be consistent
        routes = tree.lookup("192.168.1.100")
        assert len(routes) == 1
        assert 1 <= routes[0].metric <= 32768


class TestDataIntegrity:
    """Tests to verify data integrity under concurrent access."""

    def test_route_count_consistency(self):
        """Verify route count remains consistent with concurrent inserts."""
        tree = RadixTree()

        def insert_batch(start, end):
            for i in range(start, end):
                tree.insert(f"10.{i}.0.0/16", "192.168.1.1", 100)

        # Insert 100 routes across 10 threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i in range(10):
                start = i * 10
                end = start + 10
                futures.append(executor.submit(insert_batch, start, end))

            for future in as_completed(futures):
                future.result()

        # Should have exactly 100 routes
        assert tree.route_count == 100

        # Verify all routes are accessible
        all_routes = tree.get_all_routes()
        assert len(all_routes) == 100

    def test_no_race_conditions_in_updates(self):
        """Test that metric updates don't create race conditions."""
        tree = RadixTree()

        # Create a tree with parent and children
        tree.insert("10.0.0.0/8", "192.168.1.1", 100)
        tree.insert("10.1.0.0/16", "192.168.1.1", 100)
        tree.insert("10.1.1.0/24", "192.168.1.1", 100)

        def update_orlonger():
            tree.update_metric("10.1.0.0/16", "192.168.1.1", 50, "orlonger")

        def verify_metrics():
            routes = tree.lookup("10.1.1.100")
            for route in routes:
                # After update, /16 and /24 should be 50, /8 should be 100
                if route.prefix in ["10.1.0.0/16", "10.1.1.0/24"]:
                    assert route.metric in [50, 100]  # May be in transition
                elif route.prefix == "10.0.0.0/8":
                    assert route.metric == 100

        # Run updates and verifications concurrently
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=update_orlonger))
            threads.append(threading.Thread(target=verify_metrics))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Final state: /16 and /24 should be 50
        routes = tree.lookup("10.1.1.100")
        for route in routes:
            if route.prefix in ["10.1.0.0/16", "10.1.1.0/24"]:
                assert route.metric == 50
            elif route.prefix == "10.0.0.0/8":
                assert route.metric == 100
