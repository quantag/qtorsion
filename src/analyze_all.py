import os
import sys
import json
import math
from datetime import datetime

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def aggregate_counts(counts_list):
    agg = {}
    total_shots = 0
    for counts in counts_list:
        for k, v in counts.items():
            agg[k] = agg.get(k, 0) + v
            total_shots += v
    return agg, total_shots

def compute_p0_sigma(counts, total_shots):
    p0 = counts.get("0", 0) / total_shots if total_shots > 0 else 0.0
    sigma = math.sqrt(p0 * (1 - p0) / total_shots) if total_shots > 0 else 0.0
    return p0, sigma

def compute_z(p0a, sigmaa, p0b, sigmab):
    delta = abs(p0a - p0b)
    sigma_total = math.sqrt(sigmaa**2 + sigmab**2)
    z = delta / sigma_total if sigma_total > 0 else float("inf")
    return z

def main(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    files.sort()

    counts_a_list = []
    counts_b_list = []
    per_file_stats = []

    max_z = -float("inf")
    min_z = float("inf")
    max_z_file = ""
    min_z_file = ""

    for fname in files:
        path = os.path.join(folder_path, fname)
        try:
            with open(path, "r") as f:
                data = json.load(f)
                a = data["job_a"]
                b = data["job_b"]

                counts_a_list.append(a["counts"])
                counts_b_list.append(b["counts"])

                z = compute_z(a["p_0"], a["sigma"], b["p_0"], b["sigma"])
                per_file_stats.append({"file": fname, "z_value": round(z, 2)})

                if z > max_z:
                    max_z = z
                    max_z_file = fname
                if z < min_z:
                    min_z = z
                    min_z_file = fname

        except Exception as e:
            print(f"Error reading {fname}: {e}", file=sys.stderr)

    agg_a, shots_a = aggregate_counts(counts_a_list)
    agg_b, shots_b = aggregate_counts(counts_b_list)

    p0_a, sigma_a = compute_p0_sigma(agg_a, shots_a)
    p0_b, sigma_b = compute_p0_sigma(agg_b, shots_b)

    delta = abs(p0_a - p0_b)
    sigma_total = math.sqrt(sigma_a**2 + sigma_b**2)
    z_value = delta / sigma_total if sigma_total > 0 else float("inf")

    result = {
        "timestamp": timestamp(),
        "total_files": len(files),
        "job_a": {
            "counts": agg_a,
            "shots": shots_a,
            "p_0": round(p0_a, 5),
            "sigma": round(sigma_a, 5)
        },
        "job_b": {
            "counts": agg_b,
            "shots": shots_b,
            "p_0": round(p0_b, 5),
            "sigma": round(sigma_b, 5)
        },
        "delta": round(delta, 5),
        "sigma_total": round(sigma_total, 5),
        "z_value": "inf" if math.isinf(z_value) else round(z_value, 2),
        "z_analysis": {
            "max_z": round(max_z, 2),
            "max_z_file": max_z_file,
            "min_z": round(min_z, 2),
            "min_z_file": min_z_file
        },
        "per_file_stats": per_file_stats
    }

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_all.py <folder_path>")
        sys.exit(1)

    main(sys.argv[1])
