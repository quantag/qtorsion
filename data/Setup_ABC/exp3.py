import hashlib
import json
import numpy as np
from datetime import datetime
from qiskit import QuantumCircuit, transpile
from qiskit.qasm3 import dumps as qasm3_dumps, loads as qasm3_loads
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

# Constants (configurable)
PHI = np.pi / 4
THETA = np.pi / 3
SEED = 42
SHOTS = 10000
#BACKEND_NAME = "ibm_brussels"
INSTANCE = "three"
BACKEND_NAME = "ibm_strasbourg"
#INSTANCE = "two"

# Helper functions
def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def filename_timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Quantum circuit generation
def create_torsion_circuit(phi, theta, reverse=False):
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

# Experiment execution
def run_single_experiment(label, phi, theta, reverse, backend, sampler, seed):
    """Runs one circuit variant (A/B/C) and returns job metadata."""
    print(f"[{timestamp()}] Preparing circuit {label}...")
    qc = create_torsion_circuit(phi, theta, reverse)
    qasm3_str = qasm3_dumps(qc)
    qasm3_hash = hashlib.md5(qasm3_str.encode()).hexdigest()

    print(f"[{timestamp()}] Transpiling...")
    tqc = transpile(qasm3_loads(qasm3_str), backend=backend, seed_transpiler=seed)

    print(f"[{timestamp()}] Submitting circuit {label}...")
    job = sampler.run([tqc], shots=SHOTS)
    return {
        "label": label,
        "job_id": job.job_id(),
        "reverse": reverse,
        "phi": phi,
        "theta": theta,
        "qasm3_hash": qasm3_hash
    }

def run_full_experiment():
    """Main function to run all 3 circuits (A, B, C)."""
    print(f"[{timestamp()}] Connecting to {BACKEND_NAME}...")
    service = QiskitRuntimeService()
    backend = service.backend(name=BACKEND_NAME, instance=INSTANCE)
    sampler = SamplerV2(backend)

    results = {
        "timestamp": timestamp(),
        "backend": BACKEND_NAME,
        "shots": SHOTS,
        "seed_transpiler": SEED,
        "jobs": []
    }

    # Run all circuit variants
    for label, reverse in [("A", False), ("B", True), ("C", False)]:
        job_data = run_single_experiment(label, PHI, THETA, reverse, backend, sampler, SEED)
        results["jobs"].append(job_data)
        print(f"[{timestamp()}] Job {label} submitted. ID: {job_data['job_id']}")

    # Save and output
    filename = f"submit_{filename_timestamp()}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[{timestamp()}] Saved to {filename}")

    return [job["job_id"] for job in results["jobs"]]

if __name__ == "__main__":
    job_ids = run_full_experiment()
    print(" ".join(job_ids))  # For manager.py to capture