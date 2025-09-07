from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import requests
import logging
import json
from datetime import datetime
from typing import Dict, Any

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

# Auto-complete value-set lookup (updated to search on Disease and Short_Definition)
class SearchQuery(BaseModel):
    term: str

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