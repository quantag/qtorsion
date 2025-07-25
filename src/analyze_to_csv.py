import os
import sys
import json
import math
import csv
from datetime import datetime

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def compute_delta_sigma_z(p0a, sigmaa, p0b, sigmab):
    delta = abs(p0a - p0b)
    sigma_total = math.sqrt(sigmaa**2 + sigmab**2)
    z = delta / sigma_total if sigma_total > 0 else float("inf")
    return delta, sigma_total, z

def main(folder_path, output_csv="results_summary.csv"):
    files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    files.sort()

    rows = []
    for fname in files:
        path = os.path.join(folder_path, fname)
        try:
            with open(path, "r") as f:
                data = json.load(f)
                job_a = data.get("job_a", {})
                job_b = data.get("job_b", {})

                p0a = job_a.get("p_0", 0)
                sigmaa = job_a.get("sigma", 0)
                p0b = job_b.get("p_0", 0)
                sigmab = job_b.get("sigma", 0)

                delta, sigma_total, z = compute_delta_sigma_z(p0a, sigmaa, p0b, sigmab)

                row = {
                    "filename": fname,
                    "job_a_id": job_a.get("id", ""),
                    "job_a_shots": job_a.get("shots", 0),
                    "job_a_0": job_a.get("counts", {}).get("0", 0),
                    "job_a_1": job_a.get("counts", {}).get("1", 0),
                    "job_a_p0": p0a,
                    "job_a_sigma": sigmaa,
                    "job_b_id": job_b.get("id", ""),
                    "job_b_shots": job_b.get("shots", 0),
                    "job_b_0": job_b.get("counts", {}).get("0", 0),
                    "job_b_1": job_b.get("counts", {}).get("1", 0),
                    "job_b_p0": p0b,
                    "job_b_sigma": sigmab,
                    "delta": delta,
                    "sigma_total": sigma_total,
                    "z_value": z
                }
                rows.append(row)

        except Exception as e:
            print(f"Error reading {fname}: {e}", file=sys.stderr)

    # Write CSV
    if rows:
        fieldnames = list(rows[0].keys())
        with open(output_csv, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"[{timestamp()}] CSV saved to {output_csv}")
    else:
        print("No valid data found.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_to_csv.py <folder_path>")
        sys.exit(1)
    main(sys.argv[1])
