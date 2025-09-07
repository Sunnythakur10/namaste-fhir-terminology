# NAMASTE-ICD11 TM2 Micro-Service

## Project Overview
This repository contains the **NAMASTE-ICD11 TM2 Micro-Service** developed for the **Smart India Hackathon (SIH-25026)**. The project maps NAMASTE (Ayush) diagnostic codes to ICD-11 Traditional Medicine (TM2) and biomedical codes, delivering FHIR-compliant resources for integration with modern healthcare systems. It provides real-time morbidity analytics for the Ministry of Ayush, tested with a dummy dataset and visualized using Chart.js for the SIH demo.

## What Has Been Done
The project is a FastAPI-based microservice with the following accomplishments (as of September 7, 2025):

1. **FastAPI Microservice**:
   - Built a microservice in `main.py` with endpoints:
     - `/ingest-namaste`: Uploads and processes CSV files with patient data.
     - `/valueset-lookup`: Searches for terms (e.g., "Diabetes", "Cough") and returns FHIR ValueSet with NAMASTE and ICD-11 codes.
     - `/translate`: Maps NAMASTE codes (e.g., `EF-2.4.4`) to ICD-11 TM2 (`SJ00`) and biomedical (`5A11`) codes.
     - `/analytics`: Provides morbidity stats in FHIR Observation format (e.g., 10 cases per disease).
     - `/CodeSystem/namaste` and `/ConceptMap/namaste-icd11`: Expose FHIR resources.
     - `/upload-bundle`: Handles FHIR Bundles.
   - Implemented mock ABHA token authentication (`mock-abha-token`) for EHR compliance.
   - Added logging to `audit.log` for audit trails.

2. **Dataset Handling**:
   - Initially tested with a 1000-record dataset (`namaste_dummy_dataset.csv`) including columns like `Diagnosis_Code`, `Diagnosis_Name`, `AYUSH_System`, `Outcome`.
   - Updated to a new 50-record dataset with columns:
     - `Patient_ID`, `Age`, `Gender`, `Disease`, `Code`, `Short_Definition`, `State`, `Date_of_Visit`.
     - Example: `C001,20,M,Sandhigatvata,AAE-16,Vitiated Vata in Sandhi,Karnataka,2025-06-01`.
   - Adapted code to handle new columns, mapping codes (e.g., `EF-2.4.4` for `Madhumeha/Kshaudrameha` to `SJ00`/`5A11`).

3. **Testing and Bug Fixes**:
   - Successfully ingested the 50-record dataset:
     ```cmd
     curl -X POST "http://127.0.0.1:8000/ingest-namaste" -H "Authorization: Bearer mock-abha-token" -F "file=@namaste_dummy_dataset.csv"
     ```
     Output: `{"status":"success"}`
   - Tested search for "Diabetes" and "Cough":
     ```cmd
     curl -X POST "http://127.0.0.1:8000/valueset-lookup" -H "Authorization: Bearer mock-abha-token" -H "Content-Type: application/json" -d "{\"term\": \"Diabetes\"}"
     ```
     Output: Single entry for `EF-2.4.4` (fixed duplicate issue using `drop_duplicates`).
   - Tested analytics:
     ```cmd
     curl -X GET "http://127.0.0.1:8000/analytics" -H "Authorization: Bearer mock-abha-token"
     ```
     Output: FHIR Observation with `by_disease` (10 cases each for 5 diseases), `by_state`, `by_icd11_tm2`, `by_icd11_biomed`, and `total_patients: 50`.
   - Tested translation:
     ```cmd
     curl -X POST "http://127.0.0.1:8000/translate" -H "Authorization: Bearer mock-abha-token" -H "Content-Type: application/json" -d "{\"code\": \"EF-2.4.4\", \"system\": \"namaste\"}"
     ```
     Output: Maps `EF-2.4.4` to `SJ00` and `5A11`.

4. **Visualization**:
   - Added a Chart.js bar chart to `/analytics` for `by_disease` (5 diseases: `Sandhigatvata`, `Vatavyadhi`, `Arsha`, `Madhumeha/Kshaudrameha`, `Kasa`, each with 10 cases).
   - Created `index.html` to render the chart locally via `http://127.0.0.1:8080/index.html`.
   - Chart features:
     - 5 colored bars (red, blue, yellow, teal, purple).
     - X-axis: Disease names.
     - Y-axis: Number of patients (0 to 10+).
     - Title: “NAMASTE Morbidity by Disease”.
   - Added CORS middleware to `main.py` to allow frontend fetch.

5. **Issues Resolved**:
   - Fixed duplicate entries in `/valueset-lookup` (e.g., single entry for `EF-2.4.4`).
   - Addressed `uvicorn` not recognized issue by suggesting `py -m uvicorn`.

6. **Prepared for Deployment**:
   - Planned Vercel deployment (not yet implemented).
   - Discussed adding more visualizations (e.g., pie chart for `by_state`).

