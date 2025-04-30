
# Quantum Circuit Simulation on Distributed Dask Cluster

## Overview
This project sets up a Distributed Quantum Circuit Simulation platform across a custom-built Dask Cluster using Ubuntu VMs. It is designed to simulate quantum circuits at scale, distributed across multiple machines, while being fully monitored using Prometheus and Grafana.

The simulation dataset is the MNISQ Quantum Circuit Dataset, derived from encoding classical MNIST images into quantum circuits.

The full setup, automation, and simulation execution were performed via Terraform (for VM provisioning) and Ansible (for configuration management), ensuring complete reproducibility.

---

## Project Structure
```
terraform/                # Terraform files to provision management and worker nodes
ansible/
  inventory.ini            # Ansible inventory file (management and worker nodes)
  01_initial_setup/        # Mount disks, install base packages
  02_glusterfs_setup/      # Setup distributed storage (GlusterFS)
  03_dask_setup/           # Install Dask, configure Scheduler & Workers (systemd)
  04_monitoring_setup/     # Setup Prometheus, Node Exporter, Grafana
  05_simulation_setup/     # Download datasets, run distributed simulation
scripts/
  simulate_circuits.py     # Dask-distributed quantum simulation script
```

---

## Setup Flow

### 1. Infrastructure Provisioning
Use Terraform to create 1 Management Node + 4 Worker Nodes on Ubuntu 22.04.

### 2. Initial Setup
- Format and mount /dev/vdb as /mnt/simulation_data (200GB disk)
- Install python3, pip3, tmux, and basic system packages
- Setup passwordless SSH access

### 3. Distributed Storage (GlusterFS)
- Install GlusterFS on all worker nodes
- Probe and create a distributed Gluster volume
- Mount shared storage at /mnt/qasm_shared across all nodes

### 4. Dask Distributed Cluster
- Install Dask (dask[distributed], bokeh) on all machines
- Deploy Dask Scheduler as a systemd service on Management Node
- Deploy Dask Workers as systemd services on Worker Nodes

### 5. Monitoring
- Install Prometheus and Node Exporters
- Install Grafana
- Prometheus scrapes Dask metrics, Node metrics every 15s
- Grafana dashboards visualize live system health and Dask task distributions

### 6. Simulation Execution
- Download MNISQ dataset (base_train_orig_mnist_784_f90)
- Extract QASM files into /mnt/qasm_shared/input/
- Run simulate_circuits.py script to distribute and simulate all quantum circuits
- Output saved into /mnt/qasm_shared/output/

---

## How to Run

Provision infrastructure using Terraform:
```bash
cd terraform/
terraform init
terraform apply
```

Configure all nodes using Ansible:
> **Important:** All playbooks are organized in numbered directories. Run each sequentially like this:
```bash
cd ansible/
ansible-playbook -i inventory.ini 01_initial_setup/disk_mount.yml
ansible-playbook -i inventory.ini 02_glusterfs_setup/01_install_and_peer.yml
ansible-playbook -i inventory.ini 02_glusterfs_setup/02_create_volume.yml
ansible-playbook -i inventory.ini 02_glusterfs_setup/03_mount_volume.yml
ansible-playbook -i inventory.ini 03_dask_setup/01_dask_setup.yml
ansible-playbook -i inventory.ini 03_dask_setup/02_dask_services.yml
ansible-playbook -i inventory.ini 04_monitoring_setup/00_install_node_exporter.yml
ansible-playbook -i inventory.ini 04_monitoring_setup/01_install_prometheus.yml
ansible-playbook -i inventory.ini 04_monitoring_setup/02_install_grafana.yml
ansible-playbook -i inventory.ini 05_simulation_setup/01_Download_dataset.yml
ansible-playbook -i inventory.ini 05_simulation_setup/02_install_qiskit.yml
ansible-playbook -i inventory.ini 05_simulation_setup/03_push_and_run_simulations.yml
```

### SSH Tunnel Setup (if accessing Grafana/Prometheus from local machine):
```bash
ssh -L 3000:10.134.12.65:3000 -L 9090:10.134.12.65:9090 ubuntu@<CNC_VM_PUBLIC_IP>
```

### To Start Simulation:
```bash
python3 scripts/simulate_circuits.py
```

This script will automatically connect to Dask Scheduler, distribute quantum circuit simulations.  
Monitor progress live in Grafana!

---

## 🔄 Swapping Datasets (User Instructions)

Users can run simulations on any `.qasm` dataset by following these steps:

1. **Upload Your Own QASM Files**
   ```bash
   scp *.qasm ubuntu@<management-node>:/mnt/qasm_shared/input/custom_dataset/
   ```

2. **Update the Simulation Script**
   In `scripts/simulate_circuits.py`, modify this line:
   ```python
   INPUT_DIR = "/mnt/qasm_shared/input/custom_dataset"
   ```

3. **Optional: Adjust Batch Size**
   By default, the script processes the first 500 files:
   ```python
   files = sorted([...])[:500]
   ```
   Comment or edit this line to simulate the full dataset.

4. **Re-run Simulation**
   ```bash
   ansible-playbook 05_simulation_setup/03_push_and_run_simulations.yml
   ```

---

## 🌐 Public QASM Dataset Sources

- **MNISQ Quantum Circuit Dataset**  
  https://github.com/FujiiLabCollaboration/MNISQ-quantum-circuit-dataset

- **QASMBench Quantum Benchmark Suite**  
  https://github.com/quantumlib/qasmbench

- **Qiskit Community Tutorials**  
  https://github.com/Qiskit/qiskit-community-tutorials

- **Quantum Datasets on Kaggle**  
  https://www.kaggle.com/search?q=qasm

---

## Key Technologies Used
- Terraform for infrastructure provisioning
- Ubuntu 22.04 VMs
- Ansible for full automation
- GlusterFS for distributed storage
- Dask Distributed for cluster-wide parallelism
- Qiskit + Qiskit-Aer for quantum circuit simulation
- Prometheus + Grafana for cluster monitoring

---

## Notes
- Scheduler and Worker services are managed via systemd.
- Prometheus targets scrape Dask Scheduler metrics (/metrics endpoint).
- Grafana dashboards include live tracking of Workers, CPU usage, Memory, and Tasks.
- Project setup verified for Dask version 2025.x (latest CLI changes considered).
- Resilient to reboots; services auto-restart.

---

## License
This project is created for educational purposes as part of COMP0239 coursework.
