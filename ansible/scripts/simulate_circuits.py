from dask.distributed import Client, as_completed
from dask import delayed
from qiskit import QuantumCircuit, ClassicalRegister
from qiskit_aer import AerSimulator
import os
import json
import time
from tqdm import tqdm

INPUT_DIR = "/mnt/qasm_shared/input/base_train_orig_mnist_784_f90/qasm"
OUTPUT_DIR = "/mnt/qasm_shared/output"
SHOTS = 16384  # More realistic simulation per circuit

@delayed
def simulate_qasm(file_path):
    with open(file_path, 'r') as f:
        qasm_code = f.read()
    qc = QuantumCircuit.from_qasm_str(qasm_code)

    # Add classical bits and measurements if missing
    if qc.num_clbits == 0:
        qc.add_register(ClassicalRegister(qc.num_qubits))
        qc.measure_all()

    backend = AerSimulator()
    job = backend.run(qc, shots=SHOTS)
    result = job.result().get_counts()

    out_path = os.path.join(OUTPUT_DIR, os.path.basename(file_path) + ".json")
    with open(out_path, "w") as f:
        json.dump(result, f)
    return out_path

def main():
    client = Client("localhost:8786")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted([
        os.path.join(INPUT_DIR, f)
        for f in os.listdir(INPUT_DIR)
        if f.endswith(".qasm")
    ])

    if not files:
        print("⚠️ No .qasm files found — please check your input path or file extensions.")
        return

    print(f"🚀 Launching simulation of {len(files)} quantum circuits with {SHOTS} shots each...")
    start_time = time.time()

    tasks = [simulate_qasm(f) for f in files]
    futures = client.compute(tasks)

    # Use tqdm to show live progress
    results = []
    for future in tqdm(as_completed(futures), total=len(futures), desc="Simulating Circuits"):
        results.append(future.result())

    elapsed = time.time() - start_time
    print(f"✅ Simulation completed in {elapsed/60:.2f} minutes.")
    print(f"📂 Output directory: {OUTPUT_DIR}")
    print(f"📝 Example files: {results[:5]} ...")

if __name__ == "__main__":
    main()
