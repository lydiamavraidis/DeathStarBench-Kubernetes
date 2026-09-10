#!/usr/bin/env python3
"""
Jaeger Trace Extractor for DeathStarBench SocialNetwork

Extracts distributed traces from Jaeger, parses microservice call paths,
and exports latency data for analysis and synthetic workload generation.

Usage:
    python3 extract_traces.py

Requires:
    - Jaeger running on localhost:16686
    - Python 3.7+
    - requests library (pip install requests)
"""

import requests
import json
import time
import sys
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any, Optional

class JaegerTraceExtractor:
    """Extract and parse traces from Jaeger"""
    
    def __init__(self, jaeger_host: str = "localhost", jaeger_port: int = 16686):
        """
        Initialize Jaeger connection
        
        Args:
            jaeger_host: Jaeger query host
            jaeger_port: Jaeger query port
        """
        self.base_url = f"http://{jaeger_host}:{jaeger_port}/api/traces"
        self.service_url = f"http://{jaeger_host}:{jaeger_port}/api/services"
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
    
    def test_connection(self) -> bool:
        """Test if Jaeger is reachable"""
        try:
            resp = requests.get(self.service_url, timeout=5)
            return resp.status_code == 200
        except Exception as e:
            print(f"✗ Cannot connect to Jaeger: {e}")
            return False
    
    def get_services(self) -> List[str]:
        """
        Get all available services in Jaeger
        
        Returns:
            List of service names
        """
        try:
            resp = requests.get(self.service_url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            services = data.get('data', [])
            return services
        except Exception as e:
            print(f"✗ Error fetching services: {e}")
            return []
    
    def extract_traces(self, service_name: str, limit: int = 1000, 
                      lookback: int = 1800) -> Dict[str, Any]:
        """
        Extract traces for a specific service
        
        Args:
            service_name: Name of service to query (e.g., 'nginx-thrift')
            limit: Maximum number of traces to fetch
            lookback: How far back to look (in seconds)
        
        Returns:
            Dict with 'data' key containing list of traces
        """
        params = {
            'service': service_name,
            'limit': limit,
            'lookback': f'{lookback}s'
        }
        
        try:
            print(f"  Querying service '{service_name}' (limit={limit}, lookback={lookback}s)...")
            resp = requests.get(self.base_url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"  ✗ Error fetching traces: {e}")
            return {'data': []}
    
    def parse_trace(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a single Jaeger trace into structured format
        
        Args:
            trace: Raw trace object from Jaeger API
        
        Returns:
            Parsed trace with path, latencies, and span details
        """
        spans = trace.get('spans', [])
        
        if not spans:
            return None
        
        # Sort spans by start time to get execution order
        spans_sorted = sorted(spans, key=lambda s: s['startTime'])
        
        trace_id = trace.get('traceID')
        start_time = spans_sorted[0]['startTime']
        end_time = max(s['startTime'] + s['duration'] for s in spans_sorted)
        duration = end_time - start_time
        
        # Build service call path and extract per-span latencies
        path = []
        span_details = {}
        
        for span in spans_sorted:
            # Extract service name from processID
            process_id = span.get('processID', '')
            service = process_id.replace('_service', '')
            
            operation = span.get('operationName', 'unknown')
            span_duration = span.get('duration', 0)
            span_start = span.get('startTime', 0)
            
            # Extract tags
            tags = {}
            for tag in span.get('tags', []):
                key = tag.get('key', '')
                value = tag.get('value', '')
                if key and value:
                    tags[key] = value
            
            # Add to path
            path.append(f"{service}::{operation}")
            
            # Store span details
            span_key = f"{service}::{operation}"
            span_details[span_key] = {
                'duration_us': span_duration,
                'duration_ms': span_duration / 1000,
                'start_time_us': span_start,
                'tags': tags,
                'process_id': process_id
            }
        
        return {
            'trace_id': trace_id,
            'start_time_us': start_time,
            'duration_us': duration,
            'duration_ms': duration / 1000,
            'path': ' → '.join(path),
            'path_list': path,
            'num_spans': len(spans_sorted),
            'spans': span_details
        }
    
    def export_to_json(self, traces: List[Dict], output_file: str) -> None:
        """
        Export traces to JSON file
        
        Args:
            traces: List of parsed traces
            output_file: Output filename
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(traces, f, indent=2)
            print(f"✓ Exported {len(traces)} traces to JSON: {output_file}")
        except Exception as e:
            print(f"✗ Error exporting to JSON: {e}")
    
    def export_to_csv(self, traces: List[Dict], output_file: str) -> None:
        """
        Export trace summary to CSV file
        
        Args:
            traces: List of parsed traces
            output_file: Output filename
        """
        try:
            import csv
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'trace_id',
                    'duration_ms',
                    'num_spans',
                    'path'
                ])
                
                for trace in traces:
                    writer.writerow([
                        trace['trace_id'],
                        f"{trace['duration_ms']:.2f}",
                        trace['num_spans'],
                        trace['path']
                    ])
            
            print(f"✓ Exported {len(traces)} traces to CSV: {output_file}")
        except Exception as e:
            print(f"✗ Error exporting to CSV: {e}")
    
    def export_latency_distribution(self, traces: List[Dict], 
                                   output_file: str) -> None:
        """
        Export latency statistics per request path
        
        Args:
            traces: List of parsed traces
            output_file: Output filename
        """
        try:
            import csv
            
            # Group traces by path
            path_latencies = defaultdict(list)
            for trace in traces:
                path = trace['path']
                path_latencies[path].append(trace['duration_ms'])
            
            # Calculate statistics
            stats = []
            for path, latencies in path_latencies.items():
                sorted_lats = sorted(latencies)
                stats.append({
                    'path': path,
                    'count': len(latencies),
                    'avg_ms': sum(latencies) / len(latencies),
                    'min_ms': min(latencies),
                    'max_ms': max(latencies),
                    'p50_ms': sorted_lats[len(latencies) // 2],
                    'p99_ms': sorted_lats[int(len(latencies) * 0.99)],
                })
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'path', 'count', 'avg_ms', 'min_ms', 'max_ms', 'p50_ms', 'p99_ms'
                ])
                writer.writeheader()
                writer.writerows(stats)
            
            print(f"✓ Exported latency distributions: {output_file}")
        except Exception as e:
            print(f"✗ Error exporting latency distribution: {e}")
    
    def print_trace_statistics(self, traces: List[Dict]) -> None:
        """
        Print summary statistics about extracted traces
        
        Args:
            traces: List of parsed traces
        """
        if not traces:
            print("\n✗ No traces found!")
            print("\nTroubleshooting:")
            print("  1. Ensure workload generator (wrk2) is running")
            print("  2. Check that Jaeger is running: docker-compose ps | grep jaeger")
            print("  3. Wait at least 30 seconds after starting workload")
            print("  4. View Jaeger UI: http://localhost:16686")
            return
        
        durations_ms = [t['duration_ms'] for t in traces]
        paths = defaultdict(int)
        services_called = set()
        
        for trace in traces:
            paths[trace['path']] += 1
            services_called.update(trace['path_list'])
        
        print("\n" + "=" * 90)
        print("TRACE EXTRACTION SUMMARY")
        print("=" * 90)
        
        print(f"\nTraces Collected: {len(traces)}")
        print(f"Total Duration: {sum(durations_ms)/1000:.1f} seconds")
        print(f"Unique Services Called: {len(services_called)}")
        print(f"  {', '.join(sorted(services_called))}")
        
        print(f"\nLatency Statistics (across all traces):")
        print(f"  Average:  {sum(durations_ms)/len(durations_ms):8.2f} ms")
        print(f"  Min:      {min(durations_ms):8.2f} ms")
        print(f"  Max:      {max(durations_ms):8.2f} ms")
        print(f"  Median:   {sorted(durations_ms)[len(durations_ms)//2]:8.2f} ms")
        print(f"  P99:      {sorted(durations_ms)[int(len(durations_ms)*0.99)]:8.2f} ms")
        print(f"  P999:     {sorted(durations_ms)[int(len(durations_ms)*0.999)]:8.2f} ms")
        
        print(f"\nRequest Path Distribution ({len(paths)} unique paths):")
        for path, count in sorted(paths.items(), key=lambda x: x[1], reverse=True)[:10]:
            pct = (count / len(traces)) * 100
            path_display = path if len(path) < 100 else path[:97] + "..."
            print(f"  {pct:5.1f}% ({count:5d}x): {path_display}")
        
        if len(paths) > 10:
            print(f"  ... and {len(paths) - 10} more paths")
        
        print("\n" + "=" * 90)

