"""
NeuroFence - Member 3 + 4: run the whole pipeline with ONE command.

  fuzzer prompts -> activation scan -> baseline -> preliminary detection -> trigger analysis
  -> (optional clean-vs-suspect evaluation) -> risk score -> figures

Mode A - single model, no reference (result is labelled UNVALIDATED):
    python run_final_pipeline.py --model distilgpt2

Mode B - clean reference + suspect (e.g. the toy backdoored model):
    python run_final_pipeline.py --model distilgpt2 --suspect-model models/toy_backdoor_distilgpt2 --local-only

Useful options:  --max-per-type 100   --num-layers 6   --skip-scan   --dtype float16 --device-map-auto
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable


def run(step, cmd):
    print(f"\n{'=' * 70}\n{step}\n{'=' * 70}")
    r = subprocess.run([PY] + cmd, cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"\nStep failed: {step}  (see the error above)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="distilgpt2", help="CLEAN / reference model")
    ap.add_argument("--suspect-model", default=None, help="model under test (e.g. toy backdoored model)")
    ap.add_argument("--prompts", default=None)
    ap.add_argument("--max-per-type", default="100")
    ap.add_argument("--num-layers", default="4")
    ap.add_argument("--local-only", action="store_true")
    ap.add_argument("--dtype", default=None)
    ap.add_argument("--device-map-auto", action="store_true")
    ap.add_argument("--skip-scan", action="store_true", help="reuse existing activation JSON files")
    args = ap.parse_args()

    def scan_cmd(model, output):
        c = ["activation/run_activation_scan.py", "--model", model, "--output", output,
             "--max-per-type", args.max_per_type, "--num-layers", args.num_layers]
        if args.prompts: c += ["--prompts", args.prompts]
        if args.local_only: c += ["--local-only"]
        if args.dtype: c += ["--dtype", args.dtype]
        if args.device_map_auto: c += ["--device-map-auto"]
        return c

    clean_file = "activation/activation_data_clean.json"
    main_file = "activation/activation_data.json"
    has_ref = args.suspect_model is not None

    if not args.skip_scan:
        if has_ref:
            run("1a/7 Scan CLEAN reference model", scan_cmd(args.model, clean_file))
            # the scan writes activation_meta.json next to its output; re-scanning the suspect overwrites
            # it with the suspect's meta, which is what the dashboard/report should show.
            run("1b/7 Scan SUSPECT model", scan_cmd(args.suspect_model, main_file))
        else:
            run("1/7 Scan model", scan_cmd(args.model, main_file))

    run("2/7 Build normal baseline", ["detection/baseline.py"])
    run("3/7 Preliminary Z-score detection", ["detection/preliminary_detector.py"])
    ana = ["detection/analysis.py"] + (["--reference", clean_file] if has_ref else [])
    run("4/7 Trigger consistency & specificity", ana)
    if has_ref:
        run("5/7 Evaluation (precision / recall / F1)",
            ["detection/evaluate_detection.py", "--suspect", main_file, "--clean", clean_file])
    else:
        print("\n(5/7 skipped: evaluation needs --suspect-model)")
    run("6/7 Risk score", ["detection/risk_scorer.py"] + ([] if has_ref else ["--evaluation", "none"]))
    run("7/7 Figures", ["detection/visualize.py"])
    print("\nDone. Outputs: detection/final_report.json, detection/analysis_results.json, detection/figures/")


if __name__ == "__main__":
    main()
