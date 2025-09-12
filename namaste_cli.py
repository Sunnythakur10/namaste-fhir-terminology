#!/usr/bin/env python3
"""
NAMASTE-FHIR Terminology CLI Tool
Implements Terminology Ingestion & Representation feature with command-line interface

Features:
- Parse NAMASTE CSV export
- Generate FHIR CodeSystem
- Create FHIR ConceptMap linking NAMASTE → ICD-11 TM2 / Biomedicine codes
- WHO ICD-11 API Integration for real-time terminology mapping
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

try:
    from icd11_client import ICD11APIClient
    ICD11_AVAILABLE = True
except ImportError:
    ICD11_AVAILABLE = False
    print("⚠️  ICD-11 API client not available. Using fallback mappings.")


class NAMASTETerminologyCLI:
    """CLI tool for NAMASTE terminology ingestion and FHIR resource generation"""
    
    def __init__(self, use_icd11_api: bool = True):
        self.namaste_data = []
        self.use_icd11_api = use_icd11_api and ICD11_AVAILABLE
        self.icd11_client = None
        self.enhanced_mappings = None
        
        # Fallback mappings for when API is not available
        self.fallback_mappings = {
            "AAE-16": {"tm2": "SP00", "biomed": "FA01", "name": "Sandhigatvata"},
            "AA": {"tm2": "SP10", "biomed": "FA20", "name": "Vatavyadhi"},
            "EE-3": {"tm2": "SL01", "biomed": "ME83", "name": "Arsha"},
            "EF-2.4.4": {"tm2": "SJ00", "biomed": "5A11", "name": "Madhumeha/Kshaudrameha"},
            "EA-3": {"tm2": "SB00", "biomed": "CA22", "name": "Kasa"}
        }
        
        if self.use_icd11_api:
            self._initialize_icd11_client()
    
    def _initialize_icd11_client(self):
        """Initialize ICD-11 API client and fetch enhanced mappings"""
        try:
            print("🌐 Initializing WHO ICD-11 API integration...")
            self.icd11_client = ICD11APIClient()
            
            # Get enhanced mappings from real ICD-11 API
            self.enhanced_mappings = self.icd11_client.get_enhanced_namaste_mappings()
            print("✅ ICD-11 API integration initialized successfully")
            
        except Exception as e:
            print(f"⚠️  Failed to initialize ICD-11 API client: {str(e)}")
            print("   Using fallback mappings instead.")
            self.use_icd11_api = False
            self.icd11_client = None
    
    def get_icd_mappings_for_code(self, code: str) -> Dict[str, Any]:
        """Get ICD-11 mappings for a NAMASTE code"""
        if self.use_icd11_api and self.enhanced_mappings and code in self.enhanced_mappings:
            mapping_data = self.enhanced_mappings[code]
            
            # Convert enhanced mappings to compatible format
            tm2_codes = mapping_data.get('tm2_codes', [])
            biomed_codes = mapping_data.get('biomed_codes', [])
            
            return {
                'tm2': tm2_codes[0]['code'] if tm2_codes else 'UNKNOWN',
                'biomed': biomed_codes[0]['code'] if biomed_codes else 'UNKNOWN',
                'name': mapping_data.get('name', ''),
                'tm2_display': tm2_codes[0]['display'] if tm2_codes else '',
                'biomed_display': biomed_codes[0]['display'] if biomed_codes else '',
                'source': 'WHO_ICD11_API'
            }
        else:
            # Use fallback mappings
            fallback = self.fallback_mappings.get(code, {"tm2": "UNKNOWN", "biomed": "UNKNOWN", "name": ""})
            return {
                'tm2': fallback['tm2'],
                'biomed': fallback['biomed'],
                'name': fallback['name'],
                'tm2_display': f"ICD-11 TM2: {fallback['tm2']}",
                'biomed_display': f"ICD-11 Biomedicine: {fallback['biomed']}",
                'source': 'FALLBACK'
            }
    
    def parse_csv(self, csv_file_path: str) -> bool:
        """Parse NAMASTE CSV export file"""
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                self.namaste_data = []
                
                for row in csv_reader:
                    # Add ICD-11 mappings based on Code using enhanced API or fallback
                    code = row.get('Code', '')
                    mapping = self.get_icd_mappings_for_code(code)
                    
                    row['icd11_tm2_code'] = mapping['tm2']
                    row['icd11_biomed_code'] = mapping['biomed']
                    row['icd11_tm2_display'] = mapping.get('tm2_display', '')
                    row['icd11_biomed_display'] = mapping.get('biomed_display', '')
                    row['mapping_source'] = mapping.get('source', 'UNKNOWN')
                    self.namaste_data.append(row)
                
                api_source = "WHO ICD-11 API" if self.use_icd11_api else "fallback mappings"
                print(f"✅ Successfully parsed {len(self.namaste_data)} records from {csv_file_path} using {api_source}")
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
        
        # Create target elements with enhanced mapping information
        target_elements = []
        for code, row in unique_codes.items():
            targets = []
            
            # Add TM2 mapping
            tm2_code = row.get("icd11_tm2_code", "")
            tm2_display = row.get("icd11_tm2_display", f"ICD-11 TM2: {tm2_code}")
            if tm2_code and tm2_code != "UNKNOWN":
                targets.append({
                    "code": tm2_code,
                    "display": tm2_display,
                    "equivalence": "equivalent",
                    "comment": f"Traditional Medicine 2 (TM2) mapping - Source: {row.get('mapping_source', 'UNKNOWN')}"
                })
            
            # Add Biomedicine mapping
            biomed_code = row.get("icd11_biomed_code", "")
            biomed_display = row.get("icd11_biomed_display", f"ICD-11 Biomedicine: {biomed_code}")
            if biomed_code and biomed_code != "UNKNOWN":
                targets.append({
                    "code": biomed_code,
                    "display": biomed_display,
                    "equivalence": "equivalent",
                    "comment": f"Biomedicine mapping - Source: {row.get('mapping_source', 'UNKNOWN')}"
                })
            
            if targets:  # Only add if we have valid targets
                target_elements.append({
                    "code": code,
                    "display": row.get("Disease", ""),
                    "target": targets
                })
        
        conceptmap = {
            "resourceType": "ConceptMap",
            "id": "namaste-to-icd11",
            "url": "http://example.com/namaste-to-icd11",
            "version": "2.0.0",
            "name": "NamasteToICD11Enhanced",
            "title": "NAMASTE to ICD-11 Enhanced Concept Map",
            "status": "active",
            "experimental": False,
            "date": datetime.now().isoformat(),
            "publisher": "Ministry of AYUSH, Government of India",
            "description": "Enhanced mapping from NAMASTE traditional medicine terminology to ICD-11 Traditional Medicine 2 (TM2) and Biomedicine codes using WHO ICD-11 API integration",
            "sourceUri": "http://ayush.gov.in/namaste",
            "targetUri": "http://hl7.org/fhir/sid/icd-11",
            "group": [
                {
                    "source": "http://ayush.gov.in/namaste",
                    "target": "http://hl7.org/fhir/sid/icd-11",
                    "element": target_elements
                }
            ]
        }
        
        mapping_source = "WHO ICD-11 API" if self.use_icd11_api else "fallback mappings"
        print(f"✅ Generated enhanced FHIR ConceptMap with {len(unique_codes)} concept mappings using {mapping_source}")
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
        
        mapping_source = "WHO ICD-11 API" if self.use_icd11_api else "fallback mappings"
        print(f"   • Mapping source: {mapping_source}")
        
        print("\n🔗 Available Code Mappings:")
        for code in sorted(unique_codes):
            mapping = self.get_icd_mappings_for_code(code)
            tm2_code = mapping.get('tm2', 'UNKNOWN')
            biomed_code = mapping.get('biomed', 'UNKNOWN')
            source = mapping.get('source', 'UNKNOWN')
            
            print(f"   • {code} → TM2: {tm2_code}, Biomed: {biomed_code} ({source})")
        
        # Show ICD-11 API status
        if self.use_icd11_api and self.icd11_client:
            cache_summary = self.icd11_client.get_terminology_cache_summary()
            print(f"\n📱 ICD-11 API Cache: {len(cache_summary['cached_files'])} files, {cache_summary['total_cache_size']} bytes")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="NAMASTE-FHIR Terminology CLI Tool with WHO ICD-11 API Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse CSV and generate all FHIR resources with WHO ICD-11 API
  python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --all --output-dir fhir-output/

  # Generate only CodeSystem
  python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --codesystem --output codesystem.json

  # Generate only ConceptMap
  python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --conceptmap --output conceptmap.json

  # Display data summary with API mappings
  python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --summary

  # Use fallback mappings (disable API)
  python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --all --no-api

  # Test ICD-11 API integration
  python namaste_cli.py --test-api
        """
    )
    
    parser.add_argument('--input', '-i',
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
    parser.add_argument('--no-api', action='store_true',
                       help='Disable WHO ICD-11 API integration (use fallback mappings)')
    parser.add_argument('--test-api', action='store_true',
                       help='Test WHO ICD-11 API integration')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Test API integration if requested
    if args.test_api:
        if ICD11_AVAILABLE:
            from icd11_client import test_icd11_client
            test_icd11_client()
        else:
            print("❌ ICD-11 API client not available. Install requirements: pip install -r requirements.txt")
        return
    
    # Validate input requirement
    if not args.input:
        print("❌ Input file is required. Use --input or --test-api for API testing.")
        sys.exit(1)
    
    # Initialize CLI tool
    use_api = not args.no_api
    cli = NAMASTETerminologyCLI(use_icd11_api=use_api)
    
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