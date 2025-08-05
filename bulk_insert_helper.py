import json
import os
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from mongo_service import FPDSMongoDBService
from fpds_field_mappings import FPDSFieldMapper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FPDSBulkInsertHelper:
    """
    Helper class for bulk inserting FPDS data into MongoDB with proper data formatting
    """

    def __init__(self, mongo_service: FPDSMongoDBService, batch_size: int = 1000):
        self.mongo_service = mongo_service
        self.batch_size = batch_size
        self.field_mapper = FPDSFieldMapper()
        self.data_formatter = FPDSDataFormatter()

    def load_and_insert_from_directory(self, data_directory: str = "result_data") -> Dict[str, Any]:
        """
        Load JSON files from directory and insert into MongoDB
        """
        data_dir = Path(data_directory)
        if not data_dir.exists():
            raise FileNotFoundError(f"Directory {data_directory} not found")

        results = {
            "total_files": 0,
            "total_records": 0,
            "successful_inserts": 0,
            "failed_inserts": 0,
            "errors": []
        }

        # Find all JSON files in the directory
        json_files = list(data_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} JSON files in {data_directory}")

        for json_file in json_files:
            try:
                logger.info(f"Processing file: {json_file.name}")
                file_results = self._process_json_file(json_file)

                # Update overall results
                results["total_files"] += 1
                results["total_records"] += file_results["total_records"]
                results["successful_inserts"] += file_results["successful_inserts"]
                results["failed_inserts"] += file_results["failed_inserts"]
                results["errors"].extend(file_results["errors"])

            except Exception as e:
                error_msg = f"Error processing {json_file.name}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)

        logger.info(f"Bulk insert completed. Summary: {results}")
        return results

    def _process_json_file(self, json_file: Path) -> Dict[str, Any]:
        """
        Process a single JSON file and insert its data
        """
        results = {
            "total_records": 0,
            "successful_inserts": 0,
            "failed_inserts": 0,
            "errors": []
        }

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle different data structures
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict) and "contracts" in data:
                records = data["contracts"]
            elif isinstance(data, dict) and "results" in data:
                records = data["results"]
            else:
                # Assume it's a single record
                records = [data]

            results["total_records"] = len(records)
            logger.info(f"Found {len(records)} records in {json_file.name}")

            # Process records in batches
            for i in range(0, len(records), self.batch_size):
                batch = records[i:i + self.batch_size]
                batch_results = self._process_batch(batch)

                results["successful_inserts"] += batch_results["successful_inserts"]
                results["failed_inserts"] += batch_results["failed_inserts"]
                results["errors"].extend(batch_results["errors"])

                logger.info(
                    f"Processed batch {i // self.batch_size + 1}/{(len(records) + self.batch_size - 1) // self.batch_size}")

        except Exception as e:
            error_msg = f"Error reading {json_file.name}: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)

        return results

    def _process_batch(self, records: List[Dict]) -> Dict[str, Any]:
        """
        Process a batch of records
        """
        results = {
            "successful_inserts": 0,
            "failed_inserts": 0,
            "errors": []
        }

        formatted_records = []

        for record in records:
            try:
                # Extract detail_data if it exists
                if "detail_data" in record:
                    detail_data = record["detail_data"]
                else:
                    detail_data = record

                # Format the data
                formatted_data = self.data_formatter.format_contract_data(detail_data)
                formatted_records.append(formatted_data)

            except Exception as e:
                error_msg = f"Error formatting record: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["failed_inserts"] += 1

        # Insert formatted records
        if formatted_records:
            try:
                inserted_ids = self.mongo_service.store_bulk_contracts(formatted_records)
                results["successful_inserts"] = len(inserted_ids)
                logger.info(f"Successfully inserted {len(inserted_ids)} records")

            except Exception as e:
                error_msg = f"Error inserting batch: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["failed_inserts"] += len(formatted_records)

        return results


