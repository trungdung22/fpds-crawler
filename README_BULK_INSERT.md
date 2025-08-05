# FPDS Bulk Insert Helper

This module provides efficient bulk insertion of FPDS (Federal Procurement Data System) data into MongoDB with proper data type formatting and comprehensive field mappings for LLM-powered search.

## Features

- **Efficient Bulk Insertion**: Processes large datasets (2M+ records) with configurable batch sizes
- **Data Type Formatting**: Automatically converts strings to appropriate data types (dates, floats, integers)
- **Comprehensive Field Mappings**: Enhanced mappings for LLM-powered natural language search
- **Error Handling**: Robust error handling with detailed reporting
- **Flexible Data Sources**: Supports various JSON file structures

## Components

### 1. FPDSBulkInsertHelper
Main class for bulk inserting FPDS data into MongoDB.

### 2. FPDSDataFormatter
Handles data type conversion and formatting for MongoDB storage.

### 3. Enhanced FPDSFieldMapper
Provides comprehensive field mappings for LLM search capabilities.

## Installation

Ensure you have the required dependencies:

```bash
pip install pymongo
```

## Usage

### Basic Usage

```python
from mongo_service import FPDSMongoDBService
from bulk_insert_helper import FPDSBulkInsertHelper

# Initialize MongoDB service
mongo_service = FPDSMongoDBService("mongodb://localhost:27017/", "fpds")

# Initialize bulk insert helper
helper = FPDSBulkInsertHelper(mongo_service, batch_size=1000)

# Process data from result_data directory
results = helper.load_and_insert_from_directory("result_data")

print(f"Inserted {results['successful_inserts']} records")
```

### Command Line Usage

```bash
# Basic usage with default settings
python bulk_insert_helper.py

# Custom settings
python bulk_insert_helper.py \
    --data-dir result_data \
    --batch-size 2000 \
    --mongo-uri mongodb://localhost:27017/ \
    --database fpds
```

### Data Formatting

The system automatically formats data types:

- **Dates**: `"04/05/2023"` → `datetime(2023, 4, 5)`
- **Money**: `"$1,520,240.48"` → `1520240.48`
- **Integers**: `"9"` → `9`
- **Strings**: `"DEPT OF THE NAVY"` → `"DEPT OF THE NAVY"`

### Supported Data Structures

The helper supports various JSON file structures:

```json
// Array of records
[
  {"detail_data": {...}},
  {"detail_data": {...}}
]

// Object with contracts array
{
  "contracts": [
    {"detail_data": {...}},
    {"detail_data": {...}}
  ]
}

// Object with results array
{
  "results": [
    {"detail_data": {...}},
    {"detail_data": {...}}
  ]
}

// Single record
{"detail_data": {...}}
```

## Field Mappings for LLM Search

The enhanced field mappings support natural language queries for LLM-powered search:

### Example Queries

```python
from fpds_field_mappings import FPDSFieldMapper

mapper = FPDSFieldMapper()

# Find matching fields for natural language queries
matches = mapper.find_matching_fields("NASA contracts expiring soon")
matches = mapper.find_matching_fields("large contracts over $1 million")
matches = mapper.find_matching_fields("small business contracts in California")
```

### Supported Query Categories

#### Agency Queries
- "NASA contracts"
- "Navy contracts"
- "Department of Defense contracts"
- "EPA contracts"

#### Financial Queries
- "contracts over $1 million"
- "high value contracts"
- "small contracts under $100k"
- "total obligation amount"

#### Business Type Queries
- "small business contracts"
- "8a contracts"
- "women owned business contracts"
- "veteran owned contracts"

#### Contract Type Queries
- "fixed price contracts"
- "cost plus contracts"
- "delivery orders"
- "task orders"

#### Location Queries
- "contracts in California"
- "domestic contracts"
- "foreign contracts"
- "contracts in Washington DC"

#### Service Type Queries
- "construction contracts"
- "software development contracts"
- "consulting contracts"
- "research contracts"

#### Status Queries
- "active contracts"
- "expiring contracts"
- "completed contracts"
- "emergency contracts"

## Data Type Mapping

### Integer Fields
- `award_id_modification_number`
- `award_id_transaction_number`
- `number_of_actions_number_of_actions`
- `idv_number_of_offers_idv_number_of_offers`
- `number_of_offers_received_number_of_offers_received`

### Date Fields
- `date_signed_date_signed`
- `date_signed_period_of_performance_start_date`
- `date_signed_award_completion_date`
- `date_signed_estimated_ultimate_completion_date`
- `period_of_performance_start_date_period_of_performance_start_date`
- `completion_date_award_completion_date`
- `est_ultimate_completion_date_estimated_ultimate_completion_date`

### Money Fields (Float)
- `date_signed_current_obligation_amount`
- `date_signed_total_obligation_amount`
- `date_signed_current_base_and_excercised_options_value`
- `date_signed_total_base_and_excercised_options_value`
- `date_signed_base_and_all_options_value`
- `date_signed_total_base_and_all_options_value`
- `action_obligation_current_obligation_amount`
- `action_obligation_total_obligation_amount`
- `base_and_exercised_options_value_current_base_and_excercised_options_value`
- `base_and_exercised_options_value_total_base_and_excercised_options_value`
- `base_and_all_options_value_total_contract_value_base_and_all_options_value`
- `base_and_all_options_value_total_contract_value_total_base_and_all_options_value`
- `fee_paid_for_use_of_idv_fee_paid_for_use_of_indefinite_delivery_vehicle`

## Performance Optimization

### Batch Size Recommendations

- **Small datasets (< 10K records)**: 500-1000
- **Medium datasets (10K-100K records)**: 1000-2000
- **Large datasets (100K-1M records)**: 2000-5000
- **Very large datasets (> 1M records)**: 5000-10000

### MongoDB Indexes

The system automatically creates indexes for commonly queried fields:

- Agency indexes
- Date indexes
- Financial indexes
- Entity indexes
- Performance location indexes
- Contract type indexes
- Text indexes for full-text search

## Error Handling

The system provides detailed error reporting:

```python
results = helper.load_and_insert_from_directory("result_data")

if results['errors']:
    print(f"Errors encountered: {len(results['errors'])}")
    for error in results['errors']:
        print(f"  - {error}")
```

## Testing

Run the test suite to verify functionality:

```bash
python test_bulk_insert.py
```

This will test:
- Data formatting
- Field mappings
- Bulk insert functionality (requires MongoDB)

## Example Output

```
FPDS Bulk Insert Test Suite
==================================================

==================================================
TESTING DATA FORMATTER
==================================================
Original data:
  award_id_agency_id: 9700 (str)
  date_signed_date_signed: 04/05/2023 (str)
  date_signed_total_obligation_amount: $1,520,240.48 (str)
  number_of_actions_number_of_actions: 1 (str)
  unique_entity_id_legal_business_name: RENOVA-SOVEREIGN JOINT VENTURE (str)

Formatted data:
  award_id_agency_id: 9700 (str)
  date_signed_date_signed: 2023-04-05 00:00:00 (datetime)
  date_signed_total_obligation_amount: 1520240.48 (float)
  number_of_actions_number_of_actions: 1 (int)
  unique_entity_id_legal_business_name: RENOVA-SOVEREIGN JOINT VENTURE (str)

==================================================
TESTING FIELD MAPPINGS
==================================================

Query: 'NASA contracts expiring soon'
  Top matches:
    - contracting_office_agency_id_contracting_office_agency_name: Contracting office agency name (score: 15)
    - date_signed_award_completion_date: Award completion date (score: 10)
  Expanded terms: ['national aeronautics and space administration', 'nasa', 'expiring', 'ending', 'completion', 'award completion date', 'contract end', 'termination']

==================================================
TESTING BULK INSERT
==================================================
Created sample data file: result_data/sample_test_data.json
Found 1 JSON files in result_data
Processing file: sample_test_data.json
Found 2 records in sample_test_data.json
Processed batch 1/1
Successfully inserted 2 records
Total files processed: 1
Total records found: 2
Successful inserts: 2
Failed inserts: 0

Cleaned up sample file: result_data/sample_test_data.json

==================================================
TEST SUITE COMPLETED
==================================================
```

## Configuration

### Environment Variables

```bash
export MONGODB_URI="mongodb://localhost:27017/"
export MONGODB_DATABASE="fpds"
export BATCH_SIZE="1000"
```

### Configuration File

Create a `config.json` file:

```json
{
  "mongodb": {
    "uri": "mongodb://localhost:27017/",
    "database": "fpds"
  },
  "bulk_insert": {
    "batch_size": 1000,
    "data_directory": "result_data"
  }
}
```

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Ensure MongoDB is running
   - Check connection string
   - Verify network connectivity

2. **Memory Issues with Large Datasets**
   - Reduce batch size
   - Process files individually
   - Increase system memory

3. **Data Type Conversion Errors**
   - Check data format in source files
   - Review field mappings
   - Handle missing or malformed data

### Performance Tips

1. **Use appropriate batch sizes** for your dataset size
2. **Monitor memory usage** during large imports
3. **Use indexes** for better query performance
4. **Process during off-peak hours** for production systems

## API Reference

### FPDSBulkInsertHelper

```python
class FPDSBulkInsertHelper:
    def __init__(self, mongo_service: FPDSMongoDBService, batch_size: int = 1000)
    def load_and_insert_from_directory(self, data_directory: str = "result_data") -> Dict[str, Any]
```

### FPDSDataFormatter

```python
class FPDSDataFormatter:
    def __init__(self)
    def format_contract_data(self, data: Dict[str, Any]) -> Dict[str, Any]
```

### FPDSFieldMapper

```python
class FPDSFieldMapper:
    def __init__(self)
    def find_matching_fields(self, query: str) -> List[Dict]
    def expand_search_terms(self, query: str) -> List[str]
    def build_mongodb_query(self, natural_query: str) -> Dict
```

## License

This project is part of the FPDS Crawler system. 