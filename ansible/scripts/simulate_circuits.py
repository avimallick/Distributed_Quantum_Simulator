from dask.distributed import Client
from dask import delayed
import os
from qiskit import QuantumCircuit, Aer, execute
import json

INPUT_DIR = "/mnt/simulation_data/input"
OUTPUT_DIR = "/mnt/simulation_data/output"

@delayed
def simulate_qasm(file_path):
    with open(file_path, 'r') as f:
        qasm_str = f.read()
    
    qc = QuantumCircuit.from_qasm_str(qasm_str)
    backend = Aer.get_backend('qasm_simulator')
    job = execute(qc, backend, shots=1024)
    result = job.result().get_counts()

    output_file = os.path.join(OUTPUT_DIR, os.path.basename(file_path) + ".json")
    with open(output_file, 'w') as out:
        json.dump(result, out)
    
    return output_file

def main():
    client = Client("localhost:8786")
    qasm_files = [os.path.join(INPUT_DIR, f) for f in os.listdir(INPUT_DIR) if f.endswith(".qasm")]
    tasks = [simulate_qasm(f) for f in qasm_files]
    results = client.gather(client.compute(tasks))
    print("Simulation complete. Output files:")
    print(results)

if __name__ == "__main__":
    main()