def main():
    """Main entry point"""
    
    print("\n" + "=" * 90)
    print("DeathStarBench Jaeger Trace Extractor")
    print("=" * 90)
    
    # Initialize extractor
    print("\nInitializing Jaeger connection...")
    extractor = JaegerTraceExtractor(jaeger_host="localhost", jaeger_port=16686)
    
    # Test connection
    if not extractor.test_connection():
        print("\n✗ Cannot connect to Jaeger!")
        print(f"  Check if Jaeger is running:")
        print(f"  docker-compose ps | grep jaeger")
        print(f"  docker-compose logs jaeger-agent")
        sys.exit(1)
    
    print("✓ Connected to Jaeger")
    
    # Get services
    print("\nFetching available services...")
    services = extractor.get_services()
    
    if not services:
        print("✗ No services found in Jaeger")
        sys.exit(1)
    
    print(f"✓ Found {len(services)} services:")
    for svc in sorted(services):
        print(f"  - {svc}")
    
    # Extract traces from entry point
    print("\n" + "=" * 90)
    print("EXTRACTING TRACES")
    print("=" * 90)
    
    # Start from nginx-thrift (entry point) to get full request paths
    entry_point = 'nginx-thrift'
    print(f"\nQuerying traces from entry point service: {entry_point}")
    
    all_traces = []
    raw_traces = extractor.extract_traces(
        service_name=entry_point,
        limit=10000,
        lookback=1800  # Last 30 minutes
    )
    
    if raw_traces.get('data'):
        print(f"✓ Found {len(raw_traces['data'])} raw traces, parsing...")
        
        for i, trace in enumerate(raw_traces['data']):
            parsed = extractor.parse_trace(trace)
            if parsed:
                all_traces.append(parsed)
            if (i + 1) % 100 == 0:
                print(f"  Parsed {i + 1}/{len(raw_traces['data'])} traces...")
        
        print(f"✓ Successfully parsed {len(all_traces)} traces")
    else:
        print("✗ No traces returned from Jaeger")
        print("\nMake sure:")
        print("  1. System is running: docker-compose ps")
        print("  2. Workload generator is/was running: wrk2")
        print("  3. Enough time has passed (wait 30s after starting load)")
        sys.exit(1)
    
    # Print statistics
    extractor.print_trace_statistics(all_traces)
    
    # Export results with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    json_file = f"traces_{timestamp}.json"
    csv_file = f"traces_{timestamp}.csv"
    latency_file = f"traces_latency_distribution_{timestamp}.csv"
    
    print("\n" + "=" * 90)
    print("EXPORTING RESULTS")
    print("=" * 90)
    
    extractor.export_to_json(all_traces, json_file)
    extractor.export_to_csv(all_traces, csv_file)
    extractor.export_latency_distribution(all_traces, latency_file)
    
    print("\n" + "=" * 90)
    print("✓ SUCCESS")
    print("=" * 90)
    print("\nExtracted traces are ready for use in your Kubernetes cluster:")
    print(f"  - {json_file}                (Full trace details)")
    print(f"  - {csv_file}                 (Trace summary)")
    print(f"  - {latency_file}             (Latency distributions)")
    print("\nUse these files to:")
    print("  1. Generate synthetic workloads with realistic service call paths")
    print("  2. Replay requests with realistic latencies")
    print("  3. Test autoscaling and load-balancing algorithms")
    print("\n" + "=" * 90 + "\n")

if __name__ == '__main__':
    main()