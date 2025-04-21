import os
import sys
from dask.distributed import Client
from qiskit import Aer, execute

def simulate_circuit(circuit):
    simulator = Aer.get_backend('qasm_simulator')
    result = execute(circuit, backend=simulator).result()
    return result.get_counts()

if __name__ == "__main__":
    # Get scheduler address from command-line argument
    scheduler_address = sys.argv[1] if len(sys.argv) > 1 else "tcp://localhost:8786"
    client = Client(scheduler_address)
    
    # Load circuits (replace this with your actual loading logic)
    circuits = []  # Load from a file or another source
    futures = client.map(simulate_circuit, circuits)
    results = client.gather(futures)
    
    # Save results
    with open("/mnt/simulation_data/results.txt", "w") as f:
        for result in results:
            f.write(f"{result}\n")
    print("Simulations completed and results saved.")