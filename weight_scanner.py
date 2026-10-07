import os
import json
import argparse
import torch


def tensor_statistics(tensor):
    """Calculate basic statistics for a model weight tensor."""

    tensor = tensor.detach().float().cpu()

    mean = tensor.mean().item()
    std = tensor.std().item()
    min_value = tensor.min().item()
    max_value = tensor.max().item()

    if std > 0:
        z_scores = torch.abs((tensor - mean) / std)
        suspicious_count = int((z_scores > 5.0).sum().item())
    else:
        suspicious_count = 0

    total_values = tensor.numel()

    anomaly_ratio = (
        suspicious_count / total_values
        if total_values > 0
        else 0.0
    )

    return {
        "shape": list(tensor.shape),
        "num_parameters": total_values,
        "mean": mean,
        "std": std,
        "min": min_value,
        "max": max_value,
        "suspicious_values": suspicious_count,
        "anomaly_ratio": anomaly_ratio,
    }


def scan_state_dict(state_dict):
    """Scan all tensors in a model state dictionary."""

    results = []
    suspicious_layers = []

    for layer_name, tensor in state_dict.items():

        if not torch.is_tensor(tensor):
            continue

        stats = tensor_statistics(tensor)

        # Initial anomaly score.
        # This will later be replaced/enhanced by Member 4's
        # statistical detection logic.
        anomaly_score = min(
            stats["anomaly_ratio"] * 100.0,
            100.0
        )

        layer_result = {
            "layer": layer_name,
            "statistics": stats,
            "anomaly_score": anomaly_score,
        }

        results.append(layer_result)

        if stats["suspicious_values"] > 0:
            suspicious_layers.append({
                "layer": layer_name,
                "anomaly_score": anomaly_score,
                "suspicious_values": stats["suspicious_values"],
            })

    results.sort(
        key=lambda x: x["anomaly_score"],
        reverse=True
    )

    suspicious_layers.sort(
        key=lambda x: x["anomaly_score"],
        reverse=True
    )

    return results, suspicious_layers


def load_model_weights(model_path):
    """Load a PyTorch state dictionary."""

    print(f"[+] Loading weights from: {model_path}")

    checkpoint = torch.load(
        model_path,
        map_location="cpu",
        weights_only=True
    )

    if isinstance(checkpoint, dict):

        # Direct state_dict
        if all(torch.is_tensor(v) for v in checkpoint.values()):
            return checkpoint

        # Common checkpoint format
        if "state_dict" in checkpoint:
            return checkpoint["state_dict"]

    raise ValueError(
        "Unsupported checkpoint format. "
        "Expected a PyTorch state_dict."
    )


def save_report(
    output_path,
    model_path,
    results,
    suspicious_layers
):
    """Save scanner results as JSON."""

    report = {
        "scanner": "NeuroFence Weight Scanner",
        "model_path": model_path,
        "total_layers_scanned": len(results),
        "suspicious_layers_count": len(suspicious_layers),
        "verdict": (
            "SUSPICIOUS"
            if suspicious_layers
            else "NO_OBVIOUS_ANOMALY"
        ),
        "suspicious_layers": suspicious_layers,
        "layer_results": results,
    }

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            report,
            f,
            indent=4
        )

    print(f"[+] Report saved to: {output_path}")


def main():

    parser = argparse.ArgumentParser(
        description=(
            "NeuroFence - LLM Weight Poisoning "
            "and Backdoor Weight Scanner"
        )
    )

    parser.add_argument(
        "--model",
        required=True,
        help="Path to PyTorch model checkpoint (.pt/.bin)"
    )

    parser.add_argument(
        "--output",
        default="weight_scan_report.json",
        help="Output JSON report path"
    )

    args = parser.parse_args()

    if not os.path.exists(args.model):
        print(f"[!] Model file not found: {args.model}")
        return

    try:
        state_dict = load_model_weights(args.model)

        print(
            f"[+] Found {len(state_dict)} tensors"
        )

        results, suspicious_layers = scan_state_dict(
            state_dict
        )

        print("\n========== SCAN SUMMARY ==========")
        print(
            f"Layers scanned      : {len(results)}"
        )
        print(
            f"Suspicious layers   : {len(suspicious_layers)}"
        )

        if suspicious_layers:
            print("[!] Potential anomalies detected")
        else:
            print("[+] No obvious anomalies detected")

        save_report(
            args.output,
            args.model,
            results,
            suspicious_layers
        )

    except Exception as e:
        print(f"[!] Scanner error: {e}")


if __name__ == "__main__":
    main()
