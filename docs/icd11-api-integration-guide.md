# WHO ICD-11 API Integration Guide

## Overview

The NAMASTE-FHIR Terminology Bridge now includes complete WHO ICD-11 API integration that fetches and caches real ICD-11 Traditional Medicine 2 (TM2) and Biomedicine codes directly from the WHO ICD API, providing enhanced mapping capabilities for cross-referencing with NAMASTE terminology codes.

## Features

### 🌐 Live API Integration
- **Real-time data fetching** from WHO ICD-11 API
- **Automatic authentication** with WHO credentials
- **Smart caching** to minimize API calls and improve performance
- **Search functionality** for finding relevant ICD-11 codes

### 🔄 Enhanced Fallback System
- **Graceful degradation** when API is unavailable
- **Enhanced static mappings** based on WHO ICD-11 documentation
- **Seamless mode switching** between live API and fallback
- **Comprehensive error handling** and user feedback

### 📊 FHIR Resource Enhancement
- **Metadata enrichment** with mapping source information
- **Enhanced ConceptMap** resources with detailed mapping provenance
- **Version tracking** for API-based vs fallback mappings
- **Standards compliance** with FHIR R4 specifications

## API Integration Architecture

### Authentication Flow
```
1. Client credentials grant (OAuth 2.0)
2. Token caching with automatic refresh
3. Bearer token authentication for all API calls
4. Graceful handling of authentication failures
```

### Data Fetching Strategy
```
1. Search ICD-11 for relevant terms per NAMASTE code
2. Fetch both TM2 and Biomedicine mappings
3. Cache results locally with configurable TTL
4. Merge with existing terminology service
```

### Caching System
- **Local file cache** with JSON storage
- **Configurable cache duration** (default: 24 hours)
- **Cache validation** with timestamp checking
- **Automatic cache refresh** when expired

## Configuration

### Environment Variables
```bash
# WHO ICD-11 API Credentials
ICD_CLIENT_ID=your_client_id_here
ICD_CLIENT_SECRET=your_client_secret_here

# API Configuration (optional)
ICD_API_BASE_URL=https://id.who.int
ICD_API_VERSION=release/11/2024-01
CACHE_DURATION_HOURS=24
```

### Setup Instructions
1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your WHO ICD-11 API credentials
   ```

3. **Test Integration**
   ```bash
   python namaste_cli.py --test-api
   ```

## CLI Usage Examples

### Basic Operations with API
```bash
# Generate FHIR resources with live WHO ICD-11 API
python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --all --output-dir fhir-output/

# Display summary with API mappings
python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --summary

# Test API connectivity
python namaste_cli.py --test-api
```

### Fallback Mode Operations
```bash
# Use enhanced fallback mappings (disable API)
python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --all --no-api

# Generate resources with fallback mode
python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --conceptmap --output conceptmap.json --no-api
```

### Advanced Options
```bash
# Verbose output with API details
python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --summary --verbose

# Generate only CodeSystem with API enhancement
python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --codesystem --output enhanced-codesystem.json
```

## UI Integration

### Features
- **Dual-mode interface** supporting both CLI documentation and interactive UI
- **Real-time API status** display showing connection status
- **Enhanced result displays** with mapping source attribution
- **Professional file upload** with drag-and-drop functionality
- **Tabbed results interface** showing data summary, CodeSystem, and ConceptMap

### API Integration Status
The UI automatically detects and displays:
- **Live API mode**: When WHO ICD-11 API is connected and responding
- **Enhanced Fallback mode**: When using improved static mappings
- **API connectivity status**: Real-time status of WHO API connection
- **Mapping source attribution**: Clear indication of data sources for each mapping

## Technical Implementation

### ICD11APIClient Class
```python
class ICD11APIClient:
    - authenticate(): OAuth 2.0 authentication with WHO
    - fetch_tm2_codes(): Retrieve TM2 terminology
    - fetch_biomedicine_codes(): Retrieve biomedicine codes
    - search_codes(): Search functionality
    - get_enhanced_namaste_mappings(): Generate enhanced mappings
```

### Enhanced CLI Tool
```python
class NAMASTETerminologyCLI:
    - Automatic API integration initialization
    - Fallback mode for offline operation
    - Enhanced FHIR resource generation
    - Mapping source tracking and attribution
```

### Caching Strategy
- **File-based caching** in `cache/` directory
- **MD5-based cache keys** for efficient lookup
- **Timestamp validation** for cache expiry
- **Automatic cleanup** of expired cache entries

## FHIR Resource Enhancements

### Enhanced CodeSystem
```json
{
  "resourceType": "CodeSystem",
  "version": "2.0.0",
  "title": "NAMASTE Traditional Medicine Terminology (WHO ICD-11 Enhanced)",
  "property": [
    {
      "code": "mapping_source",
      "description": "Source of the ICD-11 mapping",
      "type": "string"
    }
  ],
  "concept": [
    {
      "code": "AAE-16",
      "property": [
        {
          "code": "mapping_source",
          "valueString": "WHO_ICD11_API"
        }
      ]
    }
  ]
}
```

### Enhanced ConceptMap
```json
{
  "resourceType": "ConceptMap",
  "version": "2.0.0",
  "title": "NAMASTE to ICD-11 Enhanced Concept Map (WHO API Integrated)",
  "group": [
    {
      "element": [
        {
          "target": [
            {
              "comment": "Traditional Medicine 2 (TM2) mapping - Source: WHO_ICD11_API"
            }
          ]
        }
      ]
    }
  ]
}
```

## Error Handling

### Network Issues
- **Graceful degradation** to fallback mode
- **Clear user feedback** about connectivity status
- **Retry mechanisms** with exponential backoff
- **Timeout handling** for slow connections

### Authentication Failures
- **Clear error messages** for credential issues
- **Fallback to static mappings** when auth fails
- **Logging** of authentication attempts
- **Guidance** for credential setup

### API Rate Limiting
- **Automatic retry** with appropriate delays
- **Cache utilization** to minimize API calls
- **Batch processing** for efficiency
- **Progress indicators** for long operations

## Performance Optimization

### Caching Benefits
- **Reduced API calls** through intelligent caching
- **Faster response times** for repeated operations
- **Offline capability** with cached data
- **Bandwidth savings** for development environments

### Search Optimization
- **Targeted searches** using relevant medical terms
- **Result filtering** to focus on best matches
- **Deduplication** of search results
- **Efficient data structures** for fast lookup

## Development and Testing

### Testing the Integration
```bash
# Test API connectivity
python icd11_client.py

# Test CLI with API
python namaste_cli.py --test-api

# Test with actual dataset
python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --summary
```

### Development Mode
- Set `ICD_CLIENT_ID` and `ICD_CLIENT_SECRET` for live API testing
- Use `--no-api` flag to develop with fallback mappings
- Monitor cache directory for API response caching
- Check logs for detailed API interaction information

## Deployment Considerations

### Production Setup
1. **Secure credential storage** using environment variables or secrets management
2. **Cache directory permissions** for read/write access
3. **Network connectivity** to WHO ICD API endpoints
4. **Monitoring** of API usage and rate limits

### Scaling Considerations
- **Shared cache** for multiple instances
- **Load balancing** for API requests
- **Cache warming** strategies for improved performance
- **Fallback coordination** across instances

## Troubleshooting

### Common Issues
1. **Authentication Errors**: Verify client ID and secret
2. **Network Connectivity**: Check firewall and DNS settings
3. **Cache Permissions**: Ensure write access to cache directory
4. **Rate Limiting**: Monitor API usage and implement delays

### Debug Commands
```bash
# Verbose API testing
python namaste_cli.py --test-api --verbose

# Force API refresh (clear cache)
rm -rf cache/ && python namaste_cli.py --test-api

# Test with fallback only
python namaste_cli.py --input dataset/namaste_dummy_dataset.csv --summary --no-api
```

## Future Enhancements

### Planned Features
- **Real-time sync** with WHO ICD-11 updates
- **Advanced search algorithms** for better mapping accuracy
- **Machine learning** for mapping quality improvement
- **Multi-language support** for international deployment

### API Expansion
- **Additional WHO endpoints** for comprehensive coverage
- **SNOMED CT integration** for broader terminology mapping
- **LOINC integration** for laboratory and clinical observations
- **Custom terminology** support for organization-specific codes

## Support and Maintenance

### Monitoring
- **API health checks** with automated alerts
- **Cache utilization** metrics and optimization
- **Mapping accuracy** tracking and improvement
- **Performance metrics** for optimization

### Updates
- **Regular API endpoint** updates as WHO releases new versions
- **Mapping refinement** based on user feedback and clinical validation
- **Security updates** for credential handling and data protection
- **Performance improvements** based on usage patterns

---

This WHO ICD-11 API integration provides a robust foundation for real-time terminology mapping while maintaining reliability through enhanced fallback mechanisms. The implementation ensures that the NAMASTE-FHIR Terminology Bridge can operate effectively in both connected and offline environments, providing consistent and accurate terminology mappings for healthcare interoperability.