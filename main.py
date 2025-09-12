from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Body, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
                    format='%(asctime)s - User: %(user)s - Version: %(version)s - %(levelname)s - %(message)s')

# Global state for terminology version
TERMINOLOGY_VERSION = "1.0.0"

def get_logger_adapter(user="system"):
    """Returns a logger adapter with context for user and version."""
    return logging.LoggerAdapter(logging.getLogger(), {'user': user, 'version': TERMINOLOGY_VERSION})

app = FastAPI(title="NAMASTE-ICD11 TM2 Micro-Service")

# Mount static files
app.mount("/static", StaticFiles(directory="ui"), name="static")
app.mount("/ui", StaticFiles(directory="ui"), name="ui")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ui/pages/conversion-demo.html", response_class=FileResponse)
async def read_conversion_demo():
    return "ui/pages/conversion-demo.html"

@app.post("/token")
def get_token(form_data: OAuth2PasswordRequestForm = Depends()):
    return {"access_token": "mock-abha-token", "token_type": "bearer"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Mock ABHA token validation
def verify_abha_token(token: str = Depends(oauth2_scheme)):
    if token != "mock-abha-token":
        raise HTTPException(status_code=401, detail="Invalid ABHA token")
    
    user = "mock-clinician-01"
    logger = get_logger_adapter(user)
    logger.info(f"Access granted with token for user: {user}")
    return user

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
# Load combined disease master (ICD <-> NAMASTE) for public sandbox use
try:
    df_master = pd.read_csv('data/disease_master.csv', dtype=str).fillna('')
except Exception:
    df_master = pd.DataFrame(columns=['icd_code','icd_name','namaste_code','namaste_name','source'])

# Update FHIR resources dynamically (updated for new columns: Code, Disease, Short_Definition)
def update_fhir_resources(version: str):
    global namaste_codesystem, concept_map
    namaste_codesystem = {
        "resourceType": "CodeSystem",
        "url": "http://ayush.gov.in/namaste",
        "version": version,
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
        "version": version,
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

def sync_icd_tm2(user: str):
    token = get_icd_token()
    logger = get_logger_adapter(user)
    logger.info(f"Synced ICD data for query: traditional medicine")
    return {"status": "mock-sync"}

# Ingest NAMASTE CSV and generate FHIR resources (updated for new CSV columns and UploadFile)
@app.post("/ingest-namaste")
async def ingest_namaste(file: UploadFile = File(...), user: str = Depends(verify_abha_token)):
    global df_namaste, TERMINOLOGY_VERSION
    logger = get_logger_adapter(user)
    try:
        df_namaste = pd.read_csv(file.file)
        # Automatic mapping: Add ICD-11 columns based on Code
        df_namaste['icd11_tm2_code'] = df_namaste['Code'].map(lambda x: icd_mappings.get(x, {"tm2": "UNKNOWN"})["tm2"])
        df_namaste['icd11_biomed_code'] = df_namaste['Code'].map(lambda x: icd_mappings.get(x, {"biomed": "UNKNOWN"})["biomed"])
        
        # Update terminology version
        TERMINOLOGY_VERSION = datetime.now().strftime("%Y%m%d-%H%M%S")
        update_fhir_resources(TERMINOLOGY_VERSION)
        
        sync_icd_tm2(user)
        logger.info(f"NAMASTE terminology ingested and updated to version {TERMINOLOGY_VERSION}")
        return {"status": "success", "version": TERMINOLOGY_VERSION}
    except Exception as e:
        logger.error(f"Ingest failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ICD sync failed: {str(e)}")

# Enhanced Search & Auto-Complete Models
class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    include_fuzzy: Optional[bool] = True
    threshold: Optional[int] = 60  # Minimum fuzzy match score (0-100)

class TranslationRequest(BaseModel):
    code: str
    system: str
    target_system: str

class TranslationMatch(BaseModel):
    equivalence: str
    concept: Dict[str, str]

class TranslationResponse(BaseModel):
    result: bool
    message: str
    match: List[TranslationMatch] = []

class ConditionRequest(BaseModel):
    namaste_code: str
    namaste_display: str
    icd11_tm2_code: str
    icd11_biomed_code: str
    patient_id: str

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
def get_exact_matches(df: pd.DataFrame, query: str) -> List[Dict]:
    """Find exact matches for the query in the DataFrame."""
    matches = df[
        df['Disease'].str.lower().str.contains(query, na=False, regex=False) |
        df['Short_Definition'].str.lower().str.contains(query, na=False, regex=False) |
        df['Code'].str.lower().str.contains(query, na=False, regex=False)
    ]
    return [
        {
            'namaste_code': row['Code'],
            'display_name': row['Disease'],
            'definition': row['Short_Definition'],
            'tm2_mapping': row['icd11_tm2_code'],
            'biomedicine_mapping': row['icd11_biomed_code'],
            'confidence_score': 100,
            'match_type': 'exact'
        } for _, row in matches.iterrows()
    ]

def get_fuzzy_matches(df: pd.DataFrame, query: str, limit: int, threshold: int) -> List[Dict]:
    """Find fuzzy matches for the query in the DataFrame."""
    search_texts = df['searchable_text'].unique()
    fuzzy_matches = process.extract(query, search_texts, limit=limit, scorer=fuzz.partial_ratio)
    
    results = []
    for match, score in fuzzy_matches:
        if score >= threshold:
            matched_rows = df[df['searchable_text'] == match]
            for _, row in matched_rows.iterrows():
                results.append({
                    'namaste_code': row['Code'],
                    'display_name': row['Disease'],
                    'definition': row['Short_Definition'],
                    'tm2_mapping': row['icd11_tm2_code'],
                    'biomedicine_mapping': row['icd11_biomed_code'],
                    'confidence_score': score,
                    'match_type': 'fuzzy'
                })
    return results

def fuzzy_search_terms(query: str, limit: int = 10, threshold: int = 60) -> List[Dict]:
    """
    Perform fuzzy search on NAMASTE terminology with auto-complete functionality
    Supports partial matching, synonyms, and traditional medicine terms
    """
    if df_namaste.empty:
        return []

    query_lower = query.lower().strip()
    
    df_namaste['searchable_text'] = (
        df_namaste['Disease'].astype(str) + ' ' + 
        df_namaste['Short_Definition'].astype(str) + ' ' + 
        df_namaste['Code'].astype(str)
    ).str.lower()
    
    exact_results = get_exact_matches(df_namaste, query_lower)
    
    if len(exact_results) >= limit:
        return exact_results[:limit]
        
    remaining_limit = limit - len(exact_results)
    fuzzy_results = get_fuzzy_matches(df_namaste, query_lower, remaining_limit, threshold)
    
    # Combine and remove duplicates
    combined_results = exact_results + fuzzy_results
    seen = set()
    unique_results = []
    for res in combined_results:
        if res['namaste_code'] not in seen:
            unique_results.append(res)
            seen.add(res['namaste_code'])
            
    return unique_results[:limit]


# Public sandbox endpoints (no ABHA token) ----------------------------------
@app.get('/api/autocomplete')
def api_autocomplete(q: str = Query(..., min_length=1), limit: int = 10):
    """Return simple autocomplete suggestions from the master CSV."""
    ql = q.strip().lower()
    if ql == '':
        return {'results': []}

    # search both namaste_name and icd_name and codes
    mask = (
        df_master['namaste_name'].str.lower().str.contains(ql, na=False) |
        df_master['namaste_code'].str.lower().str.contains(ql, na=False) |
        df_master['icd_code'].str.lower().str.contains(ql, na=False) |
        df_master['icd_name'].str.lower().str.contains(ql, na=False)
    )
    results = df_master[mask].head(limit)
    out = []
    for _, row in results.iterrows():
        out.append({
            'namaste_code': row.get('namaste_code',''),
            'namaste_name': row.get('namaste_name',''),
            'icd_code': row.get('icd_code',''),
            'icd_name': row.get('icd_name',''),
            'source': row.get('source','')
        })
    return {'results': out}


@app.get('/api/translate')
def api_translate(term: str = Query(..., min_length=1), prefer: str = Query('namaste')):
    """Translate a term or code. prefer='namaste' returns NAMASTE -> ICD if possible.
    prefer: 'namaste' | 'icd' | 'auto'
    """
    ql = term.strip().lower()

    def match_by_kind(kind: str):
        # kind: 'namaste' or 'icd'
        if kind == 'namaste':
            row = df_master[df_master['namaste_code'].str.lower() == ql]
            if row.empty:
                row = df_master[df_master['namaste_name'].str.lower() == ql]
            return row
        else:
            row = df_master[df_master['icd_code'].str.lower() == ql]
            if row.empty:
                row = df_master[df_master['icd_name'].str.lower() == ql]
            return row

    rows = pd.DataFrame()
    pref = (prefer or 'namaste').lower()
    if pref == 'namaste':
        rows = match_by_kind('namaste')
        if rows.empty:
            rows = match_by_kind('icd')
    elif pref == 'icd':
        rows = match_by_kind('icd')
        if rows.empty:
            rows = match_by_kind('namaste')
    else:  # auto-detect: try code-like patterns first
        # simple heuristic: codes often contain digits or hyphens; prefer code match first
        if re.search(r"\d|-", term):
            rows = match_by_kind('icd')
            if rows.empty:
                rows = match_by_kind('namaste')
        else:
            # try exact name match in both
            rows = match_by_kind('namaste')
            if rows.empty:
                rows = match_by_kind('icd')

    if rows.empty:
        return {'error': 'no match'}

    r = rows.iloc[0]
    return {
        'namaste_code': r.get('namaste_code',''),
        'namaste_name': r.get('namaste_name',''),
        'icd_code': r.get('icd_code',''),
        'icd_name': r.get('icd_name',''),
        'source': r.get('source','')
    }


@app.get('/api/disease/{code}')
def api_disease_lookup(code: str):
    """Lookup disease by NAMASTE or ICD code."""
    ql = code.strip().lower()
    rows = df_master[(df_master['namaste_code'].str.lower() == ql) | (df_master['icd_code'].str.lower() == ql)]
    if rows.empty:
        raise HTTPException(status_code=404, detail='Not found')
    r = rows.iloc[0]
    return {
        'namaste_code': r.get('namaste_code',''),
        'namaste_name': r.get('namaste_name',''),
        'icd_code': r.get('icd_code',''),
        'icd_name': r.get('icd_name',''),
        'source': r.get('source','')
    }


@app.post("/generate-condition")
async def generate_condition(request: ConditionRequest, user: str = Depends(verify_abha_token)):
    """
    Generates a FHIR Condition resource with dual NAMASTE and ICD-11 codings.
    """
    condition = {
        "resourceType": "Condition",
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                    "display": "Active"
                }
            ]
        },
        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed",
                    "display": "Confirmed"
                }
            ]
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                        "code": "problem-list-item",
                        "display": "Problem List Item"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://ayush.gov.in/namaste",
                    "code": request.namaste_code,
                    "display": request.namaste_display
                },
                {
                    "system": "http://hl7.org/fhir/sid/icd-11",
                    "code": request.icd11_tm2_code,
                    "display": f"ICD-11 TM2: {request.icd11_tm2_code}"
                },
                {
                    "system": "http://hl7.org/fhir/sid/icd-11",
                    "code": request.icd11_biomed_code,
                    "display": f"ICD-11 Biomedicine: {request.icd11_biomed_code}"
                }
            ],
            "text": request.namaste_display
        },
        "subject": {
            "reference": request.patient_id
        },
        "recordedDate": datetime.now().isoformat()
    }
    
    logger = get_logger_adapter(user)
    logger.info(f"Generated FHIR Condition for patient {request.patient_id}")
    
    return condition

