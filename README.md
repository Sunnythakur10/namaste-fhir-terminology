# NAMASTE-FHIR Terminology Service

> Bridging Traditional Ayurvedic Medicine with Modern Healthcare Standards

[![FHIR R4](https://img.shields.io/badge/FHIR-R4-blue)](http://hl7.org/fhir/)
[![ICD-11](https://img.shields.io/badge/ICD--11-WHO-green)](https://icd.who.int/browse11)
[![Python](https://img.shields.io/badge/Python-3.9+-yellow)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-teal)](https://fastapi.tiangolo.com/)

## Overview

NAMASTE-FHIR is a production-ready microservice that enables seamless integration between traditional Ayurvedic medicine terminology and modern healthcare systems. It provides intelligent mapping between the NAMASTE (National Ayush Morbidity and Standardized Terminologies Electronic) code system and WHO's ICD-11 classification, supporting both Traditional Medicine Module 2 (TM2) and Biomedicine codes.

### Key Features

🔍 **Intelligent Search**
- Fuzzy string matching for Sanskrit term variations
- Multi-field search across codes, diseases, and definitions
- Confidence-scored results (0-100%)
- Auto-complete suggestions

📊 **Real-time Analytics**
- Population health surveillance dashboard
- Disease distribution analysis
- Geographic morbidity tracking
- FHIR Observation resources

🔐 **Enterprise Security**
- OAuth 2.0 ABHA token authentication
- Comprehensive audit logging
- CORS support for web integration

🏥 **FHIR R4 Compliance**
- CodeSystem resources
- ConceptMap for bidirectional mapping
- ValueSet expansion endpoint
- Production-ready healthcare interoperability

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/Sunnythakur10/namaste-fhir-terminology.git
cd namaste-fhir-terminology

# Install dependencies
pip install -r requirements.txt
```

### Running the Service

```bash
# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Access the API documentation
# Open http://localhost:8000/docs in your browser
```

### Using the Dashboard

```bash
# Start a simple HTTP server for the dashboard
python -m http.server 3000

# Access the analytics dashboard
# Open http://localhost:3000/ministry-demo-simple.html
```

## API Examples

### Authentication

```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test"
```

### Search for Disease Terms

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Authorization: Bearer mock-abha-token" \
  -H "Content-Type: application/json" \
  -d '{"query": "Diabetes", "limit": 5}'
```

**Response:**
```json
{
  "query": "Diabetes",
  "total_results": 1,
  "results": [
    {
      "namaste_code": "EF-2.4.4",
      "display_name": "Madhumeha/Kshaudrameha",
      "definition": "Diabetes Mellitus",
      "mappings": {
        "icd11_tm2": "SJ00",
        "icd11_biomedicine": "5A11"
      },
      "match_info": {
        "confidence_score": 100,
        "match_type": "exact"
      }
    }
  ]
}
```

### Get Analytics

```bash
curl -X GET "http://localhost:8000/analytics" \
  -H "Authorization: Bearer mock-abha-token"
```

### FHIR ValueSet Lookup

```bash
curl -X POST "http://localhost:8000/valueset-lookup" \
  -H "Authorization: Bearer mock-abha-token" \
  -H "Content-Type: application/json" \
  -d '{"search_text": "Diabetes"}'
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/token` | POST | OAuth2 authentication |
| `/search` | POST | Enhanced fuzzy search with confidence scoring |
| `/analytics` | GET | Real-time morbidity statistics (FHIR Observation) |
| `/valueset-lookup` | POST | FHIR ValueSet expansion |
| `/ingest` | POST | CSV dataset upload and processing |
| `/codesystem` | GET | NAMASTE CodeSystem resource |
| `/conceptmap` | GET | NAMASTE↔ICD-11 mapping resource |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
│          (Web Dashboard, Mobile Apps, EHR Systems)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS + OAuth 2.0
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Microservice                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Search     │  │  Analytics   │  │  FHIR APIs   │     │
│  │   Engine     │  │  Dashboard   │  │  (R4)        │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Data Processing
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Terminology Mapping                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  NAMASTE Codes  ←→  ICD-11 TM2 + Biomedicine        │  │
│  │  Fuzzy Matching │  Confidence Scoring │  Validation  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Core Technologies
- **FastAPI**: Modern Python web framework with async support
- **Uvicorn**: Lightning-fast ASGI server
- **Pydantic**: Data validation using Python type annotations
- **Pandas**: Data manipulation and analytics

### Healthcare Standards
- **FHIR R4**: HL7 Fast Healthcare Interoperability Resources
- **ICD-11**: WHO International Classification of Diseases
- **OAuth 2.0**: Industry-standard authentication protocol

### Search & Matching
- **FuzzyWuzzy**: Fuzzy string matching
- **Python-Levenshtein**: Fast string similarity calculations

## Data Model

### NAMASTE Code Structure
```
EF-2.4.4
│  │ │ │
│  │ │ └─ Sub-category
│  │ └─── Category
│  └───── Section
└─────── Chapter
```

### ICD-11 Mapping
Each NAMASTE code maps to:
- **ICD-11 TM2**: Traditional Medicine Module 2 code
- **ICD-11 Biomedicine**: Standard biomedical classification

## Use Cases

### 1. Clinical Decision Support
Healthcare providers can search using common medical terms and receive appropriate Ayurvedic terminology with international codes.

### 2. Population Health Surveillance
Ministry of Ayush officials can track disease trends across states and demographics using standardized terminology.

### 3. EHR Integration
Ayurvedic hospitals can export FHIR-compliant data to integrate with modern hospital information systems.

### 4. Research & Analytics
Researchers can query traditional medicine data using standard ICD-11 codes for international collaboration.

## Project Structure

```
namaste-fhir-terminology/
├── main.py                          # FastAPI application
├── namaste_cli.py                   # Command-line interface
├── icd11_client.py                  # ICD-11 API integration
├── requirements.txt                 # Python dependencies
├── dataset/                         # NAMASTE terminology data
├── ministry-demo-simple.html        # Analytics dashboard
├── PROJECT_DESCRIPTION.md           # Comprehensive project documentation
├── LINKEDIN_POST.md                 # LinkedIn post templates
├── MINISTRY_REPORT.md              # Ministry presentation report
└── VIDEO_DEMO_SCRIPT.md            # Demo video script
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Documentation

- **[Project Description](PROJECT_DESCRIPTION.md)**: Comprehensive technical documentation for portfolio
- **[LinkedIn Post](LINKEDIN_POST.md)**: LinkedIn post templates and portfolio entry guidance
- **[Ministry Report](MINISTRY_REPORT.md)**: Detailed report for Ministry of Ayush
- **[Demo Script](VIDEO_DEMO_SCRIPT.md)**: Video demonstration script

## License

This project is developed for healthcare digitization and traditional medicine preservation.

## Contact

For questions or collaboration opportunities, please reach out via:
- GitHub: [@Sunnythakur10](https://github.com/Sunnythakur10)
- Project Issues: [GitHub Issues](https://github.com/Sunnythakur10/namaste-fhir-terminology/issues)

## Acknowledgments

- **Ministry of Ayush**: For traditional medicine standardization initiatives
- **WHO**: For ICD-11 classification system
- **HL7**: For FHIR healthcare interoperability standards

---

**Status**: ✅ Production-Ready | Active Development

**Version**: 1.0.0

**Last Updated**: October 2024
