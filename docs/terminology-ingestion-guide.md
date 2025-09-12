# NAMASTE-FHIR Terminology Ingestion & Representation

This feature implements comprehensive terminology ingestion and representation capabilities with both CLI and UI modes, allowing users to parse NAMASTE CSV exports and generate FHIR CodeSystem and ConceptMap resources.

## Feature Overview

The Terminology Ingestion & Representation feature provides:

1. **Parse NAMASTE CSV Export**: Automatic parsing of NAMASTE (National AYUSH Morbidity and Standardized Terminologies Electronic) CSV files
2. **Generate FHIR CodeSystem**: Creates standards-compliant FHIR CodeSystem resources from traditional medicine terminology
3. **Create FHIR ConceptMap**: Links NAMASTE codes to ICD-11 TM2 (Traditional Medicine 2) and Biomedicine codes

## Implementation Modes

### CLI Mode (Command-Line Interface)

The CLI tool (`namaste_cli.py`) provides full functionality for system integration and automation:

#### Installation
```bash
# The CLI tool is ready to use - no additional installation required
python namaste_cli.py --help
```

#### Usage Examples

**Display data summary:**
```bash
python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --summary
```

**Generate all FHIR resources:**
```bash
python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --all --output-dir fhir-output/
```

**Generate only CodeSystem:**
```bash
python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --codesystem --output codesystem.json
```

**Generate only ConceptMap:**
```bash
python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --conceptmap --output conceptmap.json
```

#### CLI Output Example
```
✅ Successfully parsed 50 records from dataset/namaste_dummy_dataset.csv

📊 NAMASTE Data Summary:
   • Total records: 50
   • Unique codes: 5
   • Unique diseases: 5

🔗 Available Code Mappings:
   • AAE-16 → TM2: SP00, Biomed: FA01
   • AA → TM2: SP10, Biomed: FA20
   • EE-3 → TM2: SL01, Biomed: ME83
   • EF-2.4.4 → TM2: SJ00, Biomed: 5A11
   • EA-3 → TM2: SB00, Biomed: CA22

✅ Generated FHIR CodeSystem with 5 concepts
✅ Saved CodeSystem to fhir-output/namaste-codesystem.json
✅ Generated FHIR ConceptMap with 5 concept mappings
✅ Saved ConceptMap to fhir-output/namaste-conceptmap.json

🎉 Terminology ingestion completed successfully!
```

### UI Mode (User Interface)

The web interface (`ui/pages/terminology-ingestion.html`) provides equivalent functionality with an intuitive user experience:

#### Features
- **Dual Mode Interface**: Toggle between CLI documentation and interactive UI
- **Drag & Drop Upload**: Easy CSV file upload with drag-and-drop support
- **Real-time Processing**: Immediate parsing and FHIR resource generation
- **Interactive Results**: Tabbed interface showing data summary, CodeSystem, and ConceptMap
- **JSON Preview**: Full FHIR resource previews with syntax highlighting

#### Access
Navigate to: `/ui/pages/terminology-ingestion.html`

## FHIR Resources Generated

### CodeSystem Resource
```json
{
  "resourceType": "CodeSystem",
  "id": "namaste-terminology",
  "url": "http://ayush.gov.in/namaste",
  "version": "1.0.0",
  "name": "NAMASTE",
  "title": "NAMASTE Traditional Medicine Terminology",
  "status": "active",
  "experimental": false,
  "publisher": "Ministry of AYUSH, Government of India",
  "description": "NAMASTE (National AYUSH Morbidity and Standardized Terminologies Electronic) terminology system for traditional medicine",
  "content": "complete",
  "concept": [
    {
      "code": "AAE-16",
      "display": "Sandhigatvata",
      "definition": "Vitiated Vata in Sandhi"
    }
    // ... additional concepts
  ]
}
```

### ConceptMap Resource
```json
{
  "resourceType": "ConceptMap",
  "id": "namaste-to-icd11",
  "url": "http://example.com/namaste-to-icd11",
  "version": "1.0.0",
  "name": "NamasteToICD11",
  "title": "NAMASTE to ICD-11 Concept Map",
  "status": "active",
  "sourceUri": "http://ayush.gov.in/namaste",
  "targetUri": "http://hl7.org/fhir/sid/icd-11",
  "group": [
    {
      "source": "http://ayush.gov.in/namaste",
      "target": "http://hl7.org/fhir/sid/icd-11",
      "element": [
        {
          "code": "AAE-16",
          "display": "Sandhigatvata",
          "target": [
            {
              "code": "SP00",
              "display": "ICD-11 TM2: SP00",
              "equivalence": "equivalent",
              "comment": "Traditional Medicine 2 (TM2) mapping"
            },
            {
              "code": "FA01",
              "display": "ICD-11 Biomedicine: FA01",
              "equivalence": "equivalent",
              "comment": "Biomedicine mapping"
            }
          ]
        }
        // ... additional mappings
      ]
    }
  ]
}
```

## Input CSV Format

The tool expects NAMASTE CSV files with the following structure:

| Column | Description | Example |
|--------|-------------|---------|
| Patient_ID | Unique patient identifier | C001 |
| Age | Patient age | 25 |
| Gender | Patient gender | M/F |
| Disease | Traditional medicine disease name | Sandhigatvata |
| Code | NAMASTE terminology code | AAE-16 |
| Short_Definition | Disease definition | Vitiated Vata in Sandhi |
| State | Geographic location | Karnataka |
| Date_of_Visit | Visit date | 2025-06-01 |

## ICD-11 Mappings

The system includes predefined mappings for common NAMASTE codes:

| NAMASTE Code | Disease | ICD-11 TM2 | ICD-11 Biomedicine |
|--------------|---------|------------|-------------------|
| AAE-16 | Sandhigatvata | SP00 | FA01 |
| AA | Vatavyadhi | SP10 | FA20 |
| EE-3 | Arsha | SL01 | ME83 |
| EF-2.4.4 | Madhumeha/Kshaudrameha | SJ00 | 5A11 |
| EA-3 | Kasa | SB00 | CA22 |

## Technical Implementation

### CLI Tool Architecture
- **Modular Design**: Object-oriented CLI class with separate methods for parsing, generation, and output
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Validation**: Input validation and data integrity checks
- **Flexible Output**: Support for single files or directory-based output

### UI Interface Architecture
- **Apple-Style Design**: Professional typography and visual hierarchy
- **Responsive Layout**: Mobile-optimized interface with responsive grid
- **Interactive Elements**: Drag-and-drop, tabbed navigation, and real-time processing
- **Client-Side Processing**: JavaScript-based CSV parsing and FHIR resource generation

### Data Processing
1. **CSV Parsing**: Robust CSV parsing with header detection and validation
2. **Duplicate Handling**: Automatic deduplication based on NAMASTE codes
3. **ICD-11 Mapping**: Automatic mapping to ICD-11 TM2 and Biomedicine codes
4. **FHIR Compliance**: Standards-compliant FHIR resource generation

## Integration with Existing System

### Backend Integration
The CLI tool complements the existing FastAPI backend (`main.py`) by providing:
- Standalone processing capabilities
- Batch processing for large datasets
- System integration support for automated workflows

### Frontend Integration
The UI interface integrates with the existing use-case presentation by:
- Consistent design language and typography
- Navigation links from the main presentation
- Shared architectural patterns and user experience flows

## Use Cases

### Healthcare Organizations
- **Data Migration**: Convert legacy NAMASTE data to FHIR-compliant resources
- **System Integration**: Generate terminology resources for EHR systems
- **Compliance**: Ensure standards compliance for government reporting

### Research Institutions
- **Data Analysis**: Generate structured terminology for research studies
- **Cross-System Interoperability**: Enable data sharing between research platforms
- **Evidence Generation**: Support evidence-based traditional medicine research

### Government Agencies
- **Policy Development**: Create standardized terminology for regulatory frameworks
- **Quality Assurance**: Validate terminology consistency across systems
- **International Collaboration**: Enable data sharing with WHO and other organizations

## Future Enhancements

1. **Extended Mappings**: Support for additional ICD-11 categories and SNOMED CT
2. **Validation Rules**: Enhanced validation for terminology consistency
3. **Bulk Processing**: Support for processing multiple CSV files simultaneously
4. **API Integration**: Direct integration with WHO ICD-11 API for real-time validation
5. **Export Formats**: Additional output formats (XML, RDF, etc.)

## Testing and Validation

Both CLI and UI modes have been tested with:
- Sample NAMASTE dataset (50 records, 5 unique codes)
- FHIR resource validation against official schemas
- Cross-platform compatibility (Windows, macOS, Linux)
- Mobile and desktop browser compatibility
- Accessibility compliance (WCAG AA standards)

## Support and Documentation

For technical support and additional documentation:
- Review the inline help: `python namaste_cli.py --help`
- Check the UI interface tooltips and guidance
- Refer to FHIR documentation for resource specifications
- Contact the development team for integration assistance