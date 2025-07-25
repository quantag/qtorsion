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

def analyze(job_id_a, job_id_b):
    data_a = get_result(job_id_a)
    data_b = get_result(job_id_b)

    if not data_a or not data_b:
        output = {
            "error": "One of the jobs is not complete.",
            "job_a_status": data_a is not None,
            "job_b_status": data_b is not None
        }
        print(json.dumps(output, indent=2))
        return

    pA = data_a["p0"]
    pB = data_b["p0"]
    sigmaA = data_a["sigma"]
    sigmaB = data_b["sigma"]
    delta = abs(pA - pB)
    sigma_total = math.sqrt(sigmaA**2 + sigmaB**2)
    Z = delta / sigma_total if sigma_total > 0 else float("inf")

    result_json = {
        "timestamp": timestamp(),
        "job_a": {
            "id": data_a["job_id"],
            "counts": data_a["counts"],
            "shots": data_a["shots"],
            "p_0": round(pA, 5),
            "sigma": round(sigmaA, 5)
        },
        "job_b": {
            "id": data_b["job_id"],
            "counts": data_b["counts"],
            "shots": data_b["shots"],
            "p_0": round(pB, 5),
            "sigma": round(sigmaB, 5)
        },
        "delta": round(delta, 5),
        "sigma_total": round(sigma_total, 5),
        "z_value": "inf" if math.isinf(Z) else round(Z, 2)
    }

    print(json.dumps(result_json, indent=2))

    # Save to file
    filename = f"results_{timestamp_for_filename()}.json"
    with open(filename, "w") as f:
        json.dump(result_json, f, indent=2)
    print(f"[{timestamp()}] Saved to {filename}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python analyze.py <job_id_A> <job_id_B>")
        sys.exit(1)
    analyze(sys.argv[1], sys.argv[2])
