# NeuroFence dashboard

Place `dashboard/` at the repo root, next to `fuzzer/` and `neurofence_member3_4/`.

## Run
    # Terminal 1: use a Python that has torch + transformers + numpy
    pip install -r neurofence_member3_4/requirements_member3_4.txt
    cd dashboard/backend && pip install -r requirements.txt
    uvicorn backend:app --reload --port 8000

    # Terminal 2
    cd dashboard/frontend && npm install && npm run dev      # http://localhost:5173

## What "Start scan" does
1. fuzzer/fuzzer.py                      -> fuzzer/generated_prompts.json
2. activation/run_activation_scan.py     -> activation_data.json (20 prompts per type by default)
3. detection/baseline.py                 -> baseline.json
4. detection/preliminary_detector.py     -> preliminary_results.json
Progress and log lines stream to the UI. Stop kills the running step.

## Settings
Model name or folder and the Offline switch are in the dashboard header.
Environment: NEUROFENCE_MODEL, NEUROFENCE_LOCAL_ONLY=1, NEUROFENCE_MAX_PER_TYPE, NEUROFENCE_DEMO=1 (force demo data).
If the pipeline folders are missing, the dashboard plays back backend/data/*.json instead.

## How results are derived
- Heatmap: share of anomalous activation positions per layer and prompt type, scaled to the strongest cell.
- Risk score: share of non-normal prompts flagged, minus the share of normal prompts flagged.
- Suspicious layers: layers with flagged prompts and at least a quarter of the strongest layer's anomaly ratio.
- Trigger: most common all-caps word in the trigger prompts; confidence is the share of trigger prompts flagged.
These are heuristics on top of Z-scores, not a confirmed backdoor verdict.

## Notes
- On startup the dashboard shows the results of your last scan (from preliminary_results.json), so Findings and Model & prompts are filled before you scan again.
- Light and dark themes follow your system; use the button at the bottom of the sidebar to switch.
