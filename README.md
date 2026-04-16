# SOE POC Dashboard — Streamlit

Password: **Arlington**

## Run locally
```bash
cd "$(dirname "$0")"
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud
1. Push this folder to a GitHub repo (e.g. `soe-poc-streamlit`).
2. Go to https://streamlit.io/cloud, connect the repo.
3. Main file: `app.py` — Python version 3.11+.
4. The password `Arlington` is hard-coded in `app.py`; move to Streamlit secrets if needed.

## Rebuilding data
```bash
cd ..        # Proof_of_Concept folder
python3 build_financial_json.py   # financial.json
python3 build_emissions.py        # emissions.json
```
