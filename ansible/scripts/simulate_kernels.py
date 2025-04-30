from dask.distributed import Client
from dask import delayed
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
import numpy as np
import os
import json
import time
from tqdm import tqdm

# Constants
INPUT_DIR = "/mnt/qasm_shared/input/base_train_orig_mnist_784_f90/qasm"
OUTPUT_DIR = "/mnt/qasm_shared/output"
KERNEL_FILE = os.path.join(OUTPUT_DIR, "kernel_matrix.json")
BATCH_SIZE = 5000  # Adjust if needed

def simulate_and_overlap(file1, file2):
    """Load two circuits and prepare statevectors."""
    with open(file1, 'r') as f:
        qasm_code1 = f.read()
    qc1 = QuantumCircuit.from_qasm_str(qasm_code1)

    with open(file2, 'r') as f:
        qasm_code2 = f.read()
    qc2 = QuantumCircuit.from_qasm_str(qasm_code2)

    state1 = Statevector.from_instruction(qc1)
    state2 = Statevector.from_instruction(qc2)

    return delayed(compute_overlap)(state1, state2)

@delayed
def compute_overlap(state1, state2):
    """Compute the overlap between two statevectors."""
    overlap = np.abs(state1.data.conj().dot(state2.data)) ** 2
    return overlap

def main():
    client = Client("localhost:8786")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted([
        os.path.join(INPUT_DIR, f)
        for f in os.listdir(INPUT_DIR)
        if f.endswith(".qasm")
    ])#[:500]

    n = len(files)
    if n == 0:
        print("⚠️ No .qasm files found.")
        return

    print(f"🚀 Computing quantum kernel matrix for {n} circuits...")
    start_time = time.time()

    # Precompute all (i, j) pairs
    keys = []
    pairs = []
    for i in range(n):
        for j in range(i, n):
            keys.append((i, j))
            pairs.append((files[i], files[j]))

    K = np.zeros((n, n))

    print(f"📦 Total overlaps: {len(pairs)}. Processing in batches of {BATCH_SIZE}...")

    for batch_start in tqdm(range(0, len(pairs), BATCH_SIZE), desc="Batches"):
        batch_pairs = pairs[batch_start:batch_start+BATCH_SIZE]
        batch_keys = keys[batch_start:batch_start+BATCH_SIZE]

        # Create batch tasks
        batch_tasks = [simulate_and_overlap(f1, f2) for f1, f2 in batch_pairs]

        # Submit batch
        futures = client.persist(batch_tasks)
        computed = client.gather(futures)

        # 🛠 Fix: force compute any delayed values
        results = [value.compute() if hasattr(value, 'compute') else value for value in computed]

        # Fill K matrix
        for (i, j), value in zip(batch_keys, results):
            K[i, j] = value
            K[j, i] = value  # Symmetric

    # Save kernel matrix
    with open(KERNEL_FILE, "w") as f:
        json.dump(K.tolist(), f)

    elapsed = time.time() - start_time
    print(f"✅ Kernel matrix computed in {elapsed/60:.2f} minutes.")
    print(f"📂 Saved at: {KERNEL_FILE}")

if __name__ == "__main__":
    main()
