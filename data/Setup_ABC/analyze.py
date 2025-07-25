import sys
import math
import json
import numpy as np
from qiskit_ibm_runtime import QiskitRuntimeService
from datetime import datetime

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def timestamp_for_filename():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def get_result(job_id):
    print("[" + timestamp() + "] Getting job " + job_id)
    service = QiskitRuntimeService()
    job = service.job(job_id)

    if job.status() != "DONE":
        print("[" + timestamp() + "] Job is not DONE.")
        return None

    result = job.result()
    bitarray = result[0].data.c

    arr = bitarray._array
    num_shots = arr.shape[0]
    num_bits = bitarray.num_bits

    counts = {}
    for row in arr:
        bitstr = ''.join(str(b) for b in row[:num_bits])
        counts[bitstr] = counts.get(bitstr, 0) + 1

    p0 = counts.get("0", 0) / num_shots
    sigma = math.sqrt(p0 * (1 - p0) / num_shots)

    return {
        "job_id": job_id,
        "counts": counts,
        "shots": num_shots,
        "p0": p0,
        "sigma": sigma
    }

def analyze(job_id_a, job_id_b, job_id_c):
    data_a = get_result(job_id_a)
    data_b = get_result(job_id_b)
    data_c = get_result(job_id_c)

    if not all([data_a, data_b, data_c]):
        output = {
            "error": "One or more jobs are not complete.",
            "job_a_status": data_a is not None,
            "job_b_status": data_b is not None,
            "job_c_status": data_c is not None
        }
        print(json.dumps(output, indent=2))
        return

    def compute_z(p1, p2, s1, s2):
        delta = abs(p1 - p2)
        sigma_total = math.sqrt(s1**2 + s2**2)
        Z = delta / sigma_total if sigma_total > 0 else float("inf")
        return delta, sigma_total, Z

    delta_ab, sigma_ab, z_ab = compute_z(data_a["p0"], data_b["p0"], data_a["sigma"], data_b["sigma"])
    delta_ac, sigma_ac, z_ac = compute_z(data_a["p0"], data_c["p0"], data_a["sigma"], data_c["sigma"])

    epsilon = 1e-9
    z_eff = z_ab / (z_ac + epsilon)

    result_json = {
        "timestamp": timestamp(),
        "job_a": {
            "id": data_a["job_id"],
            "p_0": round(data_a["p0"], 5),
            "sigma": round(data_a["sigma"], 5),
            "shots": data_a["shots"],
            "counts": data_a["counts"]
        },
        "job_b": {
            "id": data_b["job_id"],
            "p_0": round(data_b["p0"], 5),
            "sigma": round(data_b["sigma"], 5),
            "shots": data_b["shots"],
            "counts": data_b["counts"]
        },
        "job_c": {
            "id": data_c["job_id"],
            "p_0": round(data_c["p0"], 5),
            "sigma": round(data_c["sigma"], 5),
            "shots": data_c["shots"],
            "counts": data_c["counts"]
        },
        "z_ab": round(z_ab, 3),
        "z_ac": round(z_ac, 3),
        "z_eff": "inf" if math.isinf(z_eff) else round(z_eff, 3)
    }

    print(json.dumps(result_json, indent=2))

    # Save to file
    filename = f"results3_{timestamp_for_filename()}.json"
    with open(filename, "w") as f:
        json.dump(result_json, f, indent=2)
    print(f"[{timestamp()}] Saved to {filename}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python analyze3.py <job_id_A> <job_id_B> <job_id_C>")
        sys.exit(1)
    analyze(sys.argv[1], sys.argv[2], sys.argv[3])
