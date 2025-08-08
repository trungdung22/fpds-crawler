#!/usr/bin/env python3
"""
High-Performance FPDS.gov Crawler
Optimized for large-scale extraction (100,000+ records) with minimal delays
"""
from fpds_enhanced_extractor import FPDSEnhancedExtractor
from smart_rate_limiter import SmartRateLimiter, BatchRateLimiter
import argparse
import sys
from datetime import datetime, timedelta
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue
import time
import os
import glob

logger = logging.getLogger(__name__)


class FPDSHighPerformanceExtractor:
    """
    High-performance extractor optimized for large datasets
    """
    
    def __init__(self, 
                 max_workers: int = 16,
                 batch_size: int = 100,
                 initial_delay: float = 0.5,
                 proxy_list: list = None):
        
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.proxy_list = proxy_list or []
        
        # Smart rate limiting
        self.rate_limiter = SmartRateLimiter(
            initial_delay=initial_delay,
            min_delay=0.1,  # Very fast minimum
            max_delay=2.0   # Reasonable maximum
        )
        
        # Batch processing - allow more concurrent batches to utilize all workers
        self.batch_limiter = BatchRateLimiter(
            batch_size=batch_size,
            batch_delay=1.0,  # Shorter delay between batches
            max_concurrent_batches=max_workers  # Allow all workers to run concurrently
        )
        
        # Progress tracking
        self.progress_lock = threading.Lock()
        self.total_processed = 0
        self.current_page = 0
        self.total_pages = 0
        self.target_records = 0
        self.start_time = datetime.now()
        
        # Worker utilization tracking
        self.active_workers = set()
        self.worker_lock = threading.Lock()
        
        # Results storage
        self.results_queue = Queue()
        self.all_contracts = []
        self.fetch_all = False
        
        # Error tracking for retry
        self.failed_requests = []
        self.failed_lock = threading.Lock()
    
    def extract_large_dataset(self, 
                             start_date: str, 
                             end_date: str,
                             target_records: int = 100000,
                             additional_filters: dict = None) -> list:
        """
        Extract large dataset with optimized performance
        """
        
        logger.info(f"Starting large-scale extraction: {target_records:,} records")
        logger.info(f"Workers: {self.max_workers}, Batch size: {self.batch_size}")
        
        # Get total available records
        enhanced_extractor = FPDSEnhancedExtractor(use_selenium=False)
        total_available = enhanced_extractor.fetch_total_record(start_date, end_date, additional_filters)
        
        # Use the smaller of target_records or total_available
        actual_target = min(target_records, total_available) if total_available > 0 else target_records
        
        # Store target for progress tracking
        self.target_records = actual_target
        
        # Calculate total pages needed
        records_per_page = 30
        total_pages = (actual_target + records_per_page - 1) // records_per_page
        
        # Set total pages for progress tracking
        self.total_pages = total_pages
        
        logger.info(f"Estimated pages needed: {total_pages:,}")
        
        # Process in batches - optimize for worker utilization
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit batch tasks
            futures = []
            
            # Calculate optimal batch size to utilize all workers
            # For 556 pages and 16 workers, we want ~35 batches (556/16 ≈ 35)
            optimal_batch_size = max(1, total_pages // (self.max_workers * 2))  # Ensure at least 2x workers worth of batches
            
            logger.info(f"Using optimal batch size: {optimal_batch_size} pages per batch")
            
            batch_count = 0
            for batch_start in range(0, total_pages, optimal_batch_size):
                batch_end = min(batch_start + optimal_batch_size, total_pages)
                batch_count += 1
                
                future = executor.submit(
                    self._process_page_batch,
                    start_date, end_date, batch_start, batch_end, additional_filters
                )
                futures.append(future)
            
            logger.info(f"Created {batch_count} batches for {self.max_workers} workers (ratio: {batch_count/self.max_workers:.1f})")
            
            # Collect results
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    if batch_results:
                        self.all_contracts.extend(batch_results)
                        # Progress is already updated in real-time, so we don't need to update again
                        
                        # Check if we've reached our target
                        if self.total_processed >= self.target_records:
                            logger.info(f"Reached target of {self.target_records} records, stopping all processing")
                            break
                except Exception as e:
                    logger.error(f"Batch processing error: {e}")
        
        logger.info(f"Extraction completed: {len(self.all_contracts):,} records")
        self._print_final_stats()
        
        return self.all_contracts
    
    def _process_page_batch(self, 
                           start_date: str, 
                           end_date: str, 
                           start_page: int, 
                           end_page: int,
                           additional_filters: dict) -> list:
        """
        Process a batch of pages
        """
        
        batch_contracts = []
        
        # Wait for batch slot
        self.batch_limiter.wait_for_batch_slot()
        
        worker_id = threading.current_thread().name
        
        # Track active workers
        with self.worker_lock:
            self.active_workers.add(worker_id)
            logger.info(f"[Worker-{worker_id}] Starting batch: pages {start_page} to {end_page-1} (Active workers: {len(self.active_workers)})")
        
        try:
            for page_num in range(start_page, end_page):
                # Update current page for progress tracking
                with self.progress_lock:
                    self.current_page = page_num + 1
                
                # Smart rate limiting
                self.rate_limiter.wait()
                
                # Extract page
                page_contracts = self._extract_single_page(
                    start_date, end_date, page_num, additional_filters
                )
                
                if page_contracts:
                    batch_contracts.extend(page_contracts)
                    
                    # Update progress in real-time for each page
                    self._update_progress(len(page_contracts))
                    
                    # Record success
                    self.rate_limiter.record_request(True, False)
                    
                    # Check if we've reached our target
                    if self.total_processed >= self.target_records:
                        logger.info(f"Reached target of {self.target_records} records, stopping batch processing")
                        break
                else:
                    # Record failure and track for retry
                    self.rate_limiter.record_request(False, False)
                    self._track_failed_request("index", page_num, start_date, end_date, additional_filters)
                    logger.warning(f"Failed to extract page {page_num} - added to retry list")
                
                # Check if we have enough records (but don't stop early - let it complete the page)
                # The target check should be done at the batch level, not individual page level
        
        finally:
            self.batch_limiter.finish_batch()
            
            # Remove from active workers
            with self.worker_lock:
                self.active_workers.discard(worker_id)
                logger.info(f"[Worker-{worker_id}] Finished batch (Active workers: {len(self.active_workers)})")
        
        return batch_contracts
    
    def _extract_single_page(self, 
                            start_date: str, 
                            end_date: str, 
                            page_num: int,
                            additional_filters: dict) -> list:
        """
        Extract contracts from a single page using enhanced extractor logic
        """
        
        try:
            # Import the enhanced extractor for parsing

            
            # Build query
            query = f"ESTIMATED_COMPLETION_DATE:[{start_date},{end_date}]"
            
            if additional_filters:
                for key, value in additional_filters.items():
                    query += f" {key}:\"{value}\""
            
            # Calculate start parameter
            start_param = page_num * 30
            
            params = {
                'q': query,
                's': 'FPDS.GOV',
                'templateName': '1.5.3',
                'indexName': 'awardfull',
                'start': str(start_param)
            }
            
            # Use enhanced extractor for parsing
            enhanced_extractor = FPDSEnhancedExtractor(use_selenium=False)
            
            # Make request
            response = enhanced_extractor.session.get(
                "https://www.fpds.gov/ezsearch/fpdsportal", 
                params=params, timeout=30
            )
            
            if response.status_code == 200:
                # Parse contracts using enhanced extractor logic
                contracts = enhanced_extractor._extract_contracts_from_search_page(
                    response.text, 100  # Allow more contracts per page to see what's available
                )
                
                worker_id = threading.current_thread().name
                logger.info(f"[Worker-{worker_id}] Page {page_num}: Found {len(contracts)} contracts (start_param: {start_param})")
                
                # Extract detail data for each contract
                detailed_contracts = []
                for contract in contracts:
                    detail_data = enhanced_extractor._extract_contract_details(contract)
                    if detail_data:
                        contract['detail_data'] = detail_data
                    else:
                        # Track failed detail extraction
                        self._track_failed_request("detail", page_num, start_date, end_date, additional_filters, contract)
                        logger.warning(f"Failed to extract details for contract {contract.get('award_id_mod', 'Unknown')} on page {page_num}")
                    detailed_contracts.append(contract)
                
                return detailed_contracts
            else:
                logger.warning(f"Page {page_num} failed: {response.status_code}")
                # Track HTTP errors
                self._track_failed_request("index", page_num, start_date, end_date, additional_filters, 
                                         error_info=f"HTTP {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting page {page_num}: {e}")
            # Track exception errors
            self._track_failed_request("index", page_num, start_date, end_date, additional_filters, 
                                     error_info=str(e))
            return []
    
    def _update_progress(self, new_records: int):
        """Update progress tracking"""
        
        with self.progress_lock:
            self.total_processed += new_records
            
            # Calculate progress
            elapsed = datetime.now() - self.start_time
            rate = self.total_processed / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
            
            # Calculate page progress
            page_progress = f"{self.current_page}/{self.total_pages}" if self.total_pages > 0 else "N/A"
            page_percentage = f"{(self.current_page / self.total_pages * 100):.1f}%" if self.total_pages > 0 else "N/A"
            
            # Show target vs actual
            target_info = f"({self.total_processed}/{self.target_records})" if self.target_records > 0 else f"({self.total_processed})"
            record_percentage = f"{(self.total_processed / self.target_records * 100):.1f}%" if self.total_processed > 0 else "N/A"
            worker_id = threading.current_thread().name
            logger.info(f"[Worker-{worker_id}] Progress: {self.total_processed:,} records {target_info}, "
                       f"Page: {page_progress} ({record_percentage}), "
                       f"Rate: {rate:.1f} records/sec, "
                       f"Elapsed: {elapsed}")
    
    def _track_failed_request(self, request_type: str, page_num: int, start_date: str, end_date: str, 
                             additional_filters: dict, contract: dict = None, error_info: str = None):
        """Track failed requests for later retry"""
        
        with self.failed_lock:
            failed_request = {
                'type': request_type,  # 'index' or 'detail'
                'page_num': page_num,
                'start_date': start_date,
                'end_date': end_date,
                'additional_filters': additional_filters,
                'timestamp': datetime.now().isoformat(),
                'contract': contract if contract else None,
                'error_info': error_info
            }
            
            self.failed_requests.append(failed_request)
            
            # Log summary of failed requests
            index_failures = len([f for f in self.failed_requests if f['type'] == 'index'])
            detail_failures = len([f for f in self.failed_requests if f['type'] == 'detail'])
            logger.info(f"Failed requests tracked: {index_failures} index, {detail_failures} detail (total: {len(self.failed_requests)})")
    
    def _save_failed_requests(self) -> str:
        """Save failed requests to a JSON file for later retry in a subfolder"""
        if not self.failed_requests:
            return ""
        os.makedirs('failed_request_data', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join('failed_request_data', f"failed_requests_{timestamp}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.failed_requests, f, indent=2, ensure_ascii=False)
        return filename
    
    def retry_failed_requests(self, max_retries: int = 3) -> list:
        """Retry failed requests and return successfully processed contracts"""
        
        if not self.failed_requests:
            logger.info("No failed requests to retry")
            return []
        
        logger.info(f"Retrying {len(self.failed_requests)} failed requests...")
        
        retried_contracts = []
        successful_retries = 0
        
        for attempt in range(max_retries):
            logger.info(f"Retry attempt {attempt + 1}/{max_retries}")
            
            # Create a copy of failed requests to iterate over
            failed_copy = self.failed_requests.copy()
            self.failed_requests.clear()
            
            for failed_request in failed_copy:
                try:
                    if failed_request['type'] == 'index':
                        # Retry index page
                        contracts = self._extract_single_page(
                            failed_request['start_date'],
                            failed_request['end_date'],
                            failed_request['page_num'],
                            failed_request['additional_filters']
                        )
                        if contracts:
                            retried_contracts.extend(contracts)
                            successful_retries += 1
                            logger.info(f"Successfully retried index page {failed_request['page_num']}")
                        else:
                            # Still failed, add back to retry list
                            self.failed_requests.append(failed_request)
                    
                    elif failed_request['type'] == 'detail':
                        # Retry detail extraction
                        if failed_request['contract']:
                            enhanced_extractor = FPDSEnhancedExtractor(use_selenium=False)
                            detail_data = enhanced_extractor._extract_contract_details(failed_request['contract'])
                            if detail_data:
                                failed_request['contract']['detail_data'] = detail_data
                                retried_contracts.append(failed_request['contract'])
                                successful_retries += 1
                                logger.info(f"Successfully retried detail extraction for contract {failed_request['contract'].get('award_id_mod', 'Unknown')}")
                            else:
                                # Still failed, add back to retry list
                                self.failed_requests.append(failed_request)
                    
                    # Rate limiting for retries
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Retry failed for {failed_request['type']} request: {e}")
                    # Add back to retry list
                    self.failed_requests.append(failed_request)
            
            if not self.failed_requests:
                logger.info("All failed requests successfully retried!")
                break
        
        logger.info(f"Retry completed: {successful_retries} successful, {len(self.failed_requests)} still failed")
        return retried_contracts
    
    def _print_final_stats(self):
        """Print final statistics"""
        
        duration = datetime.now() - self.start_time
        rate_limiter_stats = self.rate_limiter.get_stats()
        
        print("\n" + "=" * 60)
        print("HIGH-PERFORMANCE EXTRACTION COMPLETED")
        print("=" * 60)
        print(f"Total records: {len(self.all_contracts):,}")
        print(f"Pages processed: {self.current_page}/{self.total_pages}")
        print(f"Duration: {duration}")
        print(f"Average rate: {len(self.all_contracts)/duration.total_seconds()*60:.1f} records/minute")
        print(f"Success rate: {rate_limiter_stats['success_rate']:.1%}")
        print(f"Final delay: {rate_limiter_stats['current_delay']:.2f}s")
        print(f"Mode: {rate_limiter_stats['mode']}")
        print(f"Parallel workers used: {self.max_workers}")
        
        # Show failed requests summary
        if self.failed_requests:
            index_failures = len([f for f in self.failed_requests if f['type'] == 'index'])
            detail_failures = len([f for f in self.failed_requests if f['type'] == 'detail'])
            print(f"Failed requests: {index_failures} index, {detail_failures} detail (total: {len(self.failed_requests)})")
            print(f"Failed requests saved to: {self._save_failed_requests()}")
        else:
            print("No failed requests")

def load_failed_requests_from_folder(folder: str) -> list:
    """Load all failed request JSON files from a folder and return a combined list"""
    all_failed = []
    for file in glob.glob(os.path.join(folder, 'failed_retry_*.json')):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_failed.extend(data)
        except Exception as e:
            logger.error(f"Error loading {file}: {e}")
    return all_failed

def main():
    parser = argparse.ArgumentParser(description='High-performance FPDS contract data extractor')
    
    # Required parameters
    parser.add_argument('--start-date',
                       help='Start date in YYYY/MM/DD format', default="2026/02/01")
    parser.add_argument('--end-date',
                       help='End date in YYYY/MM/DD format', default="2026/02/28")
    
    # Performance settings
    parser.add_argument('--target-records', type=int, default=200000,
                       help='Target number of records to extract (default: 100,000)')
    parser.add_argument('--workers', type=int, default=16,
                       help='Number of worker threads (default: 16)')
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Batch size for processing (default: 100)')
    parser.add_argument('--initial-delay', type=float, default=0.5,
                       help='Initial delay between requests in seconds (default: 0.5)')
    
    # Output settings
    parser.add_argument('--output', default='fpds_high_performance',
                       help='Output filename base')
    
    # Filters
    parser.add_argument('--agency', help='Filter by agency name')
    parser.add_argument('--vendor', help='Filter by vendor name')
    
    # Retry settings
    parser.add_argument('--enable-retry', action='store_true', default=True,
                       help='Enable automatic retry of failed requests')
    parser.add_argument('--max-retries', type=int, default=3,
                       help='Maximum number of retry attempts (default: 3)')
    parser.add_argument('--retry-failed', action='store_true', default=False,
                       help='Retry all failed requests in failed_request_data/ and save to a retry file')
    
    args = parser.parse_args()
    
    # Build filters
    additional_filters = {}
    if args.agency:
        additional_filters['CONTRACTING_AGENCY_NAME'] = args.agency
    if args.vendor:
        additional_filters['UEI_NAME'] = args.vendor
    
    print("=" * 60)
    print("HIGH-PERFORMANCE FPDS CRAWLER")
    print("=" * 60)
    print(f"Target records: {args.target_records:,}")
    print(f"Workers: {args.workers}")
    print(f"Batch size: {args.batch_size}")
    print(f"Initial delay: {args.initial_delay}s")
    print(f"Date range: {args.start_date} to {args.end_date}")
    
    if additional_filters:
        print(f"Filters: {additional_filters}")
    
    print(f"Retry enabled: {args.enable_retry}")
    if args.enable_retry:
        print(f"Max retries: {args.max_retries}")
    failed_folder = 'failed_request_data'
    result_folder = 'result_data'
    os.makedirs(failed_folder, exist_ok=True)
    os.makedirs(result_folder, exist_ok=True)
    if args.retry_failed:
        print("=" * 60)
        print("RETRYING ALL FAILED REQUESTS IN failed_request_data/")
        print("=" * 60)
        all_failed = load_failed_requests_from_folder(failed_folder)
        if not all_failed:
            print("No failed requests found in folder.")
            return
        extractor = FPDSHighPerformanceExtractor(
            max_workers=args.workers,
            batch_size=args.batch_size,
            initial_delay=args.initial_delay
        )
        extractor.failed_requests = all_failed
        retried_contracts = extractor.retry_failed_requests(args.max_retries)
        if retried_contracts:
            retry_filename = os.path.join(failed_folder, f"failed_retry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(retry_filename, 'w', encoding='utf-8') as f:
                json.dump(retried_contracts, f, indent=2, ensure_ascii=False)
            print(f"Retried contracts saved to: {retry_filename}")
        else:
            print("No contracts were successfully retried.")
        return

    # Initialize extractor
    extractor = FPDSHighPerformanceExtractor(
        max_workers=args.workers,
        batch_size=args.batch_size,
        initial_delay=args.initial_delay
    )
    
    try:
        # Extract data
        contracts = extractor.extract_large_dataset(
            start_date=args.start_date,
            end_date=args.end_date,
            target_records=args.target_records,
            additional_filters=additional_filters
        )
        
        # Retry failed requests if enabled
        if args.enable_retry and extractor.failed_requests:
            print(f"\nRetrying {len(extractor.failed_requests)} failed requests...")
            retried_contracts = extractor.retry_failed_requests(args.max_retries)
            if retried_contracts:
                contracts.extend(retried_contracts)
                print(f"Successfully retried {len(retried_contracts)} contracts")
        
        # Save results
        if contracts:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{args.output}_{timestamp}.json"
            
            with open(os.path.join(result_folder, filename), 'w', encoding='utf-8') as f:
                json.dump(contracts, f, indent=2, ensure_ascii=False)
            
            print(f"\nResults saved to: {filename}")
        else:
            print("\nNo contracts found")
    
    except KeyboardInterrupt:
        print("\nExtraction interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
        
def parse_month_year(month_year_str: str) -> tuple:
    import calendar
    """Parse month/year format (e.g., '1/2026' or '1,2/2026') and return start/end dates for the range"""
    # Parse month/year format
    if '/' in month_year_str:
        month_part, year = month_year_str.split('/')
        year = int(year)
    else:
        raise ValueError("Invalid format. Use M/YYYY or M1,M2/YYYY (e.g., 1/2026 or 1,2/2026)")
    
    # Validate year
    if year < 1900 or year > 2100:
        raise ValueError("Year must be between 1900 and 2100")
    
    # Parse months (can be single month or comma-separated list)
    if ',' in month_part:
        # Multiple months: "1,2,3/2026"
        months = [int(m.strip()) for m in month_part.split(',')]
        # Sort months to ensure proper order
        months.sort()
    else:
        # Single month: "1/2026"
        months = [int(month_part)]
    
    # Validate all months
    for month in months:
        if month < 1 or month > 12:
            raise ValueError(f"Month {month} must be between 1 and 12")
    
    # Get first day of first month and last day of last month
    first_month = months[0]
    last_month = months[-1]
    
    first_day = datetime(year, first_month, 1)
    last_day = datetime(year, last_month, calendar.monthrange(year, last_month)[1])
    
    # Format as YYYY/MM/DD
    start_date = first_day.strftime('%Y/%m/%d')
    end_date = last_day.strftime('%Y/%m/%d')
    print(start_date)
    print(end_date)
    return start_date, end_date


if __name__ == "__main__":
    #parse_month_year("2/2026")
    main()