@app.post("/upload-encounter")
async def upload_encounter(bundle: Dict[str, Any] = Body(...), user: str = Depends(verify_abha_token)):
    """
    Accepts a FHIR Bundle (e.g., containing Encounter and Condition resources).
    Logs the bundle and returns a success message.
    """
    logger = get_logger_adapter(user)
    logger.info(f"Received FHIR Bundle of type: {bundle.get('resourceType')}")
    
    if bundle.get('resourceType') != 'Bundle':
        raise HTTPException(status_code=400, detail="Invalid resource type. Expected 'Bundle'.")

    # For demonstration, we'll just log the received bundle
    logger.info(f"Bundle received with {len(bundle.get('entry', []))} entries.")
    logger.debug(json.dumps(bundle, indent=2))

    return {"status": "success", "message": "FHIR Bundle received successfully."}

def _get_translation_matches(df: pd.DataFrame, source_code: str, source_column: str, target_column: str, display_column: str) -> List[TranslationMatch]:
    """Helper to find translation matches in a DataFrame."""
    matches = []
    result_df = df[df[source_column] == source_code]
    if not result_df.empty:
        for _, row in result_df.iterrows():
            if pd.notna(row[target_column]) and row[target_column] != 'UNKNOWN':
                matches.append(TranslationMatch(
                    equivalence="equivalent",
                    concept={"code": row[target_column], "display": row.get(display_column, '')}
                ))
    return matches