## Current State
- **Location**: `C:\Users\sunny\Downloads\Namaste`
- **Files**:
  - `main.py`: FastAPI microservice with all endpoints.
  - `namaste_dummy_dataset.csv`: 50-record dataset.
  - `index.html`: Frontend for Chart.js visualization.
  - `audit.log`: Logs for debugging (e.g., “Analytics requested with chart”).
- **Endpoints**: All working, tested with `curl` commands.
- **Visualization**: Bar chart for `by_disease` viewable at `http://127.0.0.1:8080/index.html`.
- **Dependencies**: `fastapi`, `uvicorn`, `pandas`, `requests`, `python-jose`, `pydantic`.

## What Team Members Need to Do
To contribute to the project and prepare for the SIH demo, team members should focus on the following tasks:

1. **Test Existing Functionality**:
   - Verify all endpoints using `curl` or Swagger UI (`http://127.0.0.1:8000/docs`).
   - Test search for other terms (e.g., “Cough” for `Kasa`, code `EA-3`).
   - Check the bar chart at `http://127.0.0.1:8080/index.html`.

2. **Add More Visualizations**:
   - Implement a pie chart for `by_state` (e.g., Karnataka: 6, Kerala: 5):
     - Update `main.py` to add `chart_state` (see code in “Optional Enhancements”).
     - Modify `index.html` to render the pie chart.
   - Add a dropdown in `index.html` to switch between charts (disease, state, ICD-11).

3. **Integrate WHO ICD-11 API**:
   - Register for WHO ICD-11 API credentials (https://icd.who.int).
   - Update `sync_icd_tm2` in `main.py` to fetch real mappings:
     ```python
     def get_icd_token():
         data = {
             "client_id": "YOUR_CLIENT_ID",
             "client_secret": "YOUR_CLIENT_SECRET",
             "scope": "icdapi_access",
             "grant_type": "client_credentials"
         }
         response = requests.post("https://icdaccessmanagement.who.int/connect/token", data=data)
         return response.json().get("access_token")

     def sync_icd_tm2(query: str = "traditional medicine"):
         token = get_icd_token()
         headers = {"Authorization": f"Bearer {token}", "Accept": "application/json", "Accept-Language": "en"}
         url = f"https://id.who.int/icd/release/11/mms/search?q={query}"
         response = requests.get(url, headers=headers)
         if response.status_code == 200:
             return response.json()
         raise HTTPException(status_code=500, detail="ICD sync failed")
     ```
   - Update `icd_mappings` dynamically based on API results.

4. **Deploy on Vercel**:
   - Install Vercel CLI: `npm install -g vercel`.
   - Create `vercel.json`:
     ```json
     {
       "rewrites": [
         { "source": "/api/(.*)", "destination": "/api" },
         { "source": "/(.*)", "destination": "/index.html" }
       ]
     }
     ```
   - Run `vercel` in `C:\Users\sunny\Downloads\Namaste` and follow prompts.
   - Update `index.html` to fetch from the Vercel URL (e.g., `https://your-project.vercel.app/analytics`).

5. **Prepare SIH Demo**:
   - Take screenshots of the chart and API outputs (`/analytics`, `/valueset-lookup`).
   - Record a video showing the chart and API calls (e.g., search for “Diabetes”).
   - Write a report explaining how the microservice and visualization help the Ministry track morbidity trends.

6. **Enhance Frontend**:
   - Add styling to `index.html` (e.g., Ayush logo, colors).
   - Add interactivity (e.g., dropdown to switch charts, as shown below).

## How to Run the Repository
Follow these steps to set up and run the project locally in `C:\Users\sunny\Downloads\Namaste`:

### Prerequisites
- **Python 3.8+**: Ensure Python is installed (`py --version`).
- **Dependencies**: Install required packages:
  ```cmd
  py -m pip install fastapi uvicorn pandas requests python-jose pydantic
  ```
- **Dataset**: Ensure `namaste_dummy_dataset.csv` is in the folder (50 records with columns `Patient_ID`, `Age`, `Gender`, `Disease`, `Code`, `Short_Definition`, `State`, `Date_of_Visit`).
- **Node.js** (optional, for Vercel): Install Node.js for deployment (`npm install -g vercel`).

### Setup
1. **Clone or Navigate to Repository**:
   - The project is in `C:\Users\sunny\Downloads\Namaste`.
   - Ensure `main.py`, `index.html`, and `namaste_dummy_dataset.csv` are present.

2. **Run the FastAPI Server**:
   - Open Command Prompt in `C:\Users\sunny\Downloads\Namaste`.
   - Start the server:
     ```cmd
     py -m uvicorn main:app --host 0.0.0.0 --port 8000
     ```
   - If `uvicorn` fails, reinstall:
     ```cmd
     py -m pip install --force-reinstall uvicorn
     ```

3. **Ingest the Dataset**:
   - Run:
     ```cmd
     curl -X POST "http://127.0.0.1:8000/ingest-namaste" ^
       -H "Authorization: Bearer mock-abha-token" ^
       -F "file=@namaste_dummy_dataset.csv"
     ```
   - Expected: `{"status":"success"}`

4. **View the Visualization**:
   - Start an HTTP server for the frontend:
     ```cmd
     py -m http.server 8080
     ```
   - Open `http://127.0.0.1:8080/index.html` in a browser (e.g., Chrome).
   - **Expected**: A bar chart with 5 bars (`Sandhigatvata`, `Vatavyadhi`, `Arsha`, `Madhumeha/Kshaudrameha`, `Kasa`), each showing 10 patients, with colored bars and labeled axes.

5. **Test Other Endpoints**:
   - **Search**:
     ```cmd
     curl -X POST "http://127.0.0.1:8000/valueset-lookup" ^
       -H "Authorization: Bearer mock-abha-token" ^
       -H "Content-Type: application/json" ^
       -d "{\"term\": \"Diabetes\"}"
     ```
     Expected: Single entry for `EF-2.4.4` (`Madhumeha/Kshaudrameha`).
   - **Analytics**:
     ```cmd
     curl -X GET "http://127.0.0.1:8000/analytics" ^
       -H "Authorization: Bearer mock-abha-token"
     ```
     Expected: FHIR Observation with `by_disease`, `by_state`, `by_icd11_tm2`, `by_icd11_biomed`, and `chart`.
   - **Translation**:
     ```cmd
     curl -X POST "http://127.0.0.1:8000/translate" ^
       -H "Authorization: Bearer mock-abha-token" ^
       -H "Content-Type: application/json" ^
       -d "{\"code\": \"EF-2.4.4\", \"system\": \"namaste\"}"
     ```
     Expected: Maps `EF-2.4.4` to `SJ00` and `5A11`.

6. **Check Logs**:
   - Open `audit.log` to verify actions (e.g., “NAMASTE ingested and synced”, “Analytics requested with chart”).

## How to Use the Application
- **Swagger UI**: Access `http://127.0.0.1:8000/docs` to test endpoints interactively. Use `mock-abha-token` for authentication.
- **Visualization**: Open `http://127.0.0.1:8080/index.html` to view the Chart.js bar chart for `by_disease`.
- **API Testing**: Use `curl` commands or tools like Postman to test endpoints.
- **Debugging**: Check `audit.log` for errors or confirm successful actions.

## Optional Enhancements
- **Pie Chart for States**:
  - Add to `main.py`:
    ```python
    chart_config_state = {
        "type": "pie",
        "data": {
            "labels": list(analytics_data["value"]["by_state"].keys()),
            "datasets": [{
                "label": "State Distribution",
                "data": list(analytics_data["value"]["by_state"].values()),
                "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40", "#FFCD56", "#4BC0C0", "#36A2EB"],
                "borderColor": ["#FFFFFF"] * len(analytics_data["value"]["by_state"]),
                "borderWidth": 1
            }]
        },
        "options": {
            "plugins": {
                "title": {"display": True, "text": "Patients by State"},
                "legend": {"display": True, "position": "right"}
            }
        }
    }
    analytics_data["chart_state"] = chart_config_state
    ```
  - Update `index.html` to show both charts:
    ```html
    <h2>By Disease</h2>
    <canvas id="diseaseChart" width="600" height="400"></canvas>
    <h2>By State</h2>
    <canvas id="stateChart" width="600" height="400"></canvas>
    <script>
        async function fetchAnalytics() {
            const response = await fetch('http://127.0.0.1:8000/analytics', {
                headers: { 'Authorization': 'Bearer mock-abha-token' }
            });
            const data = await response.json();
            new Chart(document.getElementById('diseaseChart').getContext('2d'), data.chart);
            new Chart(document.getElementById('stateChart').getContext('2d'), data.chart_state);
        }
        fetchAnalytics();
    </script>
    ```
- **Interactivity**:
  - Add a dropdown to switch charts:
    ```html
    <select id="chartSelect" onchange="updateChart()">
        <option value="chart">By Disease (Bar)</option>
        <option value="chart_state">By State (Pie)</option>
    </select>
    <canvas id="diseaseChart" width="600" height="400"></canvas>
    <script>
        let chartInstance = null;
        async function fetchAnalytics() {
            const response = await fetch('http://127.0.0.1:8000/analytics', {
                headers: { 'Authorization': 'Bearer mock-abha-token' }
            });
            window.analyticsData = await response.json();
            updateChart();
        }
        function updateChart() {
            const select = document.getElementById('chartSelect').value;
            const ctx = document.getElementById('diseaseChart').getContext('2d');
            if (chartInstance) chartInstance.destroy();
            chartInstance = new Chart(ctx, window.analyticsData[select]);
        }
        fetchAnalytics();
    </script>
    ```

## Troubleshooting
- **Uvicorn Not Found**: Run `py -m pip install --force-reinstall uvicorn`.
- **Chart Not Loading**: Check browser console (F12 → Console) for errors. Ensure FastAPI server is running and CORS middleware is in `main.py`.
- **Empty Chart**: Re-ingest `namaste_dummy_dataset.csv` if `df_namaste` is empty.
- **Logs**: Check `audit.log` for errors or confirmation messages.

## Contact
For questions, contact [Your Name] (replace with your contact details) or ping the SIH team on [communication platform].