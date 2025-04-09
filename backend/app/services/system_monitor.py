import logging
import psutil
import math
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class SystemMonitor:
    """
    Service to monitor system resources and provide recommendations
    for concurrent call handling based on available resources.
    """
    
    def __init__(self):
        # Resource usage estimates for a single call (based on benchmarks)
        # These values are estimates and should be adjusted based on real-world testing
        self.resources_per_call = {
            # CPU usage in percentage points per call
            'cpu_per_call': 5.0,  
            
            # Memory usage in MB per call
            'memory_per_call': 150.0,
            
            # Network bandwidth in Mbps per call
            'bandwidth_per_call': 0.1,
            
            # WebSocket connections per call
            'ws_connections_per_call': 1,
        }
        
        # Recommended safety margins (keep this percentage of resources free)
        self.safety_margins = {
            'cpu': 30.0,  # Keep 30% CPU free for system operations
            'memory': 25.0,  # Keep 25% memory free
            'network': 40.0,  # Keep 40% network bandwidth free
        }
        
        # Ultravox specific limitations
        self.ultravox_limits = {
            'max_concurrent_streams': 100,  # Theoretical max concurrent streams for Ultravox
            'api_rate_limit': 100  # Requests per minute to Ultravox API
        }
        
    def get_system_resources(self) -> Dict[str, Any]:
        """
        Get current system resource usage.
        
        Returns:
            Dictionary with system resource metrics
        """
        try:
            # Get CPU info
            cpu_usage = psutil.cpu_percent(interval=0.5)
            cpu_count = psutil.cpu_count(logical=True)
            
            # Get memory info
            memory = psutil.virtual_memory()
            memory_total_mb = memory.total / (1024 * 1024)
            memory_used_mb = memory.used / (1024 * 1024)
            memory_free_mb = memory.available / (1024 * 1024)
            memory_percent = memory.percent
            
            # Get disk info
            disk = psutil.disk_usage('/')
            disk_total_gb = disk.total / (1024 * 1024 * 1024)
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            disk_percent = disk.percent
            
            # Get network info (simplified)
            net_io = psutil.net_io_counters()
            
            return {
                'timestamp': psutil.time.time(),
                'cpu': {
                    'usage_percent': cpu_usage,
                    'core_count': cpu_count,
                    'available_percent': 100.0 - cpu_usage
                },
                'memory': {
                    'total_mb': memory_total_mb,
                    'used_mb': memory_used_mb,
                    'free_mb': memory_free_mb,
                    'usage_percent': memory_percent,
                    'available_percent': 100.0 - memory_percent
                },
                'disk': {
                    'total_gb': disk_total_gb,
                    'free_gb': disk_free_gb,
                    'usage_percent': disk_percent
                },
                'network': {
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv
                }
            }
        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            # Return default values if we can't get actual system info
            return {
                'cpu': {'usage_percent': 0, 'core_count': 4, 'available_percent': 100},
                'memory': {'total_mb': 8192, 'free_mb': 8192, 'usage_percent': 0, 'available_percent': 100},
                'disk': {'total_gb': 100, 'free_gb': 100, 'usage_percent': 0},
                'network': {'bytes_sent': 0, 'bytes_recv': 0}
            }
            
    def calculate_call_capacity(self) -> Dict[str, Any]:
        """
        Calculate how many concurrent calls the system can handle
        based on current resource usage and predefined benchmarks.
        
        Returns:
            Dictionary with call capacity recommendations
        """
        # Get current system resources
        resources = self.get_system_resources()
        
        # Calculate available resources after safety margins
        available_cpu = resources['cpu']['available_percent'] - self.safety_margins['cpu']
        available_memory_mb = (resources['memory']['available_percent'] - self.safety_margins['memory']) * resources['memory']['total_mb'] / 100
        
        # Calculate max calls based on each resource constraint
        max_calls_by_cpu = available_cpu / self.resources_per_call['cpu_per_call']
        max_calls_by_memory = available_memory_mb / self.resources_per_call['memory_per_call']
        
        # The limiting factor is the minimum of all constraints
        max_concurrent_calls = min(
            max_calls_by_cpu,
            max_calls_by_memory,
            self.ultravox_limits['max_concurrent_streams']
        )
        
        # Ensure we don't recommend negative values if system is already overloaded
        max_concurrent_calls = max(0, math.floor(max_concurrent_calls))
        
        # Calculate recommended outbound and inbound calls
        # Inbound calls are unpredictable, so we reserve more capacity for them
        recommended_outbound = math.floor(max_concurrent_calls * 0.4)  # 40% for outbound
        max_inbound = math.floor(max_concurrent_calls * 0.9)  # 90% max for inbound
        
        # Calculate call rate limits (calls per minute)
        # This considers both resource constraints and API rate limits
        calls_per_minute_by_resources = max_concurrent_calls * 60 / 5  # Assuming average call setup time of 5 seconds
        calls_per_minute = min(calls_per_minute_by_resources, self.ultravox_limits['api_rate_limit'])
        
        return {
            'max_concurrent_calls': max_concurrent_calls,
            'recommended_outbound_concurrent': recommended_outbound,
            'max_inbound_concurrent': max_inbound,
            'recommended_calls_per_minute': math.floor(calls_per_minute),
            'limiting_factor': self._get_limiting_factor(max_calls_by_cpu, max_calls_by_memory),
            'resource_usage': resources
        }
    
    def _get_limiting_factor(self, max_by_cpu: float, max_by_memory: float) -> str:
        """
        Determine which resource is the limiting factor for call capacity.
        
        Returns:
            String indicating the limiting resource
        """
        min_value = min(max_by_cpu, max_by_memory, self.ultravox_limits['max_concurrent_streams'])
        
        if min_value == max_by_cpu:
            return "CPU"
        elif min_value == max_by_memory:
            return "Memory"
        else:
            return "Ultravox API limits"

    def get_estimated_capacity(self, server_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get estimated call capacity based on server configuration rather than
        live resource monitoring. Useful for planning or when psutil is unavailable.
        
        Args:
            server_config: Dictionary with server specs. If None, uses default estimates.
            
        Returns:
            Dictionary with call capacity recommendations
        """
        # Default server configuration if none provided
        if server_config is None:
            server_config = {
                'cpu_cores': 4,
                'memory_gb': 8,
                'network_mbps': 100
            }
            
        # Calculate maximum theoretical capacity based on server specs
        cpu_capacity = (server_config['cpu_cores'] * 100 - self.safety_margins['cpu']) / self.resources_per_call['cpu_per_call']
        memory_capacity = (server_config['memory_gb'] * 1024 * (100 - self.safety_margins['memory']) / 100) / self.resources_per_call['memory_per_call']
        network_capacity = (server_config['network_mbps'] * (100 - self.safety_margins['network']) / 100) / self.resources_per_call['bandwidth_per_call']
        
        # The limiting factor is the minimum of all constraints
        max_concurrent_calls = min(
            cpu_capacity,
            memory_capacity,
            network_capacity,
            self.ultravox_limits['max_concurrent_streams']
        )
        
        # Ensure we don't recommend negative values
        max_concurrent_calls = max(0, math.floor(max_concurrent_calls))
        
        # Calculate recommended outbound and inbound calls
        recommended_outbound = math.floor(max_concurrent_calls * 0.4)  # 40% for outbound
        max_inbound = math.floor(max_concurrent_calls * 0.9)  # 90% max for inbound
        
        return {
            'max_concurrent_calls': max_concurrent_calls,
            'recommended_outbound_concurrent': recommended_outbound,
            'max_inbound_concurrent': max_inbound,
            'recommended_calls_per_minute': math.floor(min(max_concurrent_calls * 12, self.ultravox_limits['api_rate_limit'])),
            'limiting_factor': self._get_limiting_factor_from_capacity(cpu_capacity, memory_capacity, network_capacity),
            'theoretical_capacity': {
                'cpu_capacity': cpu_capacity,
                'memory_capacity': memory_capacity,
                'network_capacity': network_capacity,
                'ultravox_capacity': self.ultravox_limits['max_concurrent_streams']
            }
        }
    
    def _get_limiting_factor_from_capacity(self, cpu_capacity: float, memory_capacity: float, network_capacity: float) -> str:
        """
        Determine which resource is the limiting factor based on theoretical capacities.
        
        Returns:
            String indicating the limiting resource
        """
        min_value = min(cpu_capacity, memory_capacity, network_capacity, self.ultravox_limits['max_concurrent_streams'])
        
        if min_value == cpu_capacity:
            return "CPU"
        elif min_value == memory_capacity:
            return "Memory"
        elif min_value == network_capacity:
            return "Network bandwidth"
        else:
            return "Ultravox API limits"
            
# Create singleton instance
system_monitor = SystemMonitor()
