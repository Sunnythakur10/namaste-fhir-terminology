#!/usr/bin/env python3
"""
NAMASTE-FHIR Terminology CLI Tool
Implements Terminology Ingestion & Representation feature with command-line interface

Features:
- Parse NAMASTE CSV export
- Generate FHIR CodeSystem
- Create FHIR ConceptMap linking NAMASTE → ICD-11 TM2 / Biomedicine codes
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class NAMASTETerminologyCLI:
    """CLI tool for NAMASTE terminology ingestion and FHIR resource generation"""
    
    def __init__(self):
        self.namaste_data = []
        self.icd_mappings = {
            "AAE-16": {"tm2": "SP00", "biomed": "FA01", "name": "Sandhigatvata"},
            "AA": {"tm2": "SP10", "biomed": "FA20", "name": "Vatavyadhi"},
            "EE-3": {"tm2": "SL01", "biomed": "ME83", "name": "Arsha"},
            "EF-2.4.4": {"tm2": "SJ00", "biomed": "5A11", "name": "Madhumeha/Kshaudrameha"},
            "EA-3": {"tm2": "SB00", "biomed": "CA22", "name": "Kasa"}
        }
    
    def parse_csv(self, csv_file_path: str) -> bool:
        """Parse NAMASTE CSV export file"""
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                self.namaste_data = []
                
                for row in csv_reader:
                    # Add ICD-11 mappings based on Code
                    code = row.get('Code', '')
                    mapping = self.icd_mappings.get(code, {"tm2": "UNKNOWN", "biomed": "UNKNOWN"})
                    
                    row['icd11_tm2_code'] = mapping['tm2']
                    row['icd11_biomed_code'] = mapping['biomed']
                    self.namaste_data.append(row)
                
                print(f"✅ Successfully parsed {len(self.namaste_data)} records from {csv_file_path}")
                return True
                
        except FileNotFoundError:
            print(f"❌ Error: File '{csv_file_path}' not found")
            return False
        except Exception as e:
            print(f"❌ Error parsing CSV: {str(e)}")
            return False
    
    def generate_fhir_codesystem(self) -> Dict[str, Any]:
        """Generate FHIR CodeSystem from NAMASTE data"""
        if not self.namaste_data:
            raise ValueError("No NAMASTE data loaded. Please parse CSV first.")
        
        # Get unique codes to avoid duplicates
        unique_codes = {}
        for row in self.namaste_data:
            code = row.get('Code', '')
            if code and code not in unique_codes:
                unique_codes[code] = row
        
        codesystem = {
            "resourceType": "CodeSystem",
            "id": "namaste-terminology",
            "url": "http://ayush.gov.in/namaste",
            "version": "1.0.0",
            "name": "NAMASTE",
            "title": "NAMASTE Traditional Medicine Terminology",
            "status": "active",
            "experimental": False,
            "date": datetime.now().isoformat(),
            "publisher": "Ministry of AYUSH, Government of India",
            "description": "NAMASTE (National AYUSH Morbidity and Standardized Terminologies Electronic) terminology system for traditional medicine",
            "content": "complete",
            "count": len(unique_codes),
            "concept": [
                {
                    "code": code,
                    "display": row.get("Disease", ""),
                    "definition": row.get("Short_Definition", "")
                }
                for code, row in unique_codes.items()
            ]
        }
        
        print(f"✅ Generated FHIR CodeSystem with {len(unique_codes)} concepts")
        return codesystem
    
    def generate_fhir_conceptmap(self) -> Dict[str, Any]:
        """Create FHIR ConceptMap linking NAMASTE → ICD-11 TM2 / Biomedicine codes"""
        if not self.namaste_data:
            raise ValueError("No NAMASTE data loaded. Please parse CSV first.")
        
        # Get unique codes to avoid duplicates
        unique_codes = {}
        for row in self.namaste_data:
            code = row.get('Code', '')
            if code and code not in unique_codes:
                unique_codes[code] = row
        
        conceptmap = {
            "resourceType": "ConceptMap",
            "id": "namaste-to-icd11",
            "url": "http://example.com/namaste-to-icd11",
            "version": "1.0.0",
            "name": "NamasteToICD11",
            "title": "NAMASTE to ICD-11 Concept Map",
            "status": "active",
            "experimental": False,
            "date": datetime.now().isoformat(),
            "publisher": "Ministry of AYUSH, Government of India",
            "description": "Mapping from NAMASTE traditional medicine terminology to ICD-11 Traditional Medicine 2 (TM2) and Biomedicine codes",
            "sourceUri": "http://ayush.gov.in/namaste",
            "targetUri": "http://hl7.org/fhir/sid/icd-11",
            "group": [
                {
                    "source": "http://ayush.gov.in/namaste",
                    "target": "http://hl7.org/fhir/sid/icd-11",
                    "element": [
                        {
                            "code": code,
                            "display": row.get("Disease", ""),
                            "target": [
                                {
                                    "code": row.get("icd11_tm2_code", ""),
                                    "display": f"ICD-11 TM2: {row.get('icd11_tm2_code', '')}",
                                    "equivalence": "equivalent",
                                    "comment": "Traditional Medicine 2 (TM2) mapping"
                                },
                                {
                                    "code": row.get("icd11_biomed_code", ""),
                                    "display": f"ICD-11 Biomedicine: {row.get('icd11_biomed_code', '')}",
                                    "equivalence": "equivalent", 
                                    "comment": "Biomedicine mapping"
                                }
                            ]
                        }
                        for code, row in unique_codes.items()
                    ]
                }
            ]
        }
        
        print(f"✅ Generated FHIR ConceptMap with {len(unique_codes)} concept mappings")
        return conceptmap
    
    def save_to_file(self, data: Dict[str, Any], output_path: str) -> bool:
        """Save FHIR resource to JSON file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            print(f"✅ Saved {data['resourceType']} to {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving to file: {str(e)}")
            return False
    
    def display_summary(self):
        """Display summary of loaded data"""
        if not self.namaste_data:
            print("❌ No data loaded")
            return
        
        unique_codes = set(row.get('Code', '') for row in self.namaste_data)
        unique_diseases = set(row.get('Disease', '') for row in self.namaste_data)
        
        print("\n📊 NAMASTE Data Summary:")
        print(f"   • Total records: {len(self.namaste_data)}")
        print(f"   • Unique codes: {len(unique_codes)}")
        print(f"   • Unique diseases: {len(unique_diseases)}")
        
        print("\n🔗 Available Code Mappings:")
        for code in sorted(unique_codes):
            if code in self.icd_mappings:
                mapping = self.icd_mappings[code]
                print(f"   • {code} → TM2: {mapping['tm2']}, Biomed: {mapping['biomed']}")
            else:
                print(f"   • {code} → No mapping available")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="NAMASTE-FHIR Terminology CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse CSV and generate all FHIR resources
  python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --all --output-dir fhir-output/

  # Generate only CodeSystem
  python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --codesystem --output codesystem.json

  # Generate only ConceptMap
  python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --conceptmap --output conceptmap.json

  # Display data summary
  python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --summary
        """
    )
    
    parser.add_argument('--input', '-i', required=True,
                       help='Path to NAMASTE CSV file')
    parser.add_argument('--output', '-o',
                       help='Output file path (for single resource)')
    parser.add_argument('--output-dir', '-d',
                       help='Output directory (for multiple resources)')
    parser.add_argument('--codesystem', action='store_true',
                       help='Generate FHIR CodeSystem')
    parser.add_argument('--conceptmap', action='store_true',
                       help='Generate FHIR ConceptMap')
    parser.add_argument('--all', action='store_true',
                       help='Generate all FHIR resources')
    parser.add_argument('--summary', action='store_true',
                       help='Display data summary only')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Initialize CLI tool
    cli = NAMASTETerminologyCLI()
    
    # Parse input CSV
    if not cli.parse_csv(args.input):
        sys.exit(1)
    
    # Display summary if requested
    if args.summary:
        cli.display_summary()
        return
    
    # Determine what to generate
    generate_codesystem = args.codesystem or args.all
    generate_conceptmap = args.conceptmap or args.all
    
    if not (generate_codesystem or generate_conceptmap):
        print("❌ No output specified. Use --codesystem, --conceptmap, or --all")
        sys.exit(1)
    
    # Set up output paths
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        codesystem_path = output_dir / "namaste-codesystem.json"
        conceptmap_path = output_dir / "namaste-conceptmap.json"
    elif args.output:
        if generate_codesystem and generate_conceptmap:
            print("❌ Cannot use single output file for multiple resources. Use --output-dir instead.")
            sys.exit(1)
        codesystem_path = args.output
        conceptmap_path = args.output
    else:
        # Default output files
        codesystem_path = "namaste-codesystem.json"
        conceptmap_path = "namaste-conceptmap.json"
    
    # Generate and save FHIR resources
    try:
        if generate_codesystem:
            codesystem = cli.generate_fhir_codesystem()
            cli.save_to_file(codesystem, codesystem_path)
        
        if generate_conceptmap:
            conceptmap = cli.generate_fhir_conceptmap()
            cli.save_to_file(conceptmap, conceptmap_path)
        
        print("\n🎉 Terminology ingestion completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()