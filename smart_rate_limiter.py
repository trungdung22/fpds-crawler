#!/usr/bin/env python3
"""
Smart Rate Limiter for Large-Scale FPDS Crawling
Adaptive rate limiting that balances speed with avoiding detection
"""

import time
import random
import logging
from typing import Dict, List, Optional
from threading import Lock
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)

class SmartRateLimiter:
    """
    Adaptive rate limiter that adjusts based on success rates and blocking detection
    """
    
    def __init__(self, 
                 initial_delay: float = 1.0,
                 max_delay: float = 10.0,
                 min_delay: float = 0.1,
                 success_threshold: float = 0.95,
                 failure_threshold: float = 0.8,
                 window_size: int = 100):
        
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.min_delay = min_delay
        self.current_delay = initial_delay
        
        # Success rate tracking
        self.success_threshold = success_threshold  # 95% success rate target
        self.failure_threshold = failure_threshold  # 80% failure rate triggers slowdown
        self.window_size = window_size
        
        # Request history (last N requests)
        self.request_history = deque(maxlen=window_size)
        self.lock = Lock()
        
        # Adaptive settings
        self.aggressive_mode = False
        self.conservative_mode = False
        self.last_adjustment = datetime.now()
        self.adjustment_cooldown = 30  # seconds between adjustments
        
        # Statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.blocked_requests = 0
        self.start_time = datetime.now()
    
    def wait(self, request_type: str = "general"):
        """Smart wait with adaptive timing"""
        
        with self.lock:
            # Calculate base delay
            base_delay = self.current_delay
            
            # Add randomness to avoid patterns
            random_factor = random.uniform(0.8, 1.2)
            actual_delay = base_delay * random_factor
            
            # Apply mode-specific adjustments
            if self.aggressive_mode:
                actual_delay *= 0.5  # 50% faster in aggressive mode
            elif self.conservative_mode:
                actual_delay *= 2.0  # 2x slower in conservative mode
            
            # Ensure minimum delay
            actual_delay = max(actual_delay, self.min_delay)
            
            logger.debug(f"Rate limiter: waiting {actual_delay:.2f}s (base: {base_delay:.2f}s, mode: {'aggressive' if self.aggressive_mode else 'conservative' if self.conservative_mode else 'normal'})")
            
            time.sleep(actual_delay)
    
    def record_request(self, success: bool, blocked: bool = False):
        """Record request result and adjust rate limiting"""
        
        with self.lock:
            self.total_requests += 1
            if success:
                self.successful_requests += 1
            if blocked:
                self.blocked_requests += 1
            
            # Add to history
            self.request_history.append({
                'success': success,
                'blocked': blocked,
                'timestamp': datetime.now()
            })
            
            # Adjust rate limiting based on recent performance
            self._adjust_rate_limiting()
    
    def _adjust_rate_limiting(self):
        """Adjust rate limiting based on recent success rates"""
        
        if len(self.request_history) < 10:  # Need minimum data
            return
        
        # Check if enough time has passed since last adjustment
        if (datetime.now() - self.last_adjustment).total_seconds() < self.adjustment_cooldown:
            return
        
        # Calculate recent success rate
        recent_requests = list(self.request_history)[-50:]  # Last 50 requests
        success_count = sum(1 for req in recent_requests if req['success'])
        success_rate = success_count / len(recent_requests)
        
        # Calculate recent blocking rate
        blocked_count = sum(1 for req in recent_requests if req['blocked'])
        blocked_rate = blocked_count / len(recent_requests)
        
        logger.info(f"Recent performance: {success_rate:.1%} success, {blocked_rate:.1%} blocked, current delay: {self.current_delay:.2f}s")
        
        # Adjust based on performance
        if success_rate >= self.success_threshold and blocked_rate < 0.05:
            # High success, low blocking - can be more aggressive
            if not self.aggressive_mode:
                self.aggressive_mode = True
                self.conservative_mode = False
                self.current_delay = max(self.current_delay * 0.8, self.min_delay)
                logger.info(f"Switching to aggressive mode, delay: {self.current_delay:.2f}s")
        
        elif success_rate < self.failure_threshold or blocked_rate > 0.1:
            # Low success or high blocking - be more conservative
            if not self.conservative_mode:
                self.conservative_mode = True
                self.aggressive_mode = False
                self.current_delay = min(self.current_delay * 1.5, self.max_delay)
                logger.info(f"Switching to conservative mode, delay: {self.current_delay:.2f}s")
        
        else:
            # Normal performance - gradual adjustment
            if self.aggressive_mode and success_rate < self.success_threshold:
                self.aggressive_mode = False
                self.current_delay = min(self.current_delay * 1.2, self.max_delay)
                logger.info(f"Exiting aggressive mode, delay: {self.current_delay:.2f}s")
            elif self.conservative_mode and success_rate > self.success_threshold:
                self.conservative_mode = False
                self.current_delay = max(self.current_delay * 0.9, self.min_delay)
                logger.info(f"Exiting conservative mode, delay: {self.current_delay:.2f}s")
        
        self.last_adjustment = datetime.now()
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        with self.lock:
            duration = datetime.now() - self.start_time
            requests_per_minute = self.total_requests / (duration.total_seconds() / 60) if duration.total_seconds() > 0 else 0
            
            return {
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'blocked_requests': self.blocked_requests,
                'success_rate': self.successful_requests / self.total_requests if self.total_requests > 0 else 0,
                'blocked_rate': self.blocked_requests / self.total_requests if self.total_requests > 0 else 0,
                'current_delay': self.current_delay,
                'mode': 'aggressive' if self.aggressive_mode else 'conservative' if self.conservative_mode else 'normal',
                'requests_per_minute': requests_per_minute,
                'duration': str(duration)
            }

class BatchRateLimiter:
    """
    Rate limiter optimized for batch processing of large datasets
    """
    
    def __init__(self, 
                 batch_size: int = 100,
                 batch_delay: float = 5.0,
                 max_concurrent_batches: int = 4):
        
        self.batch_size = batch_size
        self.batch_delay = batch_delay
        self.max_concurrent_batches = max_concurrent_batches
        
        self.active_batches = 0
        self.lock = Lock()
        self.last_batch_time = 0
    
    def can_start_batch(self) -> bool:
        """Check if we can start a new batch"""
        with self.lock:
            if self.active_batches >= self.max_concurrent_batches:
                return False
            
            # Ensure minimum delay between batches
            current_time = time.time()
            if current_time - self.last_batch_time < self.batch_delay:
                return False
            
            self.active_batches += 1
            self.last_batch_time = current_time
            return True
    
    def finish_batch(self):
        """Mark a batch as finished"""
        with self.lock:
            self.active_batches = max(0, self.active_batches - 1)
    
    def wait_for_batch_slot(self):
        """Wait until a batch slot is available"""
        while not self.can_start_batch():
            time.sleep(1)

class AdaptiveProxyManager:
    """
    Enhanced proxy manager with smart rate limiting
    """
    
    def __init__(self, proxy_list: List[str] = None):
        self.proxy_list = proxy_list or []
        self.rate_limiters = {}  # One per proxy
        self.batch_limiter = BatchRateLimiter()
        
        # Initialize rate limiters for each proxy
        for proxy in self.proxy_list:
            self.rate_limiters[proxy] = SmartRateLimiter()
    
    def get_proxy_with_limiter(self, proxy: str) -> Optional[SmartRateLimiter]:
        """Get rate limiter for specific proxy"""
        return self.rate_limiters.get(proxy)
    
    def get_best_proxy(self) -> Optional[str]:
        """Get proxy with best recent performance"""
        if not self.proxy_list:
            return None
        
        # Simple selection - could be enhanced with more sophisticated logic
        return random.choice(self.proxy_list)
    
    def get_batch_stats(self) -> Dict:
        """Get statistics for all proxies"""
        stats = {}
        for proxy, limiter in self.rate_limiters.items():
            stats[proxy] = limiter.get_stats()
        return stats

# Example usage and testing
def test_rate_limiting_performance():
    """Test different rate limiting strategies"""
    
    print("Rate Limiting Performance Analysis")
    print("=" * 50)
    
    # Scenario: 100,000 records
    total_records = 100000
    
    # Strategy 1: Fixed delay (current approach)
    fixed_delay = 3.5  # seconds
    fixed_time = total_records * fixed_delay / 3600  # hours
    print(f"Fixed delay ({fixed_delay}s): {fixed_time:.1f} hours")
    
    # Strategy 2: Smart adaptive (our new approach)
    # Assumes we can start with 1s delay and optimize to 0.5s
    smart_avg_delay = 0.75  # seconds
    smart_time = total_records * smart_avg_delay / 3600  # hours
    print(f"Smart adaptive (~{smart_avg_delay}s avg): {smart_time:.1f} hours")
    
    # Strategy 3: Batch processing
    batch_size = 100
    batch_delay = 5  # seconds between batches
    batches = total_records // batch_size
    batch_time = batches * batch_delay / 3600  # hours
    print(f"Batch processing ({batch_size} per batch): {batch_time:.1f} hours")
    
    # Strategy 4: Multi-threaded with smart limiting
    workers = 8
    smart_multi_time = smart_time / workers
    print(f"Multi-threaded ({workers} workers) + smart: {smart_multi_time:.1f} hours")
    
    print(f"\nImprovement: {fixed_time/smart_multi_time:.1f}x faster!")

if __name__ == "__main__":
    test_rate_limiting_performance()
    
    # Example usage
    print("\n" + "=" * 50)
    print("Example Usage:")
    
    # Initialize smart rate limiter
    limiter = SmartRateLimiter(initial_delay=1.0)
    
    # Simulate some requests
    for i in range(10):
        success = random.random() > 0.1  # 90% success rate
        blocked = random.random() < 0.02  # 2% blocking rate
        
        limiter.record_request(success, blocked)
        limiter.wait()
        
        if i % 5 == 0:
            stats = limiter.get_stats()
            print(f"Request {i}: {stats['success_rate']:.1%} success, delay: {stats['current_delay']:.2f}s") 