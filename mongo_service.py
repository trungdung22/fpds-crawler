import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from fpds_field_mappings import FPDSFieldMapper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FPDSMongoDBService:
    """
    MongoDB service for storing and querying FPDS data
    """
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", database_name: str = "fpds"):
        self.client = MongoClient(connection_string)
        self.db: Database = self.client[database_name]
        self.collection: Collection = self.db.contracts
        self.mapper = FPDSFieldMapper()
        # Create indexes for better performance
        self._create_indexes()
    
    def _create_indexes(self):
        """
        Create indexes for commonly queried fields
        """
        try:
            # Agency indexes
            self.collection.create_index("contracting_office_agency_id_contracting_office_agency_name")
            self.collection.create_index("funding_agency_id_funding_or_requesting_agency_name")
            
            # Date indexes
            self.collection.create_index("date_signed_date_signed")
            self.collection.create_index("date_signed_award_completion_date")
            self.collection.create_index("date_signed_estimated_ultimate_completion_date")
            
            # Financial indexes
            self.collection.create_index("action_obligation_total_obligation_amount")
            self.collection.create_index("base_and_exercised_options_value_total_base_and_excercised_options_value")
            
            # Entity indexes
            self.collection.create_index("unique_entity_id_legal_business_name")
            self.collection.create_index("unique_entity_id_entity_state")
            self.collection.create_index("unique_entity_id_entity_city")
            
            # Performance location indexes
            self.collection.create_index("principal_place_of_performance_code_principal_place_of_performance_state_code")
            self.collection.create_index("principal_place_of_performance_city_name_principal_place_of_performance_city_name")
            
            # Contract type indexes
            self.collection.create_index("type_of_contract")
            self.collection.create_index("award_type_display")
            self.collection.create_index("type_of_set_aside")
            
            # Text index for full-text search
            self.collection.create_index([
                ("contracting_office_agency_id_contracting_office_agency_name", "text"),
                ("unique_entity_id_legal_business_name", "text"),
                ("productservice_code_product_or_service_code_description", "text"),
                ("nature_of_services", "text")
            ])
            
            logger.info("Indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def store_contract_data(self, contract_data: Dict[str, Any]) -> str:
        """
        Store a single contract in MongoDB
        """
        try:
            # Add metadata
            contract_data["_created_at"] = datetime.now()
            contract_data["_updated_at"] = datetime.now()
            
            # Insert the document
            result = self.collection.insert_one(contract_data)
            logger.info(f"Stored contract with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Error storing contract data: {e}")
            raise
    
    def store_bulk_contracts(self, contracts: List[Dict[str, Any]]) -> List[str]:
        """
        Store multiple contracts in bulk
        """
        try:
            # Add metadata to all contracts
            current_time = datetime.now()
            for contract in contracts:
                contract["_created_at"] = current_time
                contract["_updated_at"] = current_time
            
            # Insert documents
            result = self.collection.insert_many(contracts)
            logger.info(f"Stored {len(result.inserted_ids)} contracts")
            return [str(id) for id in result.inserted_ids]
            
        except Exception as e:
            logger.error(f"Error storing bulk contracts: {e}")
            raise
  
    def close(self):
        """
        Close the MongoDB connection
        """
        self.client.close()
        logger.info("MongoDB connection closed")


# Example usage
if __name__ == "__main__":
    # Initialize the service
    service = FPDSMongoDBService()
    
    try:
        # Load sample data
        with open("data/detail.json", "r") as f:
            sample_data = json.load(f)
        
        # Store the sample contract
        contract_id = service.store_contract_data(sample_data)
        print(f"Stored contract with ID: {contract_id}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        service.close() 