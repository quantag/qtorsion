import hashlib
import json
import numpy as np
from datetime import datetime
from qiskit import QuantumCircuit, transpile
from qiskit.qasm3 import dumps as qasm3_dumps, loads as qasm3_loads
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def filename_timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def torsion_test_circuit(phi, theta, reverse=False):
    qc = QuantumCircuit(1, 1)
    qc.h(0)
    if not reverse:
        qc.rz(phi, 0)
        qc.ry(theta, 0)
        qc.rz(-phi, 0)
        qc.ry(-theta, 0)
    else:
        qc.ry(theta, 0)
        qc.rz(phi, 0)
        qc.ry(-theta, 0)
        qc.rz(-phi, 0)
    qc.h(0)
    qc.measure(0, 0)
    return qc

# Parameters
phi = np.pi / 4
theta = np.pi / 3
seed = 42
shots = 10000
backend_name = "ibm_torino"
instance = "one"

print(f"[{timestamp()}] Connecting to IBM backend...")
service = QiskitRuntimeService()
backend = service.backend(name=backend_name, instance=instance)
sampler = SamplerV2(backend)

results = {
    "timestamp": timestamp(),
    "backend": backend_name,
    "shots": shots,
    "seed_transpiler": seed,
    "jobs": []
}

for label, reverse in [("A", False), ("B", True)]:
    print(f"\n[{timestamp()}] Preparing circuit {label}...")
    qc = torsion_test_circuit(phi, theta, reverse=reverse)
    qasm3_str = qasm3_dumps(qc)
    qasm3_hash = hashlib.md5(qasm3_str.encode()).hexdigest()

    print(f"[{timestamp()}] Transpiling...")
    tqc = transpile(qasm3_loads(qasm3_str), backend=backend, seed_transpiler=seed)

    print(f"[{timestamp()}] Submitting circuit {label} to IBM Q...")
    job = sampler.run([tqc], shots=shots)
    job_id = job.job_id()
    print(f"[{timestamp()}] Job {label} submitted. Job ID: {job_id}")

    results["jobs"].append({
        "label": label,
        "job_id": job_id,
        "reverse": reverse,
        "phi": phi,
        "theta": theta,
        "qasm3_hash": qasm3_hash
    })

# Final output
job_ids = " ".join([j["job_id"] for j in results["jobs"]])
print(f"\n{job_ids}")

# Save to file
filename = f"submit_{filename_timestamp()}.json"
with open(filename, "w") as f:
    json.dump(results, f, indent=2)

print(f"[{timestamp()}] Saved job info to {filename}")
