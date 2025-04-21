import os
from qiskit import QuantumCircuit

def load_qasm_circuits(qasm_dir):
    circuits = []
    for filename in os.listdir(qasm_dir):
        if filename.endswith(".qasm"):
            filepath = os.path.join(qasm_dir, filename)
            try:
                circuit = QuantumCircuit.from_qasm_file(filepath)
                circuits.append(circuit)
                print(f"Loaded circuit from {filename}")
            except Exception as e:
                print(f"Failed to load {filename}: {e}")
    return circuits

if __name__ == "__main__":
    qasm_dir = os.getenv("QASM_DIR", "/mnt/simulation_data/qasm_circuits")
    circuits = load_qasm_circuits(qasm_dir)
    print(f"Total circuits loaded: {len(circuits)}")