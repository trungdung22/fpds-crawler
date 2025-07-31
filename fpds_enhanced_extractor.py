import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
import csv
import logging
from typing import List, Dict, Optional, Tuple, Any
import time
import re
from datetime import datetime, timedelta
import urllib.parse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FPDSEnhancedExtractor:
    """
    Enhanced FPDS extractor that handles both search results and detail pages
    """
    
    def __init__(self, use_selenium=False):
        self.base_url = "https://www.fpds.gov/ezsearch/fpdsportal"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.use_selenium = use_selenium
        self.driver = None
        self.fetch_all = False

    def fetch_total_record(self, start_date, end_date, additional_filters):
        query = f"AWARD_COMPLETION_DATE:[{start_date},{end_date}]"
        if additional_filters:
            for key, value in additional_filters.items():
                query += f" {key}:\"{value}\""
        base_params = {
            'q': query,
            's': 'FPDS.GOV',
            'templateName': '1.5.3',
            'indexName': 'awardfull'
        }
        response = self.session.get(self.base_url, params=base_params, timeout=30)
        response.raise_for_status()
        return self._extract_pagination_info(response.text)

    def search_contracts_with_date_range(
        self, 
        start_date: str, 
        end_date: str, 
        additional_filters: Optional[Dict] = None,
        max_results: int = 100,
        max_pages: int = 10
    ) -> List[Dict]:
        """
        Search contracts with date range and extract both summary and detail data
        
        Args:
            start_date: Start date in YYYY/MM/DD format
            end_date: End date in YYYY/MM/DD format
            additional_filters: Additional search filters
            max_results: Maximum number of results to process
            max_pages: Maximum number of pages to process
            
        Returns:
            List of contract dictionaries with full details
        """
        
        # Build search query
        query = f"AWARD_COMPLETION_DATE:[{start_date},{end_date}]"
        
        if additional_filters:
            for key, value in additional_filters.items():
                query += f" {key}:\"{value}\""
        
        base_params = {
            'q': query,
            's': 'FPDS.GOV',
            'templateName': '1.5.3',
            'indexName': 'awardfull'
        }
        
        logger.info(f"Searching with query: {query}")
        
        all_contracts = []
        current_page = 1
        results_per_page = 30  # FPDS shows 30 results per page
        
        try:
            start_param = (current_page - 1) * results_per_page

            # Add pagination parameters
            params = base_params.copy()
            params['start'] = str(start_param)
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            total_results = self._extract_pagination_info(response.text)
            used_results = max_results
            if self.fetch_all:
                used_results = total_results

            while current_page <= max_pages and len(all_contracts) < used_results:
                logger.info(f"Processing page {current_page}...")
                
                # Calculate start parameter for pagination
                start_param = (current_page - 1) * results_per_page
                
                # Add pagination parameters
                params = base_params.copy()
                params['start'] = str(start_param)
                start_time = time.time()
                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                # Extract contracts from current page
                page_contracts = self._extract_contracts_from_search_page(response.text, max_results - len(all_contracts))
                logger.info(f"Processing index {current_page} took {time.time() - start_time}")
                if not page_contracts:
                    logger.info(f"No more contracts found on page {current_page}")
                    break
                
                # Extract detail data for each contract on this page
                detailed_page_contracts = []
                for i, contract in enumerate(page_contracts):
                    start_time = time.time()
                    logger.info(f"Processing contract {len(all_contracts) + i + 1}/{max_results}: {contract.get('award_id', 'Unknown')}")
                    # Get detail page data
                    detail_data = self._extract_contract_details(contract)
                    if detail_data:
                        contract['detail_data'] = detail_data
                    
                    detailed_page_contracts.append(contract)
                    logger.info(
                        f"Processing detail contract {len(all_contracts) + i + 1}/{max_results}"
                        f" took {time.time() - start_time}")
                    # Rate limiting
                    time.sleep(1)
                all_contracts.extend(detailed_page_contracts)
                logger.info(f"Retrieved {len(detailed_page_contracts)} contracts from page {current_page} (total: {len(all_contracts)})")
                
                # Check if we've reached the end
                if len(page_contracts) < results_per_page:
                    logger.info("Reached last page (fewer results than expected)")
                    break
                current_page += 1
                # Rate limiting between pages
                time.sleep(2)
            
            logger.info(f"Total contracts retrieved: {len(all_contracts)}")
            return all_contracts
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return all_contracts  # Return what we have so far
    
    def _extract_contracts_from_search_page(self, html_content: str, max_results: int) -> List[Dict]:
        """Extract contract data from search results page"""
        # Extract pagination informatio
        contracts = []
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Find all result tables
        result_tables = soup.find_all("table", class_=["resultbox1", "resultbox2"])
        for table in result_tables[:max_results]:
            contract = self._parse_contract_table(table)
            if contract:
                contracts.append(contract)
        
        return contracts

    @classmethod
    def _extract_pagination_info(cls, html_content: str) -> int:
        import math
        """Extract pagination info (start, end, total, current_page, total_pages)."""
        soup = BeautifulSoup(html_content, "html.parser")

        # 1) Try bold tags first
        #    <span>…Results <b>1</b> - <b>30</b> of <b>16366</b>…</span>
        span = soup.find("span", {"class": "results_heading"})
        heading_span = soup.find(
            "span",
            {"class": "results_heading"},
            string=lambda txt: txt and "List Of Contract Actions Matching Your Criteria" in txt
        )

        row = heading_span.find_parent("tr")

        cells = row.find_all("td")
        results_td = cells[1]

        # 4) Inside that <td>, find all <b> tags; the third <b> holds the total
        b_tags = results_td.find_all("b")
        total_results = int(b_tags[2].get_text())

        print(total_results)
        return total_results
    
    def _parse_contract_table(self, table) -> Optional[Dict]:
        """Parse a single contract result table"""
        
        contract = {}

        def _extract_row_data(row_header, row_value):
            field_name = row_header.get_text(strip=True).replace(":", "")
            field_value = row_value.get_text(strip=True)

            # Clean field name
            field_name = self._clean_field_name(field_name)

            # Extract links if present
            links = cells[1].find_all("a")
            if links:
                contract[f"{field_name}_links"] = []
                for link in links:
                    link_data = {
                        'text': link.get_text(strip=True),
                        'href': link.get('href', ''),
                        'title': link.get('title', '')
                    }
                    contract[f"{field_name}_links"].append(link_data)

            # Store the main value
            contract[field_name] = field_value

        try:
            # Extract all rows
            rows = table.find_all("tr")
            
            for row in rows:
                cells = row.find_all("td")
                # Get field name and value
                if len(cells) == 2:
                    _extract_row_data(cells[0], cells[1])
                else:
                    _extract_row_data(cells[0], cells[1])
                    _extract_row_data(cells[2], cells[3])

            # Extract view link for detail page
            view_link = table.find("a", {"title": "View"})
            if view_link:
                href = view_link.get('href', '')
                # Extract parameters from JavaScript function
                contract['view_link_params'] = self._extract_view_link_params(href)
            
            return contract
            
        except Exception as e:
            logger.error(f"Error parsing contract table: {e}")
            return None
    
    def _extract_view_link_params(self, href: str) -> Dict:
        """Extract parameters from view link JavaScript function"""
        
        params = {}
        
        try:
            # Extract URL parameters from JavaScript function
            match = re.search(r"viewLinkController\.jsp\?([^']+)", href)
            if match:
                param_string = match.group(1)
                # Parse parameters
                for param in param_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key] = urllib.parse.unquote(value)
            
        except Exception as e:
            logger.error(f"Error extracting view link params: {e}")
        
        return params
    
    def _extract_contract_details(self, contract: Dict) -> Optional[Dict]:
        """Extract detailed contract information from the detail page"""
        
        if not contract.get('view_link_params'):
            return None
        
        try:
            # Build detail page URL
            detail_url = "https://www.fpds.gov/ezsearch/jsp/viewLinkController.jsp"
            params = contract['view_link_params']
            
            return self._extract_details_with_requests(detail_url, params)
                
        except Exception as e:
            logger.error(f"Error extracting contract details: {e}")
            return None

    def _extract_details_with_requests(self, detail_url: str, params: Dict) -> Optional[Dict]:
        """Extract all the form‐style data, selects, lists, nested tables, and multi-column amount rows as key → value."""
        try:
            resp = self.session.get(detail_url, params=params, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            details: Dict[str, Any] = {}

            # --- Special handling for the multi-column “amounts” section ---
            for table in soup.find_all("table"):
                header = table.find("tr", id="modAmounts")
                if not header:
                    continue

                # Column names: Previous, Current, Total
                cols = [td.get_text(strip=True) for td in header.find_all("td")[1:4]]

                # Walk subsequent rows until the separator
                for row in header.find_next_siblings("tr"):
                    if row.get("id") == "amountSectionSeparator":
                        break

                    cells = row.find_all("td", recursive=False)
                    if len(cells) < 1 + len(cols):
                        continue

                    # The first cell is the field label
                    label = cells[0].get_text(" ", strip=True).rstrip(":")

                    # Build a sub-dict of each column’s value
                    amt_data: Dict[str, str] = {}
                    for idx, col_name in enumerate(cols, start=1):
                        cell = cells[idx]
                        inp = cell.find("input")
                        if inp and inp.has_attr("value"):
                            amt_data[col_name] = inp["value"].strip()
                        else:
                            amt_data[col_name] = cell.get_text(" ", strip=True)
                    details[label] = amt_data

            # --- Generic row-by-row parsing for all other tables ---
            for table in soup.find_all("table"):
                for row in table.find_all("tr"):
                    cells = row.find_all("td", recursive=False)
                    if len(cells) < 2:
                        continue

                    label = cells[0].get_text(" ", strip=True).rstrip(":")
                    # Skip any row we've already parsed in the amounts section
                    if label in details:
                        continue

                    value_cell = cells[1]

                    # TYPE 1: simple <input> fields
                    inp = value_cell.find("input", {"type": ["text", "hidden"]})
                    if inp and inp.has_attr("value"):
                        details[label] = inp["value"]
                        continue

                    # TYPE 2: <select> pick the selected <option>
                    sel = value_cell.find("select")
                    if sel:
                        opt = sel.find("option", selected=True)
                        if opt is None:
                            opt = sel.find("option", value=lambda v: v and v.strip())
                        details[label] = opt.get_text(strip=True) if opt else None
                        continue

                    # TYPE 3: bullet lists inside a cell (<li> tags)
                    lis = value_cell.find_all("li")
                    if lis:
                        details[label] = [li.get_text(" ", strip=True) for li in lis]
                        continue

                    # NESTED TABLES: collect text inputs into a sub-dict
                    nested_inps = value_cell.find_all("input", {"type": "text"})
                    if nested_inps:
                        sub: Dict[str, str] = {}
                        for ni in nested_inps:
                            sub_label = ni.get("title") or ni.get("name")
                            sub_value = ni.get("value", "")
                            sub[sub_label] = sub_value
                        details[label] = sub
                        continue

                    # FALLBACK: plain text, monetary values, or dates
                    txt = value_cell.get_text(" ", strip=True)
                    if txt:
                        if "$" in txt:
                            details.setdefault("monetary_values", []).append(txt)
                        elif re.match(r"\d{1,2}/\d{1,2}/\d{4}", txt):
                            details.setdefault("dates", []).append(txt)
                        else:
                            details[label] = txt
            if "" in details:
                del details[""]
            return details

        except Exception as e:
            logger.error(f"Error with requests extraction: {e}", exc_info=True)
            return None

    
    def _clean_field_name(self, field_name: str) -> str:
        """Clean field name for use as dictionary key"""
        
        # Remove special characters and spaces
        cleaned = re.sub(r'[^\w\s]', '', field_name)
        cleaned = re.sub(r'\s+', '_', cleaned.strip())
        return cleaned.lower() or "field"
    
    def save_to_json(self, contracts: List[Dict], filename: str):
        """Save contracts to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(contracts, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(contracts)} contracts to {filename}")
    
    def save_to_csv(self, contracts: List[Dict], filename: str):
        """Save contracts to CSV file"""
        if not contracts:
            logger.warning("No contracts to save")
            return
        
        # Get all unique keys from all contracts
        all_keys = set()
        for contract in contracts:
            all_keys.update(contract.keys())
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()
            writer.writerows(contracts)
        
        logger.info(f"Saved {len(contracts)} contracts to {filename}")
    
    def save_to_xml(self, contracts: List[Dict], filename: str):
        """Save contracts to XML file"""
        root = ET.Element("fpds_contracts")
        root.set("extraction_timestamp", datetime.now().isoformat())
        root.set("total_contracts", str(len(contracts)))
        
        for i, contract in enumerate(contracts):
            contract_elem = ET.SubElement(root, "contract")
            contract_elem.set("id", str(i + 1))
            
            for key, value in contract.items():
                if isinstance(value, list):
                    # Handle lists
                    list_elem = ET.SubElement(contract_elem, key)
                    for item in value:
                        if isinstance(item, dict):
                            item_elem = ET.SubElement(list_elem, "item")
                            for k, v in item.items():
                                sub_elem = ET.SubElement(item_elem, k)
                                sub_elem.text = str(v)
                        else:
                            item_elem = ET.SubElement(list_elem, "item")
                            item_elem.text = str(item)
                elif isinstance(value, dict):
                    # Handle nested dictionaries
                    dict_elem = ET.SubElement(contract_elem, key)
                    for k, v in value.items():
                        sub_elem = ET.SubElement(dict_elem, k)
                        sub_elem.text = str(v)
                else:
                    field_elem = ET.SubElement(contract_elem, key)
                    field_elem.text = str(value) if value is not None else ""
        
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)
        logger.info(f"Saved {len(contracts)} contracts to {filename}")

    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()


# Example usage
if __name__ == "__main__":
    # Example 1: Using requests (faster, but may miss dynamic content)
    print("Testing with requests method...")
    extractor = FPDSEnhancedExtractor(use_selenium=False)
    
    contracts = extractor.search_contracts_with_date_range(
        start_date="2025/07/29",
        end_date="2025/07/30",
        max_results=5,
        max_pages=1
    )
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extractor.save_to_json(contracts, f"fpds_contracts_requests_{timestamp}.json")
    