class FPDSDataFormatter:
    """
    Formats FPDS data with proper data types for MongoDB storage
    """

    def __init__(self):
        # Define patterns for different data types
        self.date_pattern = re.compile(r'^\d{2}/\d{2}/\d{4}$')
        self.money_pattern = re.compile(r'^\$[\d,]+\.\d{2}$')
        self.integer_pattern = re.compile(r'^\d+$')
        self.float_pattern = re.compile(r'^\d+\.\d+$')

        # Fields that should be integers
        self.integer_fields = {
            'award_id_modification_number',
            'award_id_transaction_number',
            'referenced_idv_id_idv_mod_number',
            'number_of_actions_number_of_actions',
            'idv_number_of_offers_idv_number_of_offers',
            'number_of_offers_received_number_of_offers_received',
            'unique_entity_id_entity_congressional_district'
        }

        # Fields that should be dates
        self.date_fields = {
            'date_signed_date_signed',
            'date_signed_period_of_performance_start_date',
            'date_signed_award_completion_date',
            'date_signed_estimated_ultimate_completion_date',
            'period_of_performance_start_date_period_of_performance_start_date',
            'completion_date_award_completion_date',
            'est_ultimate_completion_date_estimated_ultimate_completion_date'
        }

        # Fields that should be money (float)
        self.money_fields = {
            'date_signed_current_obligation_amount',
            'date_signed_total_obligation_amount',
            'date_signed_current_base_and_excercised_options_value',
            'date_signed_total_base_and_excercised_options_value',
            'date_signed_base_and_all_options_value',
            'date_signed_total_base_and_all_options_value',
            'date_signed_fee_paid_for_use_of_indefinite_delivery_vehicle',
            'action_obligation_current_obligation_amount',
            'action_obligation_total_obligation_amount',
            'base_and_exercised_options_value_current_base_and_excercised_options_value',
            'base_and_exercised_options_value_total_base_and_excercised_options_value',
            'base_and_all_options_value_total_contract_value_base_and_all_options_value',
            'base_and_all_options_value_total_contract_value_total_base_and_all_options_value',
            'fee_paid_for_use_of_idv_fee_paid_for_use_of_indefinite_delivery_vehicle'
        }

    def format_contract_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format contract data with proper data types
        """
        formatted_data = {}

        for key, value in data.items():
            if value is None or value == "":
                formatted_data[key] = None
                continue

            # Convert to string first for processing
            str_value = str(value).strip()

            # Determine the data type based on field name and value pattern
            formatted_value = self._format_value(key, str_value)
            formatted_data[key] = formatted_value

        return formatted_data

    def _format_value(self, field_name: str, value: str) -> Any:
        """
        Format a single value based on field name and content
        """
        # Handle integer fields
        if field_name in self.integer_fields:
            return self._parse_integer(value)

        # Handle date fields
        if field_name in self.date_fields:
            return self._parse_date(value)

        # Handle money fields
        if field_name in self.money_fields:
            return self._parse_money(value)

        # Handle patterns
        if self.date_pattern.match(value):
            return self._parse_date(value)

        if self.money_pattern.match(value):
            return self._parse_money(value)

        if self.integer_pattern.match(value):
            return self._parse_integer(value)

        if self.float_pattern.match(value):
            return self._parse_float(value)

        # Default to string
        return value

    def _parse_integer(self, value: str) -> Optional[int]:
        """
        Parse integer value
        """
        try:
            # Remove any non-digit characters except minus sign
            cleaned = re.sub(r'[^\d-]', '', value)
            if cleaned:
                return int(cleaned)
        except (ValueError, TypeError):
            pass
        return None

    def _parse_float(self, value: str) -> Optional[float]:
        """
        Parse float value
        """
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[^\d.-]', '', value)
            if cleaned:
                return float(cleaned)
        except (ValueError, TypeError):
            pass
        return None

    def _parse_money(self, value: str) -> Optional[float]:
        """
        Parse money value (remove $ and commas)
        """
        try:
            # Remove $ and commas
            cleaned = re.sub(r'[$,]', '', value)
            if cleaned:
                return float(cleaned)
        except (ValueError, TypeError):
            pass
        return None

    def _parse_date(self, value: str) -> Optional[datetime]:
        """
        Parse date value (MM/DD/YYYY format)
        """
        try:
            if self.date_pattern.match(value):
                return datetime.strptime(value, '%m/%d/%Y')
        except (ValueError, TypeError):
            pass
        return None


def main():
    """
    Main function to run bulk insert
    """
    import argparse

    parser = argparse.ArgumentParser(description="Bulk insert FPDS data into MongoDB")
    parser.add_argument("--data-dir", default="result_data", help="Directory containing JSON files")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch size for inserts")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017/", help="MongoDB connection string")
    parser.add_argument("--database", default="fpds", help="MongoDB database name")

    args = parser.parse_args()

    try:
        # Initialize MongoDB service
        mongo_service = FPDSMongoDBService(args.mongo_uri, args.database)

        # Initialize bulk insert helper
        helper = FPDSBulkInsertHelper(mongo_service, args.batch_size)

        # Process data
        results = helper.load_and_insert_from_directory(args.data_dir)

        # Print results
        print("\n" + "=" * 50)
        print("BULK INSERT RESULTS")
        print("=" * 50)
        print(f"Total files processed: {results['total_files']}")
        print(f"Total records found: {results['total_records']}")
        print(f"Successful inserts: {results['successful_inserts']}")
        print(f"Failed inserts: {results['failed_inserts']}")

        if results['errors']:
            print(f"\nErrors ({len(results['errors'])}):")
            for error in results['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(results['errors']) > 10:
                print(f"  ... and {len(results['errors']) - 10} more errors")

        print("=" * 50)

    except Exception as e:
        logger.error(f"Error in bulk insert: {e}")
        raise
    finally:
        if 'mongo_service' in locals():
            mongo_service.close()


if __name__ == "__main__":
    main()
