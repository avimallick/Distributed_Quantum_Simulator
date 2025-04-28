from dask.distributed import Client
from dask import delayed
from qiskit import QuantumCircuit, ClassicalRegister
from qiskit.quantum_info import Statevector
import numpy as np
import os
import json
import time
from tqdm import tqdm

INPUT_DIR = "/mnt/qasm_shared/input/base_train_orig_mnist_784_f90/qasm"
OUTPUT_DIR = "/mnt/qasm_shared/output"
KERNEL_FILE = os.path.join(OUTPUT_DIR, "kernel_matrix.json")

@delayed
def simulate_and_overlap(file1, file2):
    """Simulate two circuits and compute their overlap."""
    with open(file1, 'r') as f:
        qasm_code1 = f.read()
    qc1 = QuantumCircuit.from_qasm_str(qasm_code1)
    if qc1.num_clbits == 0:
        qc1.add_register(ClassicalRegister(qc1.num_qubits))
        qc1.measure_all()
    state1 = Statevector.from_instruction(qc1)

    with open(file2, 'r') as f:
        qasm_code2 = f.read()
    qc2 = QuantumCircuit.from_qasm_str(qasm_code2)
    if qc2.num_clbits == 0:
        qc2.add_register(ClassicalRegister(qc2.num_qubits))
        qc2.measure_all()
    state2 = Statevector.from_instruction(qc2)

    overlap = np.abs(state1.data.conj().dot(state2.data)) ** 2
    return overlap


def main():
    client = Client("localhost:8786")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted([
        os.path.join(INPUT_DIR, f)
        for f in os.listdir(INPUT_DIR)
        if f.endswith(".qasm")
    ])[:500]

    n = len(files)
    if n == 0:
        print("⚠️ No .qasm files found.")
        return

    print(f"🚀 Computing quantum kernel matrix for {n} circuits...")
    start_time = time.time()

    # Create tasks
    keys = []
    tasks = []
    for i in range(n):
        for j in range(i, n):
            keys.append((i, j))
            tasks.append(simulate_and_overlap(files[i], files[j]))

    print("⏳ Submitting tasks to Dask cluster...")

    # Persist and Gather
    futures = client.persist(tasks)
    results_list = client.gather(futures)  # 👈👈 BIG CHANGE HERE

    # Build result mapping
    results = dict(zip(keys, results_list))

    # Build symmetric kernel matrix
    K = np.zeros((n, n))
    for (i, j), value in results.items():
        K[i, j] = value
        K[j, i] = value

    with open(KERNEL_FILE, "w") as f:
        json.dump(K.tolist(), f)

    elapsed = time.time() - start_time
    print(f"✅ Kernel matrix computed in {elapsed/60:.2f} minutes.")
    print(f"📂 Saved at: {KERNEL_FILE}")

if __name__ == "__main__":
    main()