@app.post("/translate", response_model=TranslationResponse)
async def translate_code(request: TranslationRequest, user: str = Depends(verify_abha_token)):
    """
    Translate a code from a source system to a target system.
    - NAMASTE -> TM2
    - TM2 -> NAMASTE
    """
    if df_namaste.empty:
        raise HTTPException(status_code=503, detail="Terminology data not ingested yet. Please upload a CSV file.")

    source_system = request.system
    target_system = request.target_system
    code = request.code
    
    logger = get_logger_adapter(user)
    logger.info(f"Performing translation for code '{code}' from {source_system} to {target_system}")

    matches = []
    if source_system == "NAMASTE" and target_system == "TM2":
        matches = _get_translation_matches(df_namaste, code, 'Code', 'icd11_tm2_code', 'Disease')
    elif source_system == "TM2" and target_system == "NAMASTE":
        matches = _get_translation_matches(df_namaste, code, 'icd11_tm2_code', 'Code', 'Disease')
    else:
        return TranslationResponse(result=False, message="Unsupported translation direction. Use NAMASTE -> TM2 or TM2 -> NAMASTE.")

    if not matches:
        return TranslationResponse(result=False, message=f"No translation found for code '{code}' from {source_system} to {target_system}.")

    return TranslationResponse(result=True, message="Translation successful", match=matches)

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
# Simple web interface - serve the main landing page
@app.get("/")
def root():
    return FileResponse('ui/pages/landing.html')

# Serve other UI pages
@app.get("/terminology-ingestion")
def terminology_ingestion():
    return FileResponse('ui/pages/terminology-ingestion.html')

@app.get("/search-autocomplete")
def search_autocomplete():
    return FileResponse('ui/pages/search-autocomplete.html')

@app.get("/doctor-sandbox")
def doctor_sandbox():
    return FileResponse('ui/pages/doctor-sandbox.html')

@app.get("/insurance-sandbox")
def insurance_sandbox():
    return FileResponse('ui/pages/insurance-sandbox.html')

@app.get("/researcher-sandbox")
def researcher_sandbox():
    return FileResponse('ui/pages/researcher-sandbox.html')

@app.get("/problem-list-generator")
def problem_list_generator():
    return FileResponse('ui/pages/problem-list-generator.html')

@app.get("/encounter-uploader")
def encounter_uploader():
    return FileResponse('ui/pages/encounter-uploader.html')

@app.get("/use-case-presentation")
def use_case_presentation():
    return FileResponse('ui/pages/use-case-presentation.html')

@app.get("/api-docs-page")
def api_docs_page():
    return FileResponse('ui/pages/api-docs.html')

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