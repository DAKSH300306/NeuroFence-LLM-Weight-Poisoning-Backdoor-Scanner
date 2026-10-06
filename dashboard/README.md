# NeuroFence dashboard

Backend (port 8000):
    cd backend && pip install -r requirements.txt && uvicorn backend:app --reload --port 8000
Frontend (port 5173, proxies /api to 8000):
    cd frontend && npm install && npm run dev

Real pipeline output (fuzzer/generated_prompts.json, detection/preliminary_results.json) is used when present;
otherwise backend/data/*.json demo data is served. Replace the provider functions in backend.py to wire in more.
