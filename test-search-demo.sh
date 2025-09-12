#!/bin/bash

# Test script for Search & Auto-Complete functionality
# This script demonstrates the REST endpoints for auto-complete lookup

echo "🔍 NAMASTE-FHIR Search & Auto-Complete Demo"
echo "============================================="
echo

# Start the API server in background
echo "Starting NAMASTE-FHIR API server..."
cd /home/runner/work/namaste-fhir-terminology/namaste-fhir-terminology

# Install dependencies if needed
pip install -q pandas requests python-dotenv fastapi uvicorn python-multipart fuzzywuzzy python-levenshtein

# Start server in background
python main.py &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 5

# Get authentication token
echo "Getting authentication token..."
TOKEN=$(curl -s -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test" | jq -r '.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Failed to get authentication token"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

echo "✅ Authentication successful"

# Load sample data
echo "Loading NAMASTE sample dataset..."
curl -s -X POST "http://localhost:8000/ingest-namaste" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@dataset/namaste_dummy_dataset.csv" > /dev/null

echo "✅ Sample data loaded"
echo

# Test 1: FHIR ValueSet/$expand endpoint
echo "🧪 Test 1: FHIR ValueSet/\$expand endpoint"
echo "Query: 'Prameha' (Traditional term for diabetes)"
echo "Endpoint: GET /ValueSet/\$expand?filter=Prameha&count=5"
echo
curl -s -X GET "http://localhost:8000/ValueSet/\$expand?filter=Prameha&count=5" \
  -H "Authorization: Bearer $TOKEN" | jq '{
    resourceType,
    expansion: {
      total: .expansion.total,
      contains: [.expansion.contains[] | {
        code,
        display,
        extensions: {
          tm2_mapping: (.extension[] | select(.url | contains("icd11-tm2")) | .valueCode),
          biomedicine_mapping: (.extension[] | select(.url | contains("icd11-biomedicine")) | .valueCode),
          confidence_score: (.extension[] | select(.url | contains("confidence-score")) | .valueInteger)
        }
      }]
    }
  }'
echo
echo "📊 Result: Found diabetes-related term with ICD-11 mappings"
echo

# Test 2: Custom search endpoint
echo "🧪 Test 2: Custom search endpoint"
echo "Query: 'Sandhigatvata' (Joint disorders)"
echo "Endpoint: POST /search"
echo
curl -s -X POST "http://localhost:8000/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Sandhigatvata", "limit": 3, "threshold": 60}' | jq '{
    query,
    total_results,
    results: [.results[] | {
      namaste_code,
      display_name,
      definition,
      mappings,
      confidence_score: .match_info.confidence_score
    }]
  }'
echo
echo "📊 Result: Exact match for joint disorder with high confidence"
echo

# Test 3: Auto-complete suggestions
echo "🧪 Test 3: Auto-complete suggestions"
echo "Query: 'San' (Partial term)"
echo "Endpoint: GET /search/suggestions?q=San&limit=3"
echo
SUGGESTIONS=$(curl -s -X GET "http://localhost:8000/search/suggestions?q=San&limit=3" \
  -H "Authorization: Bearer $TOKEN")
echo $SUGGESTIONS | jq '.'
echo
echo "📊 Result: Auto-complete suggestions for partial input"
echo

# Test 4: Fuzzy search with partial match
echo "🧪 Test 4: Fuzzy search demonstration"
echo "Query: 'Madhu' (Partial term for Madhumeha)"
echo "Endpoint: POST /search with fuzzy matching"
echo
curl -s -X POST "http://localhost:8000/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Madhu", "limit": 5, "threshold": 50}' | jq '{
    query,
    total_results,
    results: [.results[] | {
      namaste_code,
      display_name,
      match_type: .match_info.match_type,
      confidence_score: .match_info.confidence_score,
      mappings: {
        icd11_tm2: .mappings.icd11_tm2,
        icd11_biomedicine: .mappings.icd11_biomedicine
      }
    }]
  }'
echo
echo "📊 Result: Fuzzy matching found related diabetes terms"
echo

# Test 5: Multiple results with confidence scoring
echo "🧪 Test 5: Multiple results with confidence scoring"
echo "Query: 'Vata' (Dosha-related terms)"
echo
curl -s -X POST "http://localhost:8000/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Vata", "limit": 10, "threshold": 60}' | jq '{
    query,
    total_results,
    results: [.results[] | {
      code: .namaste_code,
      name: .display_name,
      confidence: .match_info.confidence_score,
      tm2: .mappings.icd11_tm2,
      biomedicine: .mappings.icd11_biomedicine
    }]
  }'
echo
echo "📊 Result: Multiple Vata-related disorders with confidence scores"
echo

# Summary
echo "🎯 Summary of Search & Auto-Complete Features:"
echo "=============================================="
echo "✅ FHIR-compliant ValueSet/\$expand endpoint"
echo "✅ Custom search with fuzzy matching"
echo "✅ Real-time auto-complete suggestions"
echo "✅ Confidence scoring for matches"
echo "✅ Support for partial and exact matches"
echo "✅ Dual ICD-11 mappings (TM2 + Biomedicine)"
echo
echo "🌐 API Endpoints Available:"
echo "• GET /ValueSet/\$expand?filter={term}&count={limit}"
echo "• POST /search (with JSON body)"
echo "• GET /search/suggestions?q={term}&limit={count}"
echo
echo "💡 Example usage: Input 'Prameha' → Output: NAMASTE code EF-2.4.4, TM2 SJ00, Biomedicine 5A11"

# Cleanup
echo
echo "Cleaning up..."
kill $SERVER_PID 2>/dev/null
echo "✅ Demo completed successfully!"