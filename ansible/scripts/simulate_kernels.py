from dask.distributed import Client, wait, as_completed
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
SUBMISSION_BATCH_SIZE = 5000  # Number of tasks to submit at once
PROCESSING_BATCH_SIZE = 1000  # Number of results to process at once

def load_circuit(filename):
    """Load a circuit from a QASM file and convert to statevector."""
    with open(filename, 'r') as f:
        qasm_code = f.read()
    qc = QuantumCircuit.from_qasm_str(qasm_code)
    return Statevector.from_instruction(qc)

@delayed
def compute_overlap(file1, file2):
    """Load two circuits and compute their overlap."""
    state1 = load_circuit(file1)
    state2 = load_circuit(file2)
    overlap = np.abs(state1.data.conj().dot(state2.data)) ** 2
    return overlap

def chunk_pairs(n, chunk_size=1000):
    """Generate index pairs in chunks to avoid memory issues."""
    total_pairs = (n * (n + 1)) // 2
    chunks = []
    count = 0
    current_chunk = []
    
    for i in range(n):
        for j in range(i, n):
            current_chunk.append((i, j))
            count += 1
            
            if len(current_chunk) >= chunk_size:
                chunks.append(current_chunk)
                current_chunk = []
                
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks, total_pairs

def main():
    client = Client("localhost:8786")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted([
        os.path.join(INPUT_DIR, f)
        for f in os.listdir(INPUT_DIR)
        if f.endswith(".qasm")
    ])[:5000]

    n = len(files)
    if n == 0:
        print("⚠️ No .qasm files found.")
        return

    print(f"🚀 Computing quantum kernel matrix for {n} circuits...")
    start_time = time.time()

    # Pre-generate chunks of index pairs
    index_chunks, total_pairs = chunk_pairs(n, SUBMISSION_BATCH_SIZE)
    print(f"📊 Total pairs: {total_pairs}, divided into {len(index_chunks)} submission chunks")

    # Create an empty kernel matrix to fill
    K = np.zeros((n, n))
    
    # Process chunks of index pairs
    for chunk_idx, index_chunk in enumerate(index_chunks):
        print(f"📦 Processing submission chunk {chunk_idx+1}/{len(index_chunks)}")
        
        # Create futures for this chunk
        futures = []
        for i, j in index_chunk:
            future = compute_overlap(files[i], files[j])
            futures.append((future, i, j))
        
        # Submit all futures at once
        future_objects = [client.compute(f[0]) for f in futures]
        
        # Process results as they complete
        remaining = len(future_objects)
        with tqdm(total=remaining, desc="Processing results") as pbar:
            for batch in as_completed(future_objects).batches():
                # Update progress
                batch_size = len(batch)
                pbar.update(batch_size)
                
                # Get results for this batch
                results = client.gather(batch)
                
                # Update kernel matrix
                for future, result in zip(batch, results):
                    # Find corresponding indices
                    idx = future_objects.index(future)
                    _, i, j = futures[idx]
                    
                    # Update matrix
                    K[i, j] = result
                    K[j, i] = result  # Symmetric matrix
        
        # Clean up to help garbage collection
        del futures
        del future_objects
        
    # Save the kernel matrix
    with open(KERNEL_FILE, "w") as f:
        json.dump(K.tolist(), f)

    elapsed = time.time() - start_time
    print(f"✅ Kernel matrix computed in {elapsed/60:.2f} minutes.")
    print(f"📂 Saved at: {KERNEL_FILE}")

if __name__ == "__main__":
    main()