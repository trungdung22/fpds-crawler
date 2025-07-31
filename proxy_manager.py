#!/usr/bin/env python3
"""
Proxy Manager for FPDS.gov Crawler
Handles proxy rotation, rate limiting, and anti-detection
"""

import requests
import time
import random
import logging
from typing import List, Dict, Optional
from threading import Lock
import json
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)

class ProxyManager:
    """Manages proxy rotation and rate limiting"""
    
    def __init__(self, proxy_list: List[str] = None, max_requests_per_proxy: int = 100):
        self.proxies = proxy_list or []
        self.max_requests_per_proxy = max_requests_per_proxy
        self.proxy_stats = {}  # Track usage per proxy
        self.lock = Lock()
        self.current_proxy_index = 0
        
        # Rate limiting settings
        self.min_delay = 0.5  # Minimum seconds between requests (much faster!)
        self.max_delay = 5  # Maximum seconds between requests
        self.last_request_time = 0
        
        # Smart rate limiting
        self.adaptive_mode = True
        self.success_count = 0
        self.error_count = 0
        self.recent_requests = deque(maxlen=50)  # Track last 50 requests
        
        # Anti-detection settings
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59'
        ]
        
        # Initialize proxy stats
        for proxy in self.proxies:
            self.proxy_stats[proxy] = {
                'requests': 0,
                'errors': 0,
                'last_used': None,
                'blocked': False
            }
    
    def add_proxy(self, proxy: str):
        """Add a new proxy to the rotation"""
        with self.lock:
            if proxy not in self.proxies:
                self.proxies.append(proxy)
                self.proxy_stats[proxy] = {
                    'requests': 0,
                    'errors': 0,
                    'last_used': None,
                    'blocked': False
                }
                logger.info(f"Added proxy: {proxy}")
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next available proxy with round-robin selection"""
        if not self.proxies:
            return None
        
        with self.lock:
            attempts = 0
            while attempts < len(self.proxies):
                proxy = self.proxies[self.current_proxy_index]
                self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
                
                # Check if proxy is available
                if not self.proxy_stats[proxy]['blocked'] and \
                   self.proxy_stats[proxy]['requests'] < self.max_requests_per_proxy:
                    return proxy
                
                attempts += 1
            
            # If all proxies are blocked or at limit, reset stats
            logger.warning("All proxies blocked or at limit, resetting stats")
            self._reset_proxy_stats()
            return self.proxies[0] if self.proxies else None
    
    def _reset_proxy_stats(self):
        """Reset proxy statistics"""
        for proxy in self.proxy_stats:
            self.proxy_stats[proxy]['requests'] = 0
            self.proxy_stats[proxy]['errors'] = 0
            self.proxy_stats[proxy]['blocked'] = False
    
    def mark_proxy_success(self, proxy: str):
        """Mark proxy as successfully used"""
        with self.lock:
            if proxy in self.proxy_stats:
                self.proxy_stats[proxy]['requests'] += 1
                self.proxy_stats[proxy]['last_used'] = datetime.now()
            
            # Update adaptive rate limiting stats
            self.success_count += 1
            self.recent_requests.append({'success': True, 'timestamp': datetime.now()})
    
    def mark_proxy_error(self, proxy: str, error_type: str = "general"):
        """Mark proxy as having an error"""
        with self.lock:
            if proxy in self.proxy_stats:
                self.proxy_stats[proxy]['errors'] += 1
                self.proxy_stats[proxy]['last_used'] = datetime.now()
                
                # Block proxy if too many errors
                if self.proxy_stats[proxy]['errors'] >= 5:
                    self.proxy_stats[proxy]['blocked'] = True
                    logger.warning(f"Blocked proxy {proxy} due to {self.proxy_stats[proxy]['errors']} errors")
            
            # Update adaptive rate limiting stats
            self.error_count += 1
            self.recent_requests.append({'success': False, 'timestamp': datetime.now()})
    
    def mark_proxy_blocked(self, proxy: str):
        """Mark proxy as blocked by target site"""
        with self.lock:
            if proxy in self.proxy_stats:
                self.proxy_stats[proxy]['blocked'] = True
                logger.warning(f"Proxy {proxy} blocked by target site")
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent"""
        return random.choice(self.user_agents)
    
    def enforce_rate_limit(self):
        """Smart rate limiting that adapts based on success rates"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Calculate adaptive delay based on recent performance
        if self.adaptive_mode and len(self.recent_requests) >= 10:
            success_rate = self.success_count / max(1, self.success_count + self.error_count)
            
            if success_rate >= 0.95:  # 95%+ success rate
                # Can be more aggressive
                adaptive_delay = max(self.min_delay, self.min_delay * 0.5)
            elif success_rate >= 0.90:  # 90%+ success rate
                # Normal speed
                adaptive_delay = self.min_delay
            elif success_rate >= 0.80:  # 80%+ success rate
                # Slightly slower
                adaptive_delay = self.min_delay * 1.5
            else:
                # Much slower due to errors
                adaptive_delay = self.max_delay
        else:
            # Default delay for initial requests
            adaptive_delay = self.min_delay
        
        # Ensure minimum delay
        if time_since_last < adaptive_delay:
            sleep_time = adaptive_delay - time_since_last
            time.sleep(sleep_time)
        
        # Add small randomness to avoid patterns
        random_delay = random.uniform(0, adaptive_delay * 0.2)
        time.sleep(random_delay)
        
        self.last_request_time = time.time()
    
    def get_proxy_stats(self) -> Dict:
        """Get current proxy statistics"""
        with self.lock:
            return self.proxy_stats.copy()
    
    def save_proxy_list(self, filename: str):
        """Save proxy list to file"""
        with open(filename, 'w') as f:
            json.dump({
                'proxies': self.proxies,
                'stats': self.proxy_stats
            }, f, indent=2, default=str)
    
    def load_proxy_list(self, filename: str):
        """Load proxy list from file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.proxies = data.get('proxies', [])
                self.proxy_stats = data.get('stats', {})
                logger.info(f"Loaded {len(self.proxies)} proxies from {filename}")
        except FileNotFoundError:
            logger.warning(f"Proxy file {filename} not found")


# Example proxy sources
def get_free_proxies() -> List[str]:
    """Get list of free proxies (use with caution)"""
    proxies = []
    
    try:
        # Free proxy list (replace with your preferred source)
        response = requests.get('https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all')
        if response.status_code == 200:
            proxy_list = response.text.strip().split('\n')
            proxies.extend([f"http://{proxy}" for proxy in proxy_list if proxy])
    except Exception as e:
        logger.error(f"Error fetching free proxies: {e}")
    
    return proxies


def get_paid_proxy_services() -> List[str]:
    """Get proxies from paid services (recommended for production)"""
    # Example paid proxy services
    services = {
        'brightdata': 'https://brightdata.com/',
        'smartproxy': 'https://smartproxy.com/',
        'oxylabs': 'https://oxylabs.io/',
        'proxyrack': 'https://proxyrack.com/'
    }
    
    logger.info("Paid proxy services (recommended for production):")
    for name, url in services.items():
        logger.info(f"  {name}: {url}")
    
    return []

if __name__ == "__main__":
    # Example usage
    proxy_manager = ProxyManager()
    
    # Add some example proxies (replace with real ones)
    example_proxies = [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080",
        "http://proxy3.example.com:8080"
    ]
    
    for proxy in example_proxies:
        proxy_manager.add_proxy(proxy)
    
    print("Proxy Manager initialized")
    print(f"Available proxies: {len(proxy_manager.proxies)}")
    print(f"Next proxy: {proxy_manager.get_next_proxy()}")
    print(f"Random user agent: {proxy_manager.get_random_user_agent()}") 