"""
Performance monitoring and optimization utilities
"""
from time import time
from asyncio import create_task, gather
from functools import wraps
from typing import Dict, List, Any
from collections import defaultdict

from FZBypass import LOGGER


class PerformanceMonitor:
    """Monitor and track bypass performance"""
    
    def __init__(self):
        self.stats = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.success_counts = defaultdict(int)
    
    def record_bypass(self, domain: str, duration: float, success: bool):
        """Record bypass attempt statistics"""
        self.stats[domain].append(duration)
        if success:
            self.success_counts[domain] += 1
        else:
            self.error_counts[domain] += 1
    
    def get_domain_stats(self, domain: str) -> Dict[str, Any]:
        """Get statistics for a specific domain"""
        durations = self.stats[domain]
        if not durations:
            return {"avg_time": 0, "success_rate": 0, "total_attempts": 0}
        
        total_attempts = len(durations)
        avg_time = sum(durations) / total_attempts
        success_rate = (self.success_counts[domain] / total_attempts) * 100
        
        return {
            "avg_time": round(avg_time, 2),
            "success_rate": round(success_rate, 2),
            "total_attempts": total_attempts,
            "fastest": min(durations),
            "slowest": max(durations)
        }
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall performance statistics"""
        all_durations = []
        total_success = 0
        total_attempts = 0
        
        for domain in self.stats:
            all_durations.extend(self.stats[domain])
            total_success += self.success_counts[domain]
            total_attempts += len(self.stats[domain])
        
        if not all_durations:
            return {"avg_time": 0, "success_rate": 0, "total_attempts": 0}
        
        return {
            "avg_time": round(sum(all_durations) / len(all_durations), 2),
            "success_rate": round((total_success / total_attempts) * 100, 2) if total_attempts > 0 else 0,
            "total_attempts": total_attempts,
            "domains_supported": len(self.stats)
        }


# Global performance monitor instance
perf_monitor = PerformanceMonitor()


def track_performance(func):
    """Decorator to track bypass performance"""
    @wraps(func)
    async def wrapper(url: str, *args, **kwargs):
        domain = url.split('/')[2] if '://' in url else 'unknown'
        start_time = time()
        success = False
        
        try:
            result = await func(url, *args, **kwargs)
            success = True
            return result
        except Exception as e:
            LOGGER.error(f"Bypass failed for {domain}: {e}")
            raise
        finally:
            duration = time() - start_time
            perf_monitor.record_bypass(domain, duration, success)
    
    return wrapper


async def optimize_concurrent_requests(urls: List[str], max_concurrent: int = 5) -> List[Any]:
    """Optimize concurrent request processing"""
    results = []
    
    # Group URLs by domain to avoid overwhelming specific servers
    domain_groups = defaultdict(list)
    for url in urls:
        domain = url.split('/')[2] if '://' in url else 'unknown'
        domain_groups[domain].append(url)
    
    # Process each domain group with controlled concurrency
    for domain, domain_urls in domain_groups.items():
        LOGGER.info(f"Processing {len(domain_urls)} URLs from {domain}")
        
        # Process in batches
        for i in range(0, len(domain_urls), max_concurrent):
            batch = domain_urls[i:i + max_concurrent]
            batch_tasks = [create_task(process_single_url(url)) for url in batch]
            
            try:
                batch_results = await gather(*batch_tasks, return_exceptions=True)
                results.extend(batch_results)
            except Exception as e:
                LOGGER.error(f"Batch processing error for {domain}: {e}")
                results.extend([Exception(f"Batch error: {e}") for _ in batch])
    
    return results


async def process_single_url(url: str) -> str:
    """Process a single URL with performance tracking"""
    from FZBypass.core.bypass_enhanced import single_bypass
    return await single_bypass(url)


class RateLimiter:
    """Simple rate limiter for bypass requests"""
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed based on rate limits"""
        now = time()
        user_requests = self.requests[identifier]
        
        # Remove old requests outside time window
        self.requests[identifier] = [
            req_time for req_time in user_requests 
            if now - req_time < self.time_window
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(now)
            return True
        
        return False
    
    def get_reset_time(self, identifier: str) -> int:
        """Get time until rate limit resets"""
        if identifier not in self.requests or not self.requests[identifier]:
            return 0
        
        oldest_request = min(self.requests[identifier])
        reset_time = oldest_request + self.time_window - time()
        return max(0, int(reset_time))


# Global rate limiter instance
rate_limiter = RateLimiter()