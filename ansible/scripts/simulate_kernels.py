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
KERNEL_FILE = os.path.join(OUTPUT_DIR, "kernel_matrix_debug_perf.json")
NUM_FILES = 2000  # Reduced number of files for debugging
SUBMISSION_BATCH_SIZE = 10000  # Smaller batch size for debugging
PROCESSING_BATCH_SIZE = 2000   # Smaller processing batch for debugging

def load_circuit(filename):
    """Load a circuit from a QASM file and convert to statevector."""
    try:
        with open(filename, 'r') as f:
            qasm_code = f.read()
        qc = QuantumCircuit.from_qasm_str(qasm_code)
        return Statevector.from_instruction(qc)
    except Exception as e:
        print(f"Error loading circuit from {filename}: {e}")
        raise

@delayed
def compute_overlap(file1, file2):
    """Load two circuits and compute their overlap."""
    try:
        state1 = load_circuit(file1)
        state2 = load_circuit(file2)
        overlap = np.abs(state1.data.conj().dot(state2.data)) ** 2
        return overlap
    except Exception as e:
        print(f"Error computing overlap between {file1} and {file2}: {e}")
        raise

def main():
    # Add verbose output for debugging
    print(f"Starting debug run with {NUM_FILES} files")
    print(f"Input directory: {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    try:
        client = Client("localhost:8786")
        print(f"Connected to Dask cluster: {client}")
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        print(f"Ensured output directory exists: {OUTPUT_DIR}")

        # Get QASM files
        all_files = sorted([
            os.path.join(INPUT_DIR, f)
            for f in os.listdir(INPUT_DIR)
            if f.endswith(".qasm")
        ])
        
        if len(all_files) == 0:
            print(f"⚠️ No QASM files found in {INPUT_DIR}")
            return
            
        print(f"Found {len(all_files)} total QASM files")
        
        # Take only the first NUM_FILES files
        files = all_files[:NUM_FILES]
        print(f"Using first {len(files)} files for debug run")

        n = len(files)
        print(f"🚀 Computing quantum kernel matrix for {n} circuits...")
        start_time = time.time()

        # Create an empty kernel matrix to fill
        K = np.zeros((n, n))
        
        # For debugging, generate all pairs upfront
        pairs = []
        for i in range(n):
            for j in range(i, n):
                pairs.append((i, j))
        
        total_pairs = len(pairs)
        print(f"Total pairs to compute: {total_pairs}")
        
        # Process in smaller batches for debugging
        for batch_start in range(0, total_pairs, SUBMISSION_BATCH_SIZE):
            batch_end = min(batch_start + SUBMISSION_BATCH_SIZE, total_pairs)
            current_pairs = pairs[batch_start:batch_end]
            
            print(f"Processing batch {batch_start//SUBMISSION_BATCH_SIZE + 1}: pairs {batch_start} to {batch_end-1}")
            
            # Create futures for this batch
            futures = []
            for i, j in current_pairs:
                future = compute_overlap(files[i], files[j])
                futures.append((future, i, j))
            
            # Submit all futures at once
            print(f"Submitting {len(futures)} tasks to Dask")
            future_objects = [client.compute(f[0]) for f in futures]
            
            # Process results as they complete
            print("Waiting for results...")
            with tqdm(total=len(future_objects), desc="Processing results") as pbar:
                for batch in as_completed(future_objects).batches():
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
        print(f"Saving kernel matrix to {KERNEL_FILE}")
        with open(KERNEL_FILE, "w") as f:
            json.dump(K.tolist(), f)

        elapsed = time.time() - start_time
        print(f"✅ Debug kernel matrix computed in {elapsed:.2f} seconds.")
        print(f"📂 Saved at: {KERNEL_FILE}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()