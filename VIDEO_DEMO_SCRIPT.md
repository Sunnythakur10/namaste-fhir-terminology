# Video Demonstration Script: NAMASTE-FHIR Analytics System

## Video Title: "Ministry of Ayush Digital Health Surveillance - Live API Demonstration"

### Scene 1: Introduction (0:00 - 0:30)
**Screen:** Dashboard homepage with analytics chart visible
**Narration:** 
"Welcome to the NAMASTE-FHIR morbidity analytics system demonstration for the Ministry of Ayush. This system bridges traditional Ayurvedic medicine with modern WHO ICD-11 standards, enabling real-time health surveillance across India."

**Visual Elements:**
- Show the main dashboard with disease distribution chart
- Highlight key metrics: 50 patients, 6 diseases, 9 states, 100% ICD-11 mapping

### Scene 2: Disease Analytics Overview (0:30 - 1:00)
**Screen:** Focus on the disease distribution chart
**Narration:**
"The system tracks traditional Ayurvedic diagnoses in real-time. Here we see Sandhigatvata and Kasa leading with 10 patients each, followed by Madhumeha - the traditional term for diabetes - with 9 patients. Each diagnosis automatically maps to WHO ICD-11 codes."

**Visual Elements:**
- Point to each bar in the chart
- Highlight the Madhumeha (Diabetes) bar in green

### Scene 3: Live API Demonstration - Search (1:00 - 1:45)
**Screen:** API demonstration section
**Narration:**
"Let's demonstrate the intelligent search functionality. When a healthcare provider searches for 'Diabetes', the system instantly recognizes this as 'Madhumeha/Kshaudrameha' in traditional terminology."

**Actions:**
1. Click "🔍 Search 'Diabetes'" button
2. Show the JSON response updating with timestamp
3. Highlight the mapping: TM2: SJ00, Biomedicine: 5A11

**API Response Highlight:**
```json
{
  "namaste_code": "EF-2.4.4",
  "display_name": "Madhumeha/Kshaudrameha",
  "definition": "Diabetes Mellitus",
  "mappings": {
    "icd11_tm2": "SJ00",
    "icd11_biomedicine": "5A11"
  },
  "confidence_score": 100
}
```

### Scene 4: Analytics API Call (1:45 - 2:15)
**Screen:** Analytics endpoint demonstration
**Narration:**
"The analytics endpoint provides comprehensive morbidity statistics for Ministry surveillance. This FHIR-compliant Observation resource shows disease distribution, geographic patterns, and ICD-11 mapping statistics."

**Actions:**
1. Click "📈 Get Analytics" button
2. Show the JSON response with disease counts
3. Highlight state-wise distribution data

**Key Data Points:**
- by_disease: Shows patient counts per traditional diagnosis
- by_state: Geographic distribution across Indian states
- by_icd11_tm2 & by_icd11_biomed: WHO standard mappings

### Scene 5: FHIR ValueSet Lookup (2:15 - 2:45)
**Screen:** ValueSet lookup demonstration
**Narration:**
"The FHIR-compliant ValueSet expansion endpoint demonstrates healthcare interoperability. This standardized format enables integration with existing Electronic Health Record systems."

**Actions:**
1. Click "🏥 ValueSet Lookup" button
2. Show FHIR ValueSet structure
3. Highlight extension fields with ICD-11 mappings

### Scene 6: Real API Testing with cURL (2:45 - 3:30)
**Screen:** Terminal/Command line demonstration
**Narration:**
"Let's verify the system with live API calls. First, we'll get an authentication token, then search for diabetes."

**Commands Shown:**
```bash
# Get authentication token
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test"

# Search for diabetes
curl -X POST "http://localhost:8000/search" \
  -H "Authorization: Bearer mock-abha-token" \
  -H "Content-Type: application/json" \
  -d '{"query": "Diabetes", "limit": 5}'

# Get analytics data
curl -X GET "http://localhost:8000/analytics" \
  -H "Authorization: Bearer mock-abha-token"
```

### Scene 7: Ministry Benefits Highlight (3:30 - 4:00)
**Screen:** Benefits section of dashboard
**Narration:**
"For the Ministry of Ayush, this system provides enhanced surveillance capabilities, intelligent search with fuzzy matching for Sanskrit terms, and seamless integration between traditional and modern medicine standards."

**Visual Elements:**
- Show the two-column benefits layout
- Highlight key capabilities:
  - Real-time disease pattern tracking
  - Geographic morbidity mapping
  - Bidirectional NAMASTE↔ICD-11 translation
  - Auto-complete suggestions

### Scene 8: Key Achievement Summary (4:00 - 4:30)
**Screen:** Achievement highlight section
**Narration:**
"The key achievement is creating a seamless bridge between traditional and modern medicine. Healthcare providers can work with familiar Ayurvedic terms like 'Madhumeha' while the system automatically ensures global health standard compliance through ICD-11 mapping."

**Visual Elements:**
- Highlight the green achievement box
- Show the specific mapping: "Madhumeha" → TM2: SJ00, Biomedicine: 5A11

### Scene 9: Conclusion & Next Steps (4:30 - 5:00)
**Screen:** Return to main dashboard
**Narration:**
"This NAMASTE-FHIR system positions the Ministry of Ayush as a leader in traditional medicine digitization, supporting evidence-based healthcare delivery while preserving ancient Ayurvedic knowledge. The system is ready for deployment and integration with existing healthcare infrastructure."

**Final Visual:**
- Show system status: "✅ System Active - Real-time WHO ICD-11 Integration"
- Display total metrics one final time

---

## Technical Setup for Video Recording

### Required Tools:
- Screen recording software (OBS Studio recommended)
- Terminal access for API demonstrations
- Web browser with dashboard loaded

### Pre-recording Checklist:
1. ✅ FastAPI server running on localhost:8000
2. ✅ HTTP server serving dashboard on localhost:3000
3. ✅ Dataset loaded with 50 patient records
4. ✅ All API endpoints tested and functional
5. ✅ Dashboard displaying correct metrics and charts

### API Endpoints to Demonstrate:
- POST /token (Authentication)
- POST /search (Enhanced search)
- GET /analytics (Morbidity statistics)
- POST /valueset-lookup (FHIR ValueSet)

### Expected Results:
- Diabetes search returns "Madhumeha/Kshaudrameha" with 100% confidence
- Analytics shows 50 patients across 6 diseases and 9 states
- All responses include proper ICD-11 TM2 and Biomedicine mappings
- FHIR ValueSet properly formatted with extensions

### Video Quality Guidelines:
- Resolution: 1920x1080 (Full HD)
- Frame Rate: 30 FPS
- Audio: Clear narration with no background noise
- Duration: 4-5 minutes maximum
- Format: MP4 for maximum compatibility

### Post-Production Notes:
- Add captions for accessibility
- Include Ministry of Ayush branding if available
- Highlight important JSON fields with visual indicators
- Add smooth transitions between scenes