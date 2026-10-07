# NeuroFence -  (Activation Tracker) (Detection & Analysis)

Defensive research only. Results are **potential activation anomalies**. 

## Folder layout (copy into repo root; no teammate file is overwritten)
```
activation/
    __init__.py
    activation_tracker.py     # hooks + stats 
    inspect_model.py          # prints real layer names of your model
    run_activation_scan.py    # prompts -> activation_data.json
    sample_prompts.json       # fallback demo prompts
detection/
    __init__.py
    baseline.py               # normal records -> baseline.json 
    preliminary_detector.py   # Z-score -> preliminary_results.json
requirements_member3_4.txt
```

## Install
```bash
pip install -r requirements_member3_4.txt
```

## Run (from repo root, in this order)
```bash
python activation/inspect_model.py --model distilgpt2          # 1. see layer names
python activation/run_activation_scan.py --model distilgpt2    # 2. activation/activation_data.json
python detection/baseline.py                                   # 3. detection/baseline.json
python detection/preliminary_detector.py                       # 4. detection/preliminary_results.json
```
Offline / local model folder: add `--local-only` and use `--model ./path/to/model`.
If `generated_prompts.json` is not at root or in `fuzzer/`, pass `--prompts path/to/file.json`.

## Output formats
- `activation_data.json`: list of `{id, type, prompt, num_tokens, activations{layer_N:[...]}, statistics{layer_N:{mean,std,min,max}}}`
- `baseline.json`: per layer `position_mean`, `position_std`, `layer_stats`
- `preliminary_results.json`: `summary`, per-record `preliminary_score`, `suspicious_layers`, top suspicious positions (neuron index, value, Z)

## Hand-off to Member 5 (UI)
Read `preliminary_results.json` -> `summary.layer_ranking_test_records` (bar chart / heatmap),
`records[*].layers[*].top_suspicious_positions` (table). Always show the `disclaimer` field.

## Common errors
- `No prompts found`: your fuzzer JSON uses different keys; check TEXT_KEYS / TYPE_KEYS in run_activation_scan.py.
- `Need at least 2 'normal' records`: fuzzer category name is not `normal`; check the `type` values in activation_data.json.
- `Length mismatch`: activation file and baseline made with different --max-values; rebuild baseline.
- Model download fails offline: download once with internet, or use `--local-only` with a local folder.
- Layer not found: run `inspect_model.py`, then send me the output.

## Limitations (final-sem work)
Z >= 3 and the flag rules (min-ratio 0.02, strong-z 10) are unvalidated heuristics. Final: trigger consistency,
neuron specificity, clean vs controlled-backdoored model, precision/recall/F1.
