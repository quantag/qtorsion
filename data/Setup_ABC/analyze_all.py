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
    return z, delta, sigma_total

def main(folder_path):
    files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    files.sort()

    counts_a_list, counts_b_list, counts_c_list = [], [], []
    per_file_stats = []

    max_z_eff, min_z_eff = -float("inf"), float("inf")
    max_file, min_file = "", ""

    for fname in files:
        path = os.path.join(folder_path, fname)
        try:
            with open(path, "r") as f:
                data = json.load(f)
                a, b, c = data["job_a"], data["job_b"], data["job_c"]

                counts_a_list.append(a["counts"])
                counts_b_list.append(b["counts"])
                counts_c_list.append(c["counts"])

                zab, _, _ = compute_z(a["p_0"], a["sigma"], b["p_0"], b["sigma"])
                zac, _, _ = compute_z(a["p_0"], a["sigma"], c["p_0"], c["sigma"])
                z_eff = zab / (zac + 1e-9)

                per_file_stats.append({
                    "file": fname,
                    "z_ab": round(zab, 3),
                    "z_ac": round(zac, 3),
                    "z_eff": "inf" if math.isinf(z_eff) else round(z_eff, 3)
                })

                if z_eff > max_z_eff:
                    max_z_eff = z_eff
                    max_file = fname
                if z_eff < min_z_eff:
                    min_z_eff = z_eff
                    min_file = fname

        except Exception as e:
            print(f"Error reading {fname}: {e}", file=sys.stderr)

    agg_a, shots_a = aggregate_counts(counts_a_list)
    agg_b, shots_b = aggregate_counts(counts_b_list)
    agg_c, shots_c = aggregate_counts(counts_c_list)

    p0_a, sigma_a = compute_p0_sigma(agg_a, shots_a)
    p0_b, sigma_b = compute_p0_sigma(agg_b, shots_b)
    p0_c, sigma_c = compute_p0_sigma(agg_c, shots_c)

    z_ab, delta_ab, sigma_ab = compute_z(p0_a, sigma_a, p0_b, sigma_b)
    z_ac, delta_ac, sigma_ac = compute_z(p0_a, sigma_a, p0_c, sigma_c)
    z_eff = z_ab / (z_ac + 1e-9)

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
        "job_c": {
            "counts": agg_c,
            "shots": shots_c,
            "p_0": round(p0_c, 5),
            "sigma": round(sigma_c, 5)
        },
        "z_ab": round(z_ab, 3),
        "z_ac": round(z_ac, 3),
        "z_eff": "inf" if math.isinf(z_eff) else round(z_eff, 3),
        "z_analysis": {
            "max_z_eff": "inf" if math.isinf(max_z_eff) else round(max_z_eff, 3),
            "min_z_eff": "inf" if math.isinf(min_z_eff) else round(min_z_eff, 3),
            "max_z_eff_file": max_file,
            "min_z_eff_file": min_file
        },
        "per_file_stats": per_file_stats
    }

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_all3.py <folder_path>")
        sys.exit(1)

    main(sys.argv[1])
