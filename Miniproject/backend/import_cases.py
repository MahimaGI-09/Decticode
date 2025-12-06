"""
Case Database Import System
Designed to import real case data into the system when ready

Usage:
    1. Prepare your case data in CSV or JSON format (see examples below)
    2. Run: python import_cases.py --file your_cases.csv --format csv
    3. System validates and stores in MongoDB
    4. Run investigations against real data

Supported Formats:
    - CSV with columns: case_id, title, description, crime_type, status, evidence (JSON)
    - JSON with array of case objects
    - Excel (.xlsx) - requires openpyxl
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Union
from datetime import datetime
import argparse
from app.core import storage

class CaseDataImporter:
    """Import and validate case data from various formats"""
    
    # Required fields for each case
    REQUIRED_FIELDS = ["case_id", "title", "crime_type"]
    
    # Optional fields with defaults
    OPTIONAL_FIELDS = {
        "description": "",
        "status": "active",
        "jurisdiction": "general",
        "created_at": None,  # Will use current time if not provided
        "evidence": []  # List of evidence items
    }
    
    # Valid crime types (matches templates)
    VALID_CRIME_TYPES = ["homicide", "theft", "fraud", "assault", "sexual_assault", 
                          "robbery", "burglary", "drug_trafficking", "arson", "generic"]
    
    # Valid statuses
    VALID_STATUSES = ["active", "closed", "cold_case", "on_hold", "reopened"]
    
    def __init__(self):
        """Initialize importer"""
        self.db = storage.get_db()
        self.cases_imported = 0
        self.cases_failed = 0
        self.errors = []
    
    def import_from_csv(self, filepath: str) -> Dict[str, Any]:
        """Import cases from CSV file
        
        Expected columns:
        - case_id (required)
        - title (required)
        - crime_type (required)
        - description (optional)
        - status (optional, default: active)
        - jurisdiction (optional)
        - evidence (optional, JSON string with list of evidence)
        
        Example CSV row:
        homicide_2024_001,"Riverside Murder","A victim found at Riverside Park",homicide,active,general,"[{\"type\": \"witness\", \"description\": \"Statement from Sarah Chen\", \"content\": \"I saw...\"}]"
        """
        print(f"[*] Importing from CSV: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                if not reader.fieldnames:
                    raise ValueError("CSV file is empty or has no headers")
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                    try:
                        case = self._process_case(row)
                        self._insert_case(case)
                        self.cases_imported += 1
                        print(f"  ✓ Row {row_num}: {case['case_id']}")
                    except Exception as e:
                        self.cases_failed += 1
                        error_msg = f"Row {row_num}: {str(e)}"
                        self.errors.append(error_msg)
                        print(f"  ✗ {error_msg}")
        
        except FileNotFoundError:
            print(f"[!] File not found: {filepath}")
            return self._get_summary()
        except Exception as e:
            print(f"[!] Error reading CSV: {e}")
            return self._get_summary()
        
        return self._get_summary()
    
    def import_from_json(self, filepath: str) -> Dict[str, Any]:
        """Import cases from JSON file
        
        Expected format:
        [
            {
                "case_id": "homicide_2024_001",
                "title": "Riverside Murder",
                "description": "...",
                "crime_type": "homicide",
                "status": "active",
                "evidence": [...]
            },
            ...
        ]
        """
        print(f"[*] Importing from JSON: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("JSON must be an array of case objects")
            
            for idx, case_data in enumerate(data, start=1):
                try:
                    case = self._process_case(case_data)
                    self._insert_case(case)
                    self.cases_imported += 1
                    print(f"  ✓ Case {idx}: {case['case_id']}")
                except Exception as e:
                    self.cases_failed += 1
                    error_msg = f"Case {idx}: {str(e)}"
                    self.errors.append(error_msg)
                    print(f"  ✗ {error_msg}")
        
        except FileNotFoundError:
            print(f"[!] File not found: {filepath}")
        except json.JSONDecodeError as e:
            print(f"[!] Invalid JSON: {e}")
        except Exception as e:
            print(f"[!] Error reading JSON: {e}")
        
        return self._get_summary()
    
    def _process_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and process case data"""
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in case_data or not case_data[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate crime type
        crime_type = case_data["crime_type"].lower()
        if crime_type not in self.VALID_CRIME_TYPES:
            raise ValueError(f"Invalid crime_type '{crime_type}'. Valid types: {', '.join(self.VALID_CRIME_TYPES)}")
        
        # Validate status if provided
        if "status" in case_data and case_data["status"]:
            status = case_data["status"].lower()
            if status not in self.VALID_STATUSES:
                raise ValueError(f"Invalid status '{status}'. Valid statuses: {', '.join(self.VALID_STATUSES)}")
        
        # Process evidence
        evidence = []
        if "evidence" in case_data and case_data["evidence"]:
            evidence_input = case_data["evidence"]
            
            # If it's a string (from CSV), try to parse as JSON
            if isinstance(evidence_input, str):
                try:
                    evidence = json.loads(evidence_input)
                except json.JSONDecodeError:
                    evidence = []
            elif isinstance(evidence_input, list):
                evidence = evidence_input
        
        # Build final case object
        case = {
            "case_id": str(case_data["case_id"]).strip(),
            "title": str(case_data["title"]).strip(),
            "crime_type": crime_type,
            "description": str(case_data.get("description", "")).strip(),
            "status": case_data.get("status", "active").lower(),
            "jurisdiction": case_data.get("jurisdiction", "general"),
            "evidence_items": evidence,
            "imported_at": datetime.utcnow(),
            "case_number": str(case_data.get("case_number", "")),
            "assigned_to": case_data.get("assigned_to"),
            "created_at": case_data.get("created_at") or datetime.utcnow().isoformat()
        }
        
        return case
    
    def _insert_case(self, case: Dict[str, Any]):
        """Insert case into MongoDB"""
        try:
            # Check if case already exists
            existing = self.db["cases"].find_one({"case_id": case["case_id"]})
            if existing:
                # Update existing case
                self.db["cases"].update_one(
                    {"case_id": case["case_id"]},
                    {"$set": case}
                )
            else:
                # Insert new case
                self.db["cases"].insert_one(case)
            
            # Insert evidence items if provided
            if case.get("evidence_items"):
                for evidence in case["evidence_items"]:
                    evidence_doc = {
                        "case_id": case["case_id"],
                        "type": evidence.get("type", "document"),
                        "description": evidence.get("description", ""),
                        "content": evidence.get("content", ""),
                        "timestamp": datetime.utcnow()
                    }
                    
                    # Upsert by case_id + description combination
                    self.db["evidence"].update_one(
                        {
                            "case_id": case["case_id"],
                            "description": evidence_doc["description"]
                        },
                        {"$set": evidence_doc},
                        upsert=True
                    )
        
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
    
    def _get_summary(self) -> Dict[str, Any]:
        """Get import summary"""
        return {
            "total_imported": self.cases_imported,
            "total_failed": self.cases_failed,
            "total_processed": self.cases_imported + self.cases_failed,
            "errors": self.errors if self.errors else None
        }


class CaseDataTemplate:
    """Generate template files for case data import"""
    
    @staticmethod
    def generate_csv_template(filepath: str = "case_template.csv"):
        """Generate CSV template"""
        template = """case_id,title,description,crime_type,status,jurisdiction,case_number,assigned_to
homicide_2024_001,"Riverside Murder","Victim found at Riverside Park with knife wound",homicide,active,general,2024-001,Detective Smith
theft_2024_001,"Downtown Jewelry Store Robbery","Estimated $50,000 in stolen items",theft,closed,downtown,2024-002,Detective Jones
fraud_2024_001,"Online Scam Ring","Multiple victims lost money to fake investment scheme",fraud,active,cyber,2024-003,Agent Williams
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(template)
        print(f"[+] CSV template created: {filepath}")
    
    @staticmethod
    def generate_json_template(filepath: str = "case_template.json"):
        """Generate JSON template"""
        template = {
            "cases": [
                {
                    "case_id": "homicide_2024_001",
                    "title": "Riverside Murder",
                    "description": "Victim found at Riverside Park with knife wound. Multiple suspects identified.",
                    "crime_type": "homicide",
                    "status": "active",
                    "jurisdiction": "general",
                    "case_number": "2024-001",
                    "assigned_to": "Detective Smith",
                    "evidence": [
                        {
                            "type": "witness_statement",
                            "description": "Witness Statement - Sarah Chen",
                            "content": "I saw a man in a dark jacket running from the park around 9:15 PM."
                        },
                        {
                            "type": "physical",
                            "description": "Murder Weapon",
                            "content": "Kitchen knife recovered from trash can. Fingerprints match suspect."
                        }
                    ]
                },
                {
                    "case_id": "theft_2024_001",
                    "title": "Downtown Jewelry Store Robbery",
                    "description": "Estimated $50,000 in stolen items",
                    "crime_type": "theft",
                    "status": "closed",
                    "jurisdiction": "downtown",
                    "case_number": "2024-002",
                    "assigned_to": "Detective Jones"
                }
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2)
        print(f"[+] JSON template created: {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Import case data into the criminal justice system"
    )
    parser.add_argument(
        "--file", "-f",
        required=True,
        help="Path to case data file (CSV or JSON)"
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json", "auto"],
        default="auto",
        help="File format (auto-detect if not specified)"
    )
    parser.add_argument(
        "--generate-template",
        choices=["csv", "json"],
        help="Generate a template file and exit"
    )
    
    args = parser.parse_args()
    
    # Generate template if requested
    if args.generate_template:
        if args.generate_template == "csv":
            CaseDataTemplate.generate_csv_template()
        else:
            CaseDataTemplate.generate_json_template()
        return
    
    # Detect format if auto
    file_format = args.format
    if file_format == "auto":
        filepath = Path(args.file)
        if filepath.suffix.lower() == ".csv":
            file_format = "csv"
        elif filepath.suffix.lower() in [".json", ".jsonl"]:
            file_format = "json"
        else:
            print("[!] Could not auto-detect format. Please specify --format")
            return
    
    # Import data
    importer = CaseDataImporter()
    
    if file_format == "csv":
        result = importer.import_from_csv(args.file)
    else:
        result = importer.import_from_json(args.file)
    
    # Print summary
    print("\n" + "=" * 70)
    print("IMPORT SUMMARY")
    print("=" * 70)
    print(f"Total processed: {result['total_processed']}")
    print(f"  ✓ Imported: {result['total_imported']}")
    print(f"  ✗ Failed: {result['total_failed']}")
    
    if result.get("errors"):
        print("\nErrors:")
        for error in result["errors"][:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(result["errors"]) > 10:
            print(f"  ... and {len(result['errors']) - 10} more")
    
    print("=" * 70)


if __name__ == "__main__":
    main()
