import json
from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime

class FPDSFieldMapper:
    """
    Maps natural language queries to FPDS database fields for LLM-powered search
    """
    
    def __init__(self):
        self.field_mappings = self._create_field_mappings()
        self.search_aliases = self._create_search_aliases()
        
    def _create_field_mappings(self) -> Dict[str, Dict]:
        """
        Create comprehensive field mappings with descriptions, categories, and search terms
        """
        return {
            # Transaction Information
            "award_type_display": {
                "description": "Type of award (e.g., Delivery/Task Order, Purchase Order)",
                "category": "transaction",
                "search_terms": ["award type", "contract type", "delivery order", "task order", "purchase order", "contract award"],
                "data_type": "string"
            },
            "award_status_display": {
                "description": "Current status of the award (e.g., Final, Draft)",
                "category": "transaction", 
                "search_terms": ["award status", "contract status", "final", "draft", "active"],
                "data_type": "string"
            },
            "closed_status_display": {
                "description": "Whether the contract is closed",
                "category": "transaction",
                "search_terms": ["closed", "closed status", "contract closed", "terminated"],
                "data_type": "string"
            },

            "prepared_date": {
                "description": "Date and time when the award record was prepared",
                "category": "transaction",
                "search_terms": ["prepared date", "date prepared", "award prepared", "prepared on"],
                "data_type": "datetime"
            },
            "prepared_user": {
                "description": "User who prepared the award record",
                "category": "transaction",
                "search_terms": ["prepared user", "prepared by", "award prepared by", "record creator"],
                "data_type": "string"
            },
            "last_modified_date": {
                "description": "Date and time when the award record was last modified",
                "category": "transaction",
                "search_terms": ["last modified date", "modified date", "updated date", "last updated"],
                "data_type": "datetime"
            },
            "last_modified_user": {
                "description": "User who last modified the award record",
                "category": "transaction",
                "search_terms": ["last modified user", "modified by", "updated by", "last updated by"],
                "data_type": "string"
            },
            "approved_date": {
                "description": "Date and time when the award was approved",
                "category": "transaction",
                "search_terms": ["approved date", "date approved", "award approved"],
                "data_type": "datetime"
            },
            "approved_by_display": {
                "description": "User who approved the award",
                "category": "transaction",
                "search_terms": ["approved by", "approver", "award approver"],
                "data_type": "string"
            },
            # Award ID Information
            "award_id_agency_id": {
                "description": "Agency ID for the award",
                "category": "award_id",
                "search_terms": ["agency id", "award agency", "contracting agency"],
                "data_type": "string"
            },
            "award_id_procurement_identifier": {
                "description": "Procurement identifier (PIID)",
                "category": "award_id",
                "search_terms": ["procurement id", "piid", "contract number", "award number"],
                "data_type": "string"
            },
            "award_id_modification_number": {
                "description": "Modification number for the award",
                "category": "award_id",
                "search_terms": ["modification", "mod number", "contract modification"],
                "data_type": "string"
            },
            "award_id_transaction_number": {
                "description": "Transaction number",
                "category": "award_id",
                "search_terms": ["transaction number", "transaction id"],
                "data_type": "string"
            },
            "solicitation_id_solicitation_id": {
                "description": "Solicitation ID for the award",
                "category": "award_id",
                "search_terms": ["solicitation id", "solicitation", "bid id", "request for proposal"],
                "data_type": "string"
            },
            
            # Referenced IDV Information
            "referenced_idv_id_indefinite_delivery_vehicle_agency_id": {
                "description": "Agency ID for the referenced IDV",
                "category": "idv",
                "search_terms": ["idv agency", "indefinite delivery vehicle agency"],
                "data_type": "string"
            },
            "referenced_idv_id_indefinite_delivery_vehicle_procurement_id": {
                "description": "Procurement ID for the referenced IDV",
                "category": "idv",
                "search_terms": ["idv procurement", "indefinite delivery vehicle procurement"],
                "data_type": "string"
            },
            "referenced_idv_id_idv_mod_number": {
                "description": "Modification number for the IDV",
                "category": "idv",
                "search_terms": ["idv modification", "idv mod"],
                "data_type": "string"
            },
            
            # Dates
            "date_signed_date_signed": {
                "description": "Date when the contract was signed",
                "category": "dates",
                "search_terms": ["date signed", "signature date", "contract date", "award date"],
                "data_type": "date"
            },
            "date_signed_period_of_performance_start_date": {
                "description": "Start date of the performance period",
                "category": "dates",
                "search_terms": ["performance start", "start date", "period start", "contract start"],
                "data_type": "date"
            },
            "date_signed_award_completion_date": {
                "description": "Award completion date",
                "category": "dates",
                "search_terms": ["completion date", "award completion", "contract completion", "end date"],
                "data_type": "date"
            },
            "date_signed_estimated_ultimate_completion_date": {
                "description": "Estimated ultimate completion date",
                "category": "dates",
                "search_terms": ["estimated completion", "ultimate completion", "expected end"],
                "data_type": "date"
            },
            # Financial Information
            "action_obligation_current_obligation_amount": {
                "description": "Current obligation amount",
                "category": "financial",
                "search_terms": ["current obligation", "obligation amount", "current amount", "funds obligated"],
                "data_type": "currency"
            },
            "action_obligation_total_obligation_amount": {
                "description": "Total obligation amount",
                "category": "financial",
                "search_terms": ["total obligation", "total amount", "total funds", "total obligated"],
                "data_type": "currency"
            },
            "base_and_exercised_options_value_current_base_and_excercised_options_value": {
                "description": "Current base and exercised options value",
                "category": "financial",
                "search_terms": ["base value", "exercised options", "current value"],
                "data_type": "currency"
            },
            "base_and_exercised_options_value_total_base_and_excercised_options_value": {
                "description": "Total base and exercised options value",
                "category": "financial",
                "search_terms": ["total base", "total options", "total contract value"],
                "data_type": "currency"
            },
            
            # Contracting Office Information
            "contracting_office_agency_id_contracting_office_agency_id": {
                "description": "Contracting office agency ID",
                "category": "contracting_office",
                "search_terms": ["contracting office agency", "contracting agency id"],
                "data_type": "string"
            },
            "contracting_office_agency_id_contracting_office_agency_name": {
                "description": "Contracting office agency name",
                "category": "contracting_office",
                "search_terms": ["contracting office", "contracting agency", "awarding agency"],
                "data_type": "string"
            },
            "contracting_office_id_contracting_office_id": {
                "description": "Contracting office ID",
                "category": "contracting_office",
                "search_terms": ["contracting office id", "office id"],
                "data_type": "string"
            },
            "contracting_office_id_contracting_office_name": {
                "description": "Contracting office name",
                "category": "contracting_office",
                "search_terms": ["contracting office name", "office name"],
                "data_type": "string"
            },
            
            # Funding Information
            "funding_agency_id_funding_or_requesting_agency_id": {
                "description": "Funding agency ID",
                "category": "funding",
                "search_terms": ["funding agency", "funding agency id", "requesting agency"],
                "data_type": "string"
            },
            "funding_agency_id_funding_or_requesting_agency_name": {
                "description": "Funding agency name",
                "category": "funding",
                "search_terms": ["funding agency name", "requesting agency name"],
                "data_type": "string"
            },
            "funding_office_id_funding_or_requesting_office_id": {
                "description": "Funding office ID",
                "category": "funding",
                "search_terms": ["funding office", "funding office id"],
                "data_type": "string"
            },
            "funding_office_id_funding_or_requesting_office_name": {
                "description": "Funding office name",
                "category": "funding",
                "search_terms": ["funding office name"],
                "data_type": "string"
            },
            
            # Entity Information
            "unique_entity_id_unique_entity_identifier": {
                "description": "Unique entity identifier (UEI)",
                "category": "entity",
                "search_terms": ["unique entity id", "uei", "entity identifier", "vendor id"],
                "data_type": "string"
            },
            "unique_entity_id_legal_business_name": {
                "description": "Legal business name of the contractor",
                "category": "entity",
                "search_terms": ["business name", "contractor name", "vendor name", "company name"],
                "data_type": "string"
            },
            "unique_entity_id_cage_code": {
                "description": "CAGE code of the contractor",
                "category": "entity",
                "search_terms": ["cage code", "cage"],
                "data_type": "string"
            },
            "unique_entity_id_entity_city": {
                "description": "City of the contractor",
                "category": "entity",
                "search_terms": ["contractor city", "vendor city", "business city"],
                "data_type": "string"
            },
            "unique_entity_id_entity_state": {
                "description": "State of the contractor",
                "category": "entity",
                "search_terms": ["contractor state", "vendor state", "business state"],
                "data_type": "string"
            },
            "unique_entity_id_entity_zip": {
                "description": "ZIP code of the contractor",
                "category": "entity",
                "search_terms": ["contractor zip", "vendor zip", "business zip"],
                "data_type": "string"
            },
            "unique_entity_id_entity_country": {
                "description": "Country of the contractor",
                "category": "entity",
                "search_terms": ["contractor country", "vendor country", "business country"],
                "data_type": "string"
            },
            
            # Contract Information
            "type_of_contract": {
                "description": "Type of contract (e.g., Firm Fixed Price)",
                "category": "contract",
                "search_terms": ["contract type", "type of contract", "fixed price", "cost plus"],
                "data_type": "string"
            },
            "nature_of_services": {
                "description": "Nature of services provided",
                "category": "contract",
                "search_terms": ["nature of services", "service type", "work type"],
                "data_type": "string"
            },
            "multiyear_contract": {
                "description": "Whether this is a multiyear contract",
                "category": "contract",
                "search_terms": ["multiyear", "multi year", "multi-year"],
                "data_type": "string"
            },
            
            # Place of Performance
            "principal_place_of_performance_code_principal_place_of_performance_state_code": {
                "description": "State code for principal place of performance",
                "category": "performance_location",
                "search_terms": ["performance state", "work state", "location state"],
                "data_type": "string"
            },
            "principal_place_of_performance_code_principal_place_of_performance_country_code": {
                "description": "Country code for principal place of performance",
                "category": "performance_location",
                "search_terms": ["performance country", "work country", "location country"],
                "data_type": "string"
            },
            "principal_place_of_performance_county_name_principal_place_of_performance_county_name": {
                "description": "County name for principal place of performance",
                "category": "performance_location",
                "search_terms": ["performance county", "work county", "location county"],
                "data_type": "string"
            },
            "principal_place_of_performance_city_name_principal_place_of_performance_city_name": {
                "description": "City name for principal place of performance",
                "category": "performance_location",
                "search_terms": ["performance city", "work city", "location city"],
                "data_type": "string"
            },
            
            # Product/Service Information
            "productservice_code_product_or_service_code": {
                "description": "Product or service code",
                "category": "product_service",
                "search_terms": ["product code", "service code", "psc", "product service code"],
                "data_type": "string"
            },
            "productservice_code_product_or_service_code_description": {
                "description": "Description of the product or service code",
                "category": "product_service",
                "search_terms": ["product description", "service description", "work description"],
                "data_type": "string"
            },
            "principal_naics_code_principal_north_american_industry_classification_system_code": {
                "description": "Principal NAICS code",
                "category": "product_service",
                "search_terms": ["naics code", "naics", "industry code"],
                "data_type": "string"
            },
            "principal_naics_code_north_american_industry_classification_system_description": {
                "description": "NAICS code description",
                "category": "product_service",
                "search_terms": ["naics description", "industry description"],
                "data_type": "string"
            },
            "description_of_requirement": {
                "description": "Detailed description of the requirement (e.g., period of performance extension TI 003)",
                "category": "product_service",
                "search_terms": ["requirement description", "description of requirement", "period of performance",
                                 "performance extension"],
                "data_type": "string"
            },
            # Competition Information
            "extent_competed": {
                "description": "Extent of competition",
                "category": "competition",
                "search_terms": ["extent competed", "competition", "competitive", "full and open"],
                "data_type": "string"
            },
            "type_of_set_aside": {
                "description": "Type of set aside",
                "category": "competition",
                "search_terms": ["set aside", "small business", "8a", "women owned"],
                "data_type": "string"
            },
            "number_of_offers_received_number_of_offers_received": {
                "description": "Number of offers received",
                "category": "competition",
                "search_terms": ["number of offers", "offers received", "bids received"],
                "data_type": "number"
            },
            
            # Business Size
            "contracting_officers_business_size_selection": {
                "description": "Business size selection by contracting officer",
                "category": "business_size",
                "search_terms": ["business size", "small business", "large business"],
                "data_type": "string"
            },
            
            # Additional Financial Fields
            "date_signed_current_obligation_amount": {
                "description": "Current obligation amount as of date signed",
                "category": "financial",
                "search_terms": ["current obligation", "current amount", "obligated funds", "current funding"],
                "data_type": "currency"
            },
            "date_signed_total_obligation_amount": {
                "description": "Total obligation amount as of date signed",
                "category": "financial",
                "search_terms": ["total obligation", "total amount", "total funding", "total obligated"],
                "data_type": "currency"
            },
            "date_signed_current_base_and_excercised_options_value": {
                "description": "Current base and exercised options value",
                "category": "financial",
                "search_terms": ["current value", "base value", "exercised options", "current contract value"],
                "data_type": "currency"
            },
            "date_signed_total_base_and_excercised_options_value": {
                "description": "Total base and exercised options value",
                "category": "financial",
                "search_terms": ["total value", "total contract value", "total options", "full contract value"],
                "data_type": "currency"
            },
            "date_signed_base_and_all_options_value": {
                "description": "Base and all options value",
                "category": "financial",
                "search_terms": ["all options", "potential value", "maximum value", "ceiling value"],
                "data_type": "currency"
            },
            "date_signed_total_base_and_all_options_value": {
                "description": "Total base and all options value",
                "category": "financial",
                "search_terms": ["total potential", "maximum contract", "ceiling amount", "total ceiling"],
                "data_type": "currency"
            },
            "date_signed_fee_paid_for_use_of_indefinite_delivery_vehicle": {
                "description": "Fee paid for use of indefinite delivery vehicle",
                "category": "financial",
                "search_terms": ["idv fee", "delivery vehicle fee", "contract fee", "vehicle fee"],
                "data_type": "currency"
            },
            
            # Additional Date Fields
            "period_of_performance_start_date_period_of_performance_start_date": {
                "description": "Period of performance start date",
                "category": "dates",
                "search_terms": ["performance start", "work start", "contract start", "period start"],
                "data_type": "date"
            },
            "completion_date_award_completion_date": {
                "description": "Award completion date",
                "category": "dates",
                "search_terms": ["completion date", "award completion", "contract end", "work end"],
                "data_type": "date"
            },
            "est_ultimate_completion_date_estimated_ultimate_completion_date": {
                "description": "Estimated ultimate completion date",
                "category": "dates",
                "search_terms": ["estimated completion", "ultimate completion", "expected end", "projected end"],
                "data_type": "date"
            },
            
            # Additional Entity Fields
            "unique_entity_id_entity_street": {
                "description": "Street address of the contractor",
                "category": "entity",
                "search_terms": ["contractor address", "vendor address", "business address", "street address"],
                "data_type": "string"
            },
            "unique_entity_id_entity_zip": {
                "description": "ZIP code of the contractor",
                "category": "entity",
                "search_terms": ["contractor zip", "vendor zip", "business zip", "zip code"],
                "data_type": "string"
            },
            "unique_entity_id_vendorcountry": {
                "description": "Vendor country code",
                "category": "entity",
                "search_terms": ["vendor country", "contractor country", "business country", "country code"],
                "data_type": "string"
            },
            "unique_entity_id_entity_phone_number": {
                "description": "Phone number of the contractor",
                "category": "entity",
                "search_terms": ["contractor phone", "vendor phone", "business phone", "phone number"],
                "data_type": "string"
            },
            "unique_entity_id_entity_congressional_district": {
                "description": "Congressional district of the contractor",
                "category": "entity",
                "search_terms": ["congressional district", "contractor district", "vendor district", "political district"],
                "data_type": "string"
            },
            
            # Additional Contract Fields
            "reason_for_modification_reason_for_modification": {
                "description": "Reason for contract modification",
                "category": "contract",
                "search_terms": ["modification reason", "change reason", "contract change", "mod reason"],
                "data_type": "string"
            },
            "foreign_funding": {
                "description": "Whether contract uses foreign funding",
                "category": "contract",
                "search_terms": ["foreign funding", "international funding", "foreign money", "overseas funding"],
                "data_type": "string"
            },
            "multiyear_contract": {
                "description": "Whether this is a multiyear contract",
                "category": "contract",
                "search_terms": ["multiyear", "multi year", "multi-year", "long term contract"],
                "data_type": "string"
            },
            "national_interest_action": {
                "description": "National interest action designation",
                "category": "contract",
                "search_terms": ["national interest", "national security", "critical action", "priority contract"],
                "data_type": "string"
            },
            "cost_or_pricing_data": {
                "description": "Whether cost or pricing data was required",
                "category": "contract",
                "search_terms": ["cost data", "pricing data", "cost analysis", "price analysis"],
                "data_type": "string"
            },
            "purchase_card_used_as_payment_method": {
                "description": "Whether purchase card was used for payment",
                "category": "contract",
                "search_terms": ["purchase card", "government card", "payment method", "card payment"],
                "data_type": "string"
            },
            "undefinitized_action": {
                "description": "Whether this is an undefinitized action",
                "category": "contract",
                "search_terms": ["undefinitized", "not definitized", "pending definition", "temporary contract"],
                "data_type": "string"
            },
            "performance_based_service_acquisition": {
                "description": "Whether this is a performance-based service acquisition",
                "category": "contract",
                "search_terms": ["performance based", "pbsa", "service acquisition", "performance contract"],
                "data_type": "string"
            },
            "emergency_acquisition": {
                "description": "Whether this is an emergency acquisition",
                "category": "contract",
                "search_terms": ["emergency", "urgent", "crisis", "emergency contract"],
                "data_type": "string"
            },
            "contract_financing": {
                "description": "Type of contract financing used",
                "category": "contract",
                "search_terms": ["contract financing", "payment terms", "financing", "payment schedule"],
                "data_type": "string"
            },
            "cost_accounting_standards_clause": {
                "description": "Cost accounting standards clause",
                "category": "contract",
                "search_terms": ["cost accounting", "cas", "accounting standards", "cost standards"],
                "data_type": "string"
            },
            "consolidated_contract": {
                "description": "Whether this is a consolidated contract",
                "category": "contract",
                "search_terms": ["consolidated", "combined contract", "merged contract", "unified contract"],
                "data_type": "string"
            },
            "clingercohen_act": {
                "description": "Whether Clinger-Cohen Act applies",
                "category": "contract",
                "search_terms": ["clinger cohen", "it management", "information technology", "it reform"],
                "data_type": "string"
            },
            "labor_standards": {
                "description": "Whether labor standards apply",
                "category": "contract",
                "search_terms": ["labor standards", "wage requirements", "worker protection", "employment standards"],
                "data_type": "string"
            },
            "materials_supplies_articles_and_equip": {
                "description": "Whether contract involves materials, supplies, articles, and equipment",
                "category": "contract",
                "search_terms": ["materials", "supplies", "equipment", "articles", "goods"],
                "data_type": "string"
            },
            "construction_wage_rate_requirements": {
                "description": "Whether construction wage rate requirements apply",
                "category": "contract",
                "search_terms": ["construction wage", "davis bacon", "prevailing wage", "construction labor"],
                "data_type": "string"
            },
            "interagency_contracting_authority": {
                "description": "Interagency contracting authority used",
                "category": "contract",
                "search_terms": ["interagency", "cross agency", "shared services", "cooperative agreement"],
                "data_type": "string"
            },
            
            # Additional Performance Location Fields
            "principal_place_of_performance_code_principal_place_of_performance_country_code": {
                "description": "Country code for principal place of performance",
                "category": "performance_location",
                "search_terms": ["performance country", "work country", "location country", "country of work"],
                "data_type": "string"
            },
            "principal_place_of_performance_county_name_principal_place_of_performance_county_name": {
                "description": "County name for principal place of performance",
                "category": "performance_location",
                "search_terms": ["performance county", "work county", "location county", "county of work"],
                "data_type": "string"
            },
            "congressional_district_place_of_performance_congressional_district_place_of_performance": {
                "description": "Congressional district for place of performance",
                "category": "performance_location",
                "search_terms": ["performance district", "work district", "location district", "political district"],
                "data_type": "string"
            },
            "place_of_performance_zip_code4_place_of_performance_zip_code5": {
                "description": "ZIP code for place of performance",
                "category": "performance_location",
                "search_terms": ["performance zip", "work zip", "location zip", "zip code"],
                "data_type": "string"
            },
            "place_of_performance_zip_code4_place_of_performance_zip_code4": {
                "description": "ZIP+4 code for place of performance",
                "category": "performance_location",
                "search_terms": ["performance zip4", "work zip4", "location zip4", "zip+4"],
                "data_type": "string"
            },
            
            # Additional Product/Service Fields
            "bundled_contract": {
                "description": "Whether this is a bundled contract",
                "category": "product_service",
                "search_terms": ["bundled", "combined services", "package contract", "multiple services"],
                "data_type": "string"
            },
            "dod_acquisition_program_dod_acquisition_program": {
                "description": "DOD acquisition program code",
                "category": "product_service",
                "search_terms": ["dod program", "acquisition program", "defense program", "military program"],
                "data_type": "string"
            },
            "dod_acquisition_program_programsystem_or_equipment_code_description": {
                "description": "DOD acquisition program description",
                "category": "product_service",
                "search_terms": ["dod description", "program description", "defense description", "military description"],
                "data_type": "string"
            },
            "country_of_product_or_service_origin_country_of_product_or_service_origin": {
                "description": "Country of origin for product or service",
                "category": "product_service",
                "search_terms": ["origin country", "product origin", "service origin", "country of origin"],
                "data_type": "string"
            },
            "country_of_product_or_service_origin_country_of_product_or_service_origin_for_display": {
                "description": "Display name for country of origin",
                "category": "product_service",
                "search_terms": ["origin display", "product origin display", "service origin display"],
                "data_type": "string"
            },
            "place_of_manufacture": {
                "description": "Place of manufacture for the product",
                "category": "product_service",
                "search_terms": ["manufacture", "manufacturing location", "production location", "made in"],
                "data_type": "string"
            },
            "domestic_or_foreign_entity": {
                "description": "Whether the entity is domestic or foreign",
                "category": "entity",
                "search_terms": ["domestic", "foreign", "u.s. owned", "foreign owned", "entity type"],
                "data_type": "string"
            },
            "recovered_materialssustainability": {
                "description": "Recovered materials and sustainability information",
                "category": "product_service",
                "search_terms": ["recovered materials", "sustainability", "green", "environmental", "recycled"],
                "data_type": "string"
            },
            "information_technology_commercial_category": {
                "description": "Information technology commercial category",
                "category": "product_service",
                "search_terms": ["it", "information technology", "software", "hardware", "technology"],
                "data_type": "string"
            },
            "claimant_program_code_claimant_program_code": {
                "description": "Claimant program code",
                "category": "product_service",
                "search_terms": ["claimant program", "program code", "claimant", "program identifier"],
                "data_type": "string"
            },
            "claimant_program_code_claimant_program_code_description": {
                "description": "Claimant program code description",
                "category": "product_service",
                "search_terms": ["claimant description", "program description", "claimant program description"],
                "data_type": "string"
            },
            "sea_transportation": {
                "description": "Sea transportation information",
                "category": "product_service",
                "search_terms": ["sea transportation", "maritime", "shipping", "ocean transport"],
                "data_type": "string"
            },
            "gfp_provided_under_this_action": {
                "description": "Government furnished property provided under this action",
                "category": "product_service",
                "search_terms": ["gfp", "government furnished", "government property", "furnished property"],
                "data_type": "string"
            },
            "use_of_epa_designated_products": {
                "description": "Use of EPA designated products",
                "category": "product_service",
                "search_terms": ["epa", "environmental protection", "designated products", "green products"],
                "data_type": "string"
            },
            
            # Additional Competition Fields
            "source_selection_process": {
                "description": "Source selection process used",
                "category": "competition",
                "search_terms": ["source selection", "selection process", "evaluation process", "award process"],
                "data_type": "string"
            },
            "solicitation_procedures": {
                "description": "Solicitation procedures used",
                "category": "competition",
                "search_terms": ["solicitation", "procurement procedures", "bidding process", "request process"],
                "data_type": "string"
            },
            "idv_type_of_set_aside_idv_type_of_set_aside": {
                "description": "IDV type of set aside",
                "category": "competition",
                "search_terms": ["idv set aside", "delivery vehicle set aside", "vehicle set aside"],
                "data_type": "string"
            },
            "type_of_set_aside_source_type_of_set_aside_source": {
                "description": "Source of the set aside type",
                "category": "competition",
                "search_terms": ["set aside source", "set aside origin", "set aside authority"],
                "data_type": "string"
            },
            "evaluated_preference": {
                "description": "Evaluated preference used",
                "category": "competition",
                "search_terms": ["evaluated preference", "preference", "evaluation preference", "award preference"],
                "data_type": "string"
            },
            "sbirsttr": {
                "description": "SBIR/STTR information",
                "category": "competition",
                "search_terms": ["sbir", "sttr", "small business innovation", "research"],
                "data_type": "string"
            },
            "fair_opportunitylimited_sources": {
                "description": "Fair opportunity or limited sources",
                "category": "competition",
                "search_terms": ["fair opportunity", "limited sources", "competitive set aside", "restricted competition"],
                "data_type": "string"
            },
            "other_than_full_and_open_competition": {
                "description": "Other than full and open competition",
                "category": "competition",
                "search_terms": ["other than full", "non-competitive", "limited competition", "restricted"],
                "data_type": "string"
            },
            "local_area_set_aside": {
                "description": "Local area set aside",
                "category": "competition",
                "search_terms": ["local area", "geographic set aside", "local preference", "area preference"],
                "data_type": "string"
            },
            "contract_opportunities_notice": {
                "description": "Contract opportunities notice",
                "category": "competition",
                "search_terms": ["opportunities notice", "contract notice", "solicitation notice", "bid notice"],
                "data_type": "string"
            },
            "a76_action": {
                "description": "A-76 action",
                "category": "competition",
                "search_terms": ["a76", "circular a-76", "commercial activities", "outsourcing"],
                "data_type": "string"
            },
            "commercial_products_and_services_acquisition_procedures": {
                "description": "Commercial products and services acquisition procedures",
                "category": "competition",
                "search_terms": ["commercial procedures", "commercial acquisition", "commercial products", "commercial services"],
                "data_type": "string"
            },
            "number_of_offers_received_number_of_offers_source": {
                "description": "Source of number of offers received",
                "category": "competition",
                "search_terms": ["offers source", "bids source", "proposals source", "responses source"],
                "data_type": "string"
            },
            "simplified_procedures_for_certain_commercial_products_and_commercial_services": {
                "description": "Simplified procedures for commercial products and services",
                "category": "competition",
                "search_terms": ["simplified procedures", "commercial simplified", "streamlined procedures"],
                "data_type": "string"
            },
            "subcontract_plan": {
                "description": "Subcontract plan",
                "category": "competition",
                "search_terms": ["subcontract", "subcontracting", "subcontract plan", "subcontracting plan"],
                "data_type": "string"
            }
        }
    
    def _create_search_aliases(self) -> Dict[str, List[str]]:
        """
        Create search aliases for common terms and agencies
        """
        return {
            # Agency aliases
            "nasa": ["national aeronautics and space administration", "nasa"],
            "navy": ["department of the navy", "navy", "dept of the navy", "naval", "navfac"],
            "army": ["department of the army", "army", "dept of the army", "military"],
            "air force": ["department of the air force", "air force", "dept of the air force", "usaf"],
            "defense": ["department of defense", "dod", "defense", "military", "defense department"],
            "homeland security": ["department of homeland security", "dhs", "homeland security", "border security"],
            "energy": ["department of energy", "doe", "energy", "nuclear", "renewable energy"],
            "health": ["department of health and human services", "hhs", "health", "medical", "healthcare"],
            "treasury": ["department of the treasury", "treasury", "irs", "tax", "financial"],
            "interior": ["department of the interior", "interior", "national parks", "land management"],
            "agriculture": ["department of agriculture", "usda", "agriculture", "farming", "food"],
            "commerce": ["department of commerce", "commerce", "trade", "economic development"],
            "labor": ["department of labor", "labor", "employment", "workforce"],
            "transportation": ["department of transportation", "dot", "transportation", "highway", "aviation"],
            "education": ["department of education", "education", "schools", "universities"],
            "veterans": ["department of veterans affairs", "va", "veterans", "veteran affairs"],
            "justice": ["department of justice", "doj", "justice", "law enforcement", "fbi"],
            "state": ["department of state", "state department", "diplomacy", "foreign affairs"],
            "epa": ["environmental protection agency", "epa", "environmental", "pollution"],
            "gsa": ["general services administration", "gsa", "government services", "federal buildings"],
            "ssa": ["social security administration", "ssa", "social security", "benefits"],
            "opm": ["office of personnel management", "opm", "personnel", "human resources"],
            "nrc": ["nuclear regulatory commission", "nrc", "nuclear", "regulatory"],
            "fcc": ["federal communications commission", "fcc", "communications", "telecommunications"],
            
            # Date aliases
            "expiring": ["expiring", "ending", "completion", "award completion date", "contract end", "termination"],
            "expired": ["expired", "completed", "finished", "terminated", "closed"],
            "active": ["active", "current", "ongoing", "in progress", "live"],
            "recent": ["recent", "new", "latest", "fresh", "modern"],
            "old": ["old", "historical", "past", "legacy", "archived"],
            "this year": ["this year", "current year", "2024", "2025"],
            "last year": ["last year", "previous year", "2023", "2022"],
            "next year": ["next year", "upcoming year", "2025", "2026"],
            
            # Amount aliases
            "large": ["large", "big", "high value", "expensive", "major", "significant"],
            "small": ["small", "low value", "cheap", "inexpensive", "minor", "minimal"],
            "million": ["million", "millions", "1m", "2m", "multi-million"],
            "billion": ["billion", "billions", "1b", "2b", "multi-billion"],
            "thousand": ["thousand", "thousands", "1k", "2k", "multi-thousand"],
            "high value": ["high value", "expensive", "costly", "premium", "valuable"],
            "low value": ["low value", "cheap", "inexpensive", "budget", "affordable"],
            
            # Business type aliases
            "small business": ["small business", "small", "sba", "small company", "small firm"],
            "large business": ["large business", "large", "big business", "major company", "corporation"],
            "8a": ["8a", "8(a)", "eight a", "8a program", "disadvantaged business"],
            "women owned": ["women owned", "women-owned", "wosb", "women's business", "female owned"],
            "veteran owned": ["veteran owned", "veteran-owned", "vosb", "veteran's business", "military owned"],
            "minority owned": ["minority owned", "minority-owned", "minority business", "diverse owned"],
            "disadvantaged": ["disadvantaged", "sdb", "small disadvantaged business", "economically disadvantaged"],
            "hubzone": ["hubzone", "h.u.b.zone", "historically underutilized", "rural business"],
            "service disabled": ["service disabled", "service-disabled", "disabled veteran", "sdvosb"],
            
            # Contract type aliases
            "fixed price": ["fixed price", "firm fixed price", "ffp", "lump sum", "set price"],
            "cost plus": ["cost plus", "cost-plus", "cost reimbursement", "cost plus fixed fee", "cpff"],
            "time and materials": ["time and materials", "t&m", "time and material", "hourly rate"],
            "delivery order": ["delivery order", "task order", "idv", "indefinite delivery", "blanket purchase"],
            "task order": ["task order", "delivery order", "idv", "work order", "service order"],
            "purchase order": ["purchase order", "po", "buy", "procurement"],
            "modification": ["modification", "mod", "change order", "amendment", "revision"],
            
            # Competition aliases
            "competitive": ["competitive", "full and open", "competed", "bidding", "auction"],
            "non-competitive": ["non-competitive", "noncompetitive", "sole source", "single source", "no competition"],
            "set aside": ["set aside", "set-aside", "reserved", "restricted", "limited competition"],
            "full and open": ["full and open", "unrestricted", "open competition", "public bidding"],
            "sole source": ["sole source", "single source", "no competition", "direct award"],
            
            # Service type aliases
            "construction": ["construction", "building", "infrastructure", "facility", "renovation"],
            "maintenance": ["maintenance", "repair", "service", "upkeep", "support"],
            "consulting": ["consulting", "advisory", "professional services", "expertise", "consultant"],
            "training": ["training", "education", "instruction", "learning", "development"],
            "research": ["research", "development", "rd", "r&d", "study", "analysis"],
            "software": ["software", "it", "information technology", "programming", "development"],
            "hardware": ["hardware", "equipment", "machinery", "devices", "systems"],
            "supplies": ["supplies", "materials", "equipment", "goods", "products"],
            "transportation": ["transportation", "shipping", "logistics", "delivery", "freight"],
            "security": ["security", "protection", "safety", "guarding", "defense"],
            "medical": ["medical", "healthcare", "health", "clinical", "therapeutic"],
            "environmental": ["environmental", "remediation", "cleanup", "pollution", "sustainability"],
            
            # Location aliases
            "domestic": ["domestic", "u.s.", "united states", "american", "local"],
            "foreign": ["foreign", "international", "overseas", "global", "non-domestic"],
            "california": ["california", "ca", "cal", "golden state"],
            "texas": ["texas", "tx", "tex", "lone star state"],
            "new york": ["new york", "ny", "empire state"],
            "florida": ["florida", "fl", "sunshine state"],
            "washington": ["washington", "wa", "evergreen state"],
            "virginia": ["virginia", "va", "old dominion"],
            "maryland": ["maryland", "md", "old line state"],
            "colorado": ["colorado", "co", "centennial state"],
            
            # Status aliases
            "active": ["active", "current", "ongoing", "live", "in progress"],
            "completed": ["completed", "finished", "done", "closed", "terminated"],
            "cancelled": ["cancelled", "canceled", "terminated", "stopped", "discontinued"],
            "pending": ["pending", "waiting", "on hold", "suspended", "delayed"],
            
            # Financial aliases
            "obligated": ["obligated", "committed", "spent", "funded", "allocated"],
            "unobligated": ["unobligated", "uncommitted", "available", "remaining", "unspent"],
            "current": ["current", "present", "now", "today", "latest"],
            "total": ["total", "complete", "full", "entire", "overall"],
            "base": ["base", "basic", "fundamental", "core", "primary"],
            "options": ["options", "optional", "potential", "future", "additional"],
            
            # Performance aliases
            "on time": ["on time", "timely", "schedule", "deadline", "due date"],
            "delayed": ["delayed", "late", "behind schedule", "overdue", "extended"],
            "ahead of schedule": ["ahead of schedule", "early", "premature", "accelerated"],
            "quality": ["quality", "excellent", "superior", "high quality", "premium"],
            "poor": ["poor", "low quality", "inferior", "substandard", "deficient"],
            
            # Emergency aliases
            "emergency": ["emergency", "urgent", "crisis", "critical", "immediate"],
            "disaster": ["disaster", "catastrophe", "emergency response", "recovery", "relief"],
            "covid": ["covid", "covid-19", "coronavirus", "pandemic", "health emergency"],
            
            # Technology aliases
            "ai": ["ai", "artificial intelligence", "machine learning", "automation"],
            "cloud": ["cloud", "cloud computing", "saas", "software as a service"],
            "cybersecurity": ["cybersecurity", "security", "information security", "cyber", "protection"],
            "data": ["data", "analytics", "big data", "information", "statistics"],
            "mobile": ["mobile", "smartphone", "app", "application", "ios", "android"],
            
            # Industry aliases
            "aerospace": ["aerospace", "aviation", "aircraft", "space", "satellite"],
            "defense": ["defense", "military", "weapons", "security", "national security"],
            "healthcare": ["healthcare", "medical", "health", "clinical", "patient care"],
            "education": ["education", "training", "learning", "academic", "school"],
            "transportation": ["transportation", "logistics", "shipping", "delivery", "freight"],
            "energy": ["energy", "power", "electricity", "renewable", "solar", "wind"],
            "environmental": ["environmental", "cleanup", "remediation", "pollution", "sustainability"]
        }
    
    def find_matching_fields(self, query: str) -> List[Dict]:
        """
        Find fields that match the natural language query
        """
        query_lower = query.lower()
        matches = []
        
        # Check for exact matches and partial matches
        for field_name, field_info in self.field_mappings.items():
            score = 0
            matched_terms = []
            
            # Check description
            if query_lower in field_info["description"].lower():
                score += 10
                matched_terms.append("description")
            
            # Check search terms
            for term in field_info["search_terms"]:
                if query_lower in term.lower() or term.lower() in query_lower:
                    score += 5
                    matched_terms.append(f"search_term: {term}")
            
            # Check category
            if query_lower in field_info["category"]:
                score += 3
                matched_terms.append("category")
            
            if score > 0:
                matches.append({
                    "field_name": field_name,
                    "score": score,
                    "matched_terms": matched_terms,
                    "description": field_info["description"],
                    "category": field_info["category"],
                    "data_type": field_info["data_type"]
                })
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches
    
    def expand_search_terms(self, query: str) -> List[str]:
        """
        Expand search terms using aliases
        """
        expanded_terms = [query.lower()]
        
        for alias_key, alias_terms in self.search_aliases.items():
            if alias_key in query.lower():
                expanded_terms.extend(alias_terms)
        
        return list(set(expanded_terms))
    
    def build_mongodb_query(self, natural_query: str) -> Dict:
        """
        Build a MongoDB query from natural language
        """
        # This is a simplified version - in practice, you'd use more sophisticated NLP
        query_parts = natural_query.lower().split()
        mongo_query = {}
        
        # Look for specific patterns
        if "nasa" in natural_query.lower():
            mongo_query["contracting_office_agency_id_contracting_office_agency_name"] = {
                "$regex": "NASA", "$options": "i"
            }
        
        if "expiring" in natural_query.lower():
            # Look for completion dates in the future
            mongo_query["date_signed_award_completion_date"] = {
                "$gte": datetime.now().strftime("%m/%d/%Y")
            }
        
        if "large" in natural_query.lower():
            # Look for high-value contracts
            mongo_query["$or"] = [
                {"action_obligation_total_obligation_amount": {"$regex": r"\$[0-9]{7,}", "$options": "i"}},
                {"base_and_exercised_options_value_total_base_and_excercised_options_value": {"$regex": r"\$[0-9]{7,}", "$options": "i"}}
            ]
        
        return mongo_query
    
    def get_field_info(self, field_name: str) -> Optional[Dict]:
        """
        Get information about a specific field
        """
        return self.field_mappings.get(field_name)
    
    def get_fields_by_category(self, category: str) -> List[str]:
        """
        Get all fields in a specific category
        """
        return [field for field, info in self.field_mappings.items() if info["category"] == category]
    
    def get_all_categories(self) -> List[str]:
        """
        Get all available categories
        """
        return list(set(info["category"] for info in self.field_mappings.values()))
    
    def get_award_id_fields(self) -> List[str]:
        """
        Get all award ID related fields
        """
        return [field for field, info in self.field_mappings.items() if info["category"] == "award_id"]
    
    def ensure_award_id_in_results(self, results: List[Dict]) -> List[Dict]:
        """
        Ensure award ID fields are always present in results
        """
        award_id_fields = self.get_award_id_fields()
        
        for result in results:
            # Ensure all award ID fields are present
            for field in award_id_fields:
                if field not in result:
                    result[field] = "Not Available"
        
        return results
    
    def build_award_id_query(self, award_id: str) -> Dict:
        """
        Build a query to search by award ID (PIID)
        """
        return {
            "award_id_procurement_identifier": {
                "$regex": award_id, "$options": "i"
            }
        }
    
    def build_award_id_agency_query(self, agency_id: str) -> Dict:
        """
        Build a query to search by award agency ID
        """
        return {
            "award_id_agency_id": {
                "$regex": agency_id, "$options": "i"
            }
        }

# Example usage
if __name__ == "__main__":
    mapper = FPDSFieldMapper()
    
    # Test field matching
    query = "NASA contracts expiring soon"
    matches = mapper.find_matching_fields(query)
    print(f"Matches for '{query}':")
    for match in matches[:5]:
        print(f"  {match['field_name']}: {match['description']} (score: {match['score']})")
    
    # Test MongoDB query building
    mongo_query = mapper.build_mongodb_query("NASA contracts expiring in 2025")
    print(f"\nMongoDB query: {json.dumps(mongo_query, indent=2)}") 