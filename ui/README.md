# NAMASTE-FHIR Terminology UI

This directory contains the UI components for the NAMASTE-FHIR Terminology Translation project.

## Directory Structure

```
ui/
├── assets/
│   ├── css/         # CSS stylesheets
│   ├── js/          # JavaScript files
│   └── images/      # Images and icons
├── components/      # Reusable UI components
└── pages/           # HTML pages for different workflows
```

## Pages

- **landing.html**: Modern landing page with feature overview
- **doctor-sandbox.html**: Advanced interface for doctors to search and add diagnoses with dual-coding
- **researcher-workflow.html**: Tools for researchers to analyze morbidity data
- **insurance-workflow.html**: Workflow for insurance claim verification
- **api-docs.html**: API documentation

## Features

- NAMASTE and ICD-11 terminology search
- Autocomplete diagnosis search
- Dual coding display (NAMASTE + ICD-11)
- Problem list management
- FHIR bundle export
- Analytics visualization
- Insurance claim verification

## Development

This is a prototype UI for demonstration purposes. It uses HTML, CSS, and vanilla JavaScript with no build process required.

To serve the UI locally, you can use any simple HTTP server. For example:

```bash
python -m http.server 8000
```

Then navigate to `http://localhost:8000/ui/pages/landing.html` in your browser.

## Implementation Notes

- The UI is designed to demonstrate the functionality of the NAMASTE-FHIR Terminology Translation API
- Mock data is used for demonstration purposes
- In a production environment, this would connect to the actual API endpoints
