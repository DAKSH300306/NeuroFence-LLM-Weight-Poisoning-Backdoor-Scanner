# NeuroFence - Member 3 (Activation Tracker) + Member 4 (Detection & Analysis) - FINAL

Defensive AI-security research. Every result is a **potential activation anomaly / indicator**, never proof of a backdoor.

## 0. Virtual environment (do this first)
Yes, create your OWN environment. The Mistral-7B setup of your teammates has heavy packages (CUDA torch, bitsandbytes,
accelerate). Our pipeline only needs torch + transformers + numpy + matplotlib, and a separate env keeps both working.

macOS / Linux:
```bash
cd NeuroFence-LLM-Weight-Poisoning-Backdoor-Scanner
python3 -m venv .venv-neurofence
source .venv-neurofence/bin/activate
pip install --upgrade pip
pip install -r requirements_member3_4.txt
```
Windows (PowerShell):
```powershell
py -m venv .venv-neurofence
.venv-neurofence\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements_member3_4.txt
```
Dashboard backend in the same env: `pip install -r dashboard/backend/requirements.txt` then `cd dashboard/backend && uvicorn backend:app --port 8000`.
(The dashboard launches the pipeline with the Python that runs uvicorn, so start it from this env.)

## 1. What is new in this package
```
activation/   activation_tracker.py (+ float16 / device_map support), run_activation_scan.py (+ --dtype, --device-map-auto),
              inspect_model.py, sample_prompts.json
detection/    baseline.py, preliminary_detector.py            (mid-sem, unchanged)
              analysis.py            NEW  false-positive check, trigger consistency, specificity, clean-reference comparison
              evaluate_detection.py  NEW  precision / recall / F1 on held-out prompts + clean-model false alarms
              risk_scorer.py         NEW  final risk indicator -> detection/final_report.json
              visualize.py           NEW  PNG figures for the report -> detection/figures/
experiments/  make_toy_backdoor.py   NEW  controlled, benign toy backdoor (distilgpt2) for validation
run_final_pipeline.py                NEW  one command for everything
```
No teammate file is modified.

## 2. Run
Mode A - single model (result is labelled UNVALIDATED because there is no clean reference):
```bash
python run_final_pipeline.py --model distilgpt2
```
Mode B - full validation with a known ground truth (recommended for the final demo):
```bash
python experiments/make_toy_backdoor.py                       # trains models/toy_backdoor_distilgpt2 (few minutes on CPU)
python run_final_pipeline.py --model distilgpt2 --suspect-model models/toy_backdoor_distilgpt2
```
`make_toy_backdoor.py` prints "Backdoor check: marker on trigger prompts X/3, on normal prompts Y/3".
You want 3/3 and 0/3. If not, run it again with `--epochs 8`.

Mistral-7B (optional, needs a big GPU / lots of RAM; use only if your team demo needs it):
```bash
pip install accelerate
python run_final_pipeline.py --model mistralai/Mistral-7B-Instruct-v0.2 --dtype float16 --device-map-auto --max-per-type 20
```
Mistral hidden size is 4096; by default only the first 768 positions are stored. Add `--max-values 4096` to
`activation/run_activation_scan.py` if you run it yourself.

## 3. Outputs
| File | Meaning |
|---|---|
| activation/activation_data.json | activations of the model under test |
| activation/activation_data_clean.json | clean reference activations (Mode B) |
| detection/baseline.json, preliminary_results.json | mid-sem baseline + Z-score screening |
| detection/analysis_results.json | false positives, consistency, specificity, candidate neurons |
| detection/evaluation.json | confusion matrix, precision/recall/F1, clean false-alarm rate |
| detection/final_report.json | risk score, level, verdict, suspicious layers, limitations (for Member 5 / PDF) |
| detection/figures/*.png | heatmap, candidate positions, top neurons |

## 4. How to explain it (viva)
1. Hooks capture each transformer block's output; tokens are averaged -> one vector per layer (position = neuron).
2. Normal prompts define a baseline (mean/std per position). Z = |x - mean| / std.
3. Mid-sem finding: edge and long prompts are flagged as much as trigger prompts -> Z-score alone measures "different input", not backdoor.
4. Final method: keep only positions that are (a) consistent across trigger prompts, (b) not shared by edge/long prompts,
   (c) absent in a clean reference model. Those are candidate trigger neurons.
5. Validation: toy backdoored model (ground truth known), held-out prompts, precision / recall / F1, and false alarms on the clean model.
6. Risk score = weighted heuristic of specificity, consistency, layer spread, discounted by the false-positive rate.

## 5. Honest limitations (say these yourself in the viva)
- Weights, thresholds (Z=3, consistency 0.7, level cut-offs) are not scientifically validated.
- Validated only on a small toy model and a toy trigger; no claim about real-world models.
- The code was tested end-to-end on real repo activations plus a synthetic injected spike. The synthetic spike is easy, so perfect
  precision/recall there says little. Real numbers come from YOUR run of the toy backdoor (Mode B) - report those, whatever they are.
- Mean pooling mixes in prompt-length effects (prompt length correlates with deviation).
- A high score = "potential backdoor indicator", never "confirmed backdoor".

## 6. Common errors
- `No prompts found`: check keys in fuzzer/generated_prompts.json (needs "prompt" and "type").
- `Need at least 2 normal records`: category names; run with --max-per-type 20 or more.
- `Length mismatch`: baseline and activations made with different --max-values; rerun both.
- Offline / local model: add --local-only and give a folder path.
- `device_map` error: `pip install accelerate`.
- Out of memory with Mistral: use distilgpt2, or float16 + --device-map-auto, or fewer prompts.
