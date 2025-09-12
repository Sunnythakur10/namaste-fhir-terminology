from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Body, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import requests
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from fuzzywuzzy import fuzz, process
import re

# Setup logging for audit trails (EHR compliance)
logging.basicConfig(filename='audit.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(title="NAMASTE-ICD11 TM2 Micro-Service")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/token")
def get_token(form_data: OAuth2PasswordRequestForm = Depends()):
    return {"access_token": "mock-abha-token", "token_type": "bearer"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Mock ABHA token validation
def verify_abha_token(token: str = Depends(oauth2_scheme)):
    if token != "mock-abha-token":
        raise HTTPException(status_code=401, detail="Invalid ABHA token")
    logging.info(f"Access granted with token: {token}")
    return token

# Mock ICD-11 mappings based on NEW dummy dataset codes (replace with real WHO API)
icd_mappings = {
    "AAE-16": {"tm2": "SP00", "biomed": "FA01", "name": "Sandhigatvata"},  # Mock for Vitiated Vata in Sandhi (Osteoarthritis-like)
    "AA": {"tm2": "SP10", "biomed": "FA20", "name": "Vatavyadhi"},  # Mock for Vata disorders
    "EE-3": {"tm2": "SL01", "biomed": "ME83", "name": "Arsha"},  # Mock for Hemorrhoids
    "EF-2.4.4": {"tm2": "SJ00", "biomed": "5A11", "name": "Madhumeha/Kshaudrameha"},  # Mock for Diabetes
    "EA-3": {"tm2": "SB00", "biomed": "CA22", "name": "Kasa"}  # Mock for Cough
    # Add more if new codes appear in future data
}

# Global DataFrame to store ingested data
df_namaste = pd.DataFrame()

# Update FHIR resources dynamically (updated for new columns: Code, Disease, Short_Definition)
def update_fhir_resources():
    global namaste_codesystem, concept_map
    namaste_codesystem = {
        "resourceType": "CodeSystem",
        "url": "http://ayush.gov.in/namaste",
        "version": "1.0.0",
        "name": "NAMASTE",
        "status": "active",
        "content": "complete",
        "concept": [
            {"code": row["Code"], "display": row["Disease"], "definition": row["Short_Definition"]}
            for _, row in df_namaste.iterrows()
        ]
    }
    concept_map = {
        "resourceType": "ConceptMap",
        "url": "http://example.com/namaste-to-icd11",
        "version": "1.0.0",
        "name": "NamasteToICD11",
        "status": "active",
        "sourceUri": "http://ayush.gov.in/namaste",
        "targetUri": "http://hl7.org/fhir/sid/icd-11",
        "group": [
            {
                "source": "http://ayush.gov.in/namaste",
                "target": "http://hl7.org/fhir/sid/icd-11",
                "element": [
                    {
                        "code": row["Code"],
                        "target": [
                            {"code": row["icd11_tm2_code"], "equivalence": "equivalent", "comment": "TM2"},
                            {"code": row["icd11_biomed_code"], "equivalence": "equivalent", "comment": "Biomedicine"}
                        ]
                    } for _, row in df_namaste.iterrows()
                ]
            }
        ]
    }

# Mock ICD-11 API sync (no changes)
def get_icd_token():
    return "mock-token"

def sync_icd_tm2(query: str = "traditional medicine"):
    token = get_icd_token()
    logging.info(f"Synced ICD data for query: {query}")
    return {"status": "mock-sync"}

# Ingest NAMASTE CSV and generate FHIR resources (updated for new CSV columns and UploadFile)
@app.post("/ingest-namaste")
async def ingest_namaste(file: UploadFile = File(...), token: str = Depends(verify_abha_token)):
    global df_namaste
    try:
        df_namaste = pd.read_csv(file.file)
        # Automatic mapping: Add ICD-11 columns based on Code
        df_namaste['icd11_tm2_code'] = df_namaste['Code'].map(lambda x: icd_mappings.get(x, {"tm2": "UNKNOWN"})["tm2"])
        df_namaste['icd11_biomed_code'] = df_namaste['Code'].map(lambda x: icd_mappings.get(x, {"biomed": "UNKNOWN"})["biomed"])
        update_fhir_resources()  # Regenerate CodeSystem and ConceptMap
        sync_icd_tm2()  # Sync on ingest
        logging.info("NAMASTE ingested and synced")
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Ingest failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ICD sync failed: {str(e)}")

# Enhanced Search & Auto-Complete Models
class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    include_fuzzy: Optional[bool] = True
    threshold: Optional[int] = 60  # Minimum fuzzy match score (0-100)

class AutoCompleteResponse(BaseModel):
    namaste_code: str
    display_name: str
    definition: str
    tm2_mapping: str
    biomedicine_mapping: str
    confidence_score: int  # Fuzzy match confidence (0-100)

# Legacy model for backward compatibility
class SearchQuery(BaseModel):
    term: str

# Enhanced search functionality
def fuzzy_search_terms(query: str, limit: int = 10, threshold: int = 60) -> List[Dict]:
    """
    Perform fuzzy search on NAMASTE terminology with auto-complete functionality
    Supports partial matching, synonyms, and traditional medicine terms
    """
    if df_namaste.empty:
        return []
    
    results = []
    query_lower = query.lower().strip()
    
    # Create searchable text combining Disease, Short_Definition, and Code
    df_namaste['searchable_text'] = (
        df_namaste['Disease'].astype(str) + ' ' + 
        df_namaste['Short_Definition'].astype(str) + ' ' + 
        df_namaste['Code'].astype(str)
    ).str.lower()
    
    # 1. Exact matches (highest priority)
    exact_matches = df_namaste[
        df_namaste['Disease'].str.lower().str.contains(query_lower, na=False, regex=False) |
        df_namaste['Short_Definition'].str.lower().str.contains(query_lower, na=False, regex=False) |
        df_namaste['Code'].str.lower().str.contains(query_lower, na=False, regex=False)
    ]
    
    for _, row in exact_matches.iterrows():
        results.append({
            'namaste_code': row['Code'],
            'display_name': row['Disease'],
            'definition': row['Short_Definition'],
            'tm2_mapping': row['icd11_tm2_code'],
            'biomedicine_mapping': row['icd11_biomed_code'],
            'confidence_score': 100,
            'match_type': 'exact'
        })
    
    # 2. Fuzzy matches for remaining results
    if len(results) < limit:
        remaining_limit = limit - len(results)
        
        # Get all unique searchable texts for fuzzy matching
        search_texts = df_namaste['searchable_text'].unique()
        
        # Use fuzzywuzzy for intelligent matching
        fuzzy_matches = process.extract(
            query_lower, 
            search_texts, 
            limit=remaining_limit * 2,  # Get more to filter
            scorer=fuzz.partial_ratio
        )
        
        for match_text, score in fuzzy_matches:
            if score >= threshold:
                # Find the row with this searchable text
                matched_rows = df_namaste[df_namaste['searchable_text'] == match_text]
                
                for _, row in matched_rows.iterrows():
                    # Avoid duplicates from exact matches
                    if not any(r['namaste_code'] == row['Code'] for r in results):
                        results.append({
                            'namaste_code': row['Code'],
                            'display_name': row['Disease'],
                            'definition': row['Short_Definition'],
                            'tm2_mapping': row['icd11_tm2_code'],
                            'biomedicine_mapping': row['icd11_biomed_code'],
                            'confidence_score': score,
                            'match_type': 'fuzzy'
                        })
                        
                        if len(results) >= limit:
                            break
            
            if len(results) >= limit:
                break
    
    # Sort by confidence score (descending)
    results.sort(key=lambda x: x['confidence_score'], reverse=True)
    
    return results[:limit]

# FHIR ValueSet/$expand endpoint for auto-complete lookup
@app.get("/ValueSet/$expand", response_model=Dict)
def valueset_expand(
    url: Optional[str] = Query(None, description="ValueSet canonical URL"),
    filter: Optional[str] = Query(None, description="Search filter term"),
    count: Optional[int] = Query(10, description="Maximum number of results"),
    token: str = Depends(verify_abha_token)
):
    """
    FHIR-compliant ValueSet expansion endpoint with auto-complete functionality.
    Supports queries like: /ValueSet/$expand?filter=Prameha&count=5
    """
    if not filter:
        raise HTTPException(status_code=400, detail="Filter parameter is required for search")
    
    # Perform enhanced search
    search_results = fuzzy_search_terms(filter, limit=count, threshold=60)
    
    # Format as FHIR ValueSet expansion
    expansion = {
        "resourceType": "ValueSet",
        "url": url or "http://ayush.gov.in/namaste/vs-all",
        "version": "1.0.0",
        "name": "NAMASTE_AutoComplete",
        "status": "active",
        "expansion": {
            "identifier": f"urn:uuid:search-{datetime.utcnow().isoformat()}",
            "timestamp": datetime.utcnow().isoformat(),
            "total": len(search_results),
            "parameter": [
                {"name": "filter", "valueString": filter},
                {"name": "count", "valueInteger": count}
            ],
            "contains": []
        }
    }
    
    for result in search_results:
        contains_entry = {
            "system": "http://ayush.gov.in/namaste",
            "code": result['namaste_code'],
            "display": result['display_name'],
            "designation": [
                {
                    "language": "en",
                    "value": result['definition']
                }
            ],
            "extension": [
                {
                    "url": "http://ayush.gov.in/namaste/extension/icd11-tm2",
                    "valueCode": result['tm2_mapping']
                },
                {
                    "url": "http://ayush.gov.in/namaste/extension/icd11-biomedicine",
                    "valueCode": result['biomedicine_mapping']
                },
                {
                    "url": "http://ayush.gov.in/namaste/extension/confidence-score",
                    "valueInteger": result['confidence_score']
                },
                {
                    "url": "http://ayush.gov.in/namaste/extension/match-type",
                    "valueString": result['match_type']
                }
            ]
        }
        expansion["expansion"]["contains"].append(contains_entry)
    
    logging.info(f"ValueSet expansion for filter '{filter}' returned {len(search_results)} results")
    return expansion

# Custom search endpoint with enhanced functionality
@app.post("/search", response_model=Dict)
def custom_search(request: SearchRequest, token: str = Depends(verify_abha_token)):
    """
    Custom search endpoint with advanced fuzzy matching and auto-complete.
    Example: POST /search {"query": "Prameha", "limit": 5, "threshold": 70}
    """
    search_results = fuzzy_search_terms(
        request.query, 
        limit=request.limit, 
        threshold=request.threshold
    )
    
    # Enhanced response format
    response = {
        "query": request.query,
        "total_results": len(search_results),
        "search_parameters": {
            "limit": request.limit,
            "include_fuzzy": request.include_fuzzy,
            "threshold": request.threshold
        },
        "timestamp": datetime.utcnow().isoformat(),
        "results": []
    }
    
    for result in search_results:
        formatted_result = {
            "namaste_code": result['namaste_code'],
            "display_name": result['display_name'],
            "definition": result['definition'],
            "mappings": {
                "icd11_tm2": result['tm2_mapping'],
                "icd11_biomedicine": result['biomedicine_mapping']
            },
            "match_info": {
                "confidence_score": result['confidence_score'],
                "match_type": result['match_type']
            }
        }
        response["results"].append(formatted_result)
    
    logging.info(f"Custom search for '{request.query}' returned {len(search_results)} results")
    return response

# Auto-complete suggestions endpoint
@app.get("/search/suggestions", response_model=List[str])
def get_search_suggestions(
    q: str = Query(..., description="Query term for suggestions"),
    limit: int = Query(5, description="Maximum number of suggestions"),
    token: str = Depends(verify_abha_token)
):
    """
    Get auto-complete suggestions for search terms.
    Returns simple list of suggested terms based on existing terminology.
    """
    if df_namaste.empty:
        return []
    
    # Get unique disease names and codes for suggestions
    all_terms = list(df_namaste['Disease'].unique()) + list(df_namaste['Code'].unique())
    
    # Use fuzzy matching to find similar terms
    suggestions = process.extract(q.lower(), [term.lower() for term in all_terms], limit=limit*2)
    
    # Return original case suggestions with good scores
    result_suggestions = []
    for suggestion, score in suggestions:
        if score >= 60 and len(result_suggestions) < limit:
            # Find original case version
            original_term = next((term for term in all_terms if term.lower() == suggestion), suggestion)
            if original_term not in result_suggestions:
                result_suggestions.append(original_term)
    
    logging.info(f"Auto-complete suggestions for '{q}': {result_suggestions}")
    return result_suggestions

# Legacy endpoint for backward compatibility
@app.post("/valueset-lookup", response_model=Dict)
def valueset_lookup(query: SearchQuery, token: str = Depends(verify_abha_token)):
    matches = df_namaste[
        df_namaste["Disease"].str.contains(query.term, case=False, na=False) |
        df_namaste["Short_Definition"].str.contains(query.term, case=False, na=False)
    ]
    # Deduplicate by Code to avoid repeated entries
    matches = matches[['Code', 'Disease', 'Short_Definition', 'icd11_tm2_code', 'icd11_biomed_code']].drop_duplicates(subset=['Code'])
    valueset = {
        "resourceType": "ValueSet",
        "expansion": {
            "contains": [
                {
                    "system": "http://ayush.gov.in/namaste",
                    "code": row["Code"],
                    "display": row["Disease"],
                    "extension": [
                        {"url": "icd11_tm2", "valueCode": row["icd11_tm2_code"]},
                        {"url": "icd11_biomed", "valueCode": row["icd11_biomed_code"]}
                    ]
                } for _, row in matches.iterrows()
            ]
        }
    }
    logging.info(f"Lookup for {query.term}")
    return valueset

# Translation operation (updated to use Code instead of namaste_code)
class TranslateRequest(BaseModel):
    code: str
    system: str  # "namaste" or "icd11"

@app.post("/translate", response_model=Dict)
def translate(req: TranslateRequest, token: str = Depends(verify_abha_token)):
    if req.system == "namaste":
        match = df_namaste[df_namaste["Code"] == req.code]
        if not match.empty:
            result = {
                "match": [
                    {"concept": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-11", "code": match.iloc[0]["icd11_tm2_code"]}]}},
                    {"concept": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-11", "code": match.iloc[0]["icd11_biomed_code"]}]}}
                ]
            }
            return result
    elif req.system == "icd11":
        # Reverse lookup (add logic if bidirectional)
        pass
    raise HTTPException(status_code=404, detail="Code not found")

# Encounter upload (no changes)
@app.post("/upload-bundle", dependencies=[Depends(verify_abha_token)])
def upload_bundle(bundle: Dict[str, Any] = Body(...)):
    if bundle.get("resourceType") != "Bundle":
        raise HTTPException(status_code=400, detail="Invalid FHIR Bundle")
    bundle["meta"] = {
        "versionId": "1",
        "lastUpdated": datetime.utcnow().isoformat(),
        "security": [{"system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality", "code": "N"}]
    }
    logging.info(f"Bundle uploaded: {json.dumps(bundle, indent=2)}")
    return {"status": "uploaded", "bundle": bundle}

# Analytics (updated for new columns: by_disease, by_state; removed by_ayush_system and by_outcome)
@app.get("/analytics", response_model=Dict)
def analytics(token: str = Depends(verify_abha_token)):
    if df_namaste.empty:
        raise HTTPException(status_code=404, detail="No data ingested")
    analytics_data = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"coding": [{"system": "http://ayush.gov.in", "code": "morbidity-stats"}]},
        "value": {
            "by_disease": df_namaste["Disease"].value_counts().to_dict(),
            "by_state": df_namaste["State"].value_counts().to_dict(),
            "by_icd11_tm2": df_namaste["icd11_tm2_code"].value_counts().to_dict(),
            "by_icd11_biomed": df_namaste["icd11_biomed_code"].value_counts().to_dict(),
            "total_patients": len(df_namaste)
        }
    }
    chart_config = {
        "type": "bar",
        "data": {
            "labels": list(analytics_data["value"]["by_disease"].keys()),
            "datasets": [{
                "label": "Disease Counts",
                "data": list(analytics_data["value"]["by_disease"].values()),
                "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"],
                "borderColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF"],
                "borderWidth": 1
            }]
        },
        "options": {
            "scales": {
                "y": {"beginAtZero": True, "title": {"display": True, "text": "Number of Patients"}},
                "x": {"title": {"display": True, "text": "Disease"}}
            },
            "plugins": {
                "title": {"display": True, "text": "NAMASTE Morbidity by Disease"},
                "legend": {"display": True, "position": "top"}
            }
        }
    }
    analytics_data["chart"] = chart_config
    logging.info("Analytics requested with chart")
    return analytics_data
# Simple web interface (no changes)
@app.get("/")
def root():
    return {"message": "NAMASTE-ICD11 Micro-Service. Use /docs for API."}

# FHIR resources endpoints (no changes)
@app.get("/CodeSystem/namaste")
def get_codesystem(token: str = Depends(verify_abha_token)):
    return namaste_codesystem

@app.get("/ConceptMap/namaste-icd11")
def get_conceptmap(token: str = Depends(verify_abha_token)):
    return concept_map

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)