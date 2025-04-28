# Data sources for image and SSH key
data "harvester_image" "img" {
  display_name = var.img_display_name
  namespace    = "harvester-public"
}

data "harvester_ssh_key" "mysshkey" {
  name      = var.keyname
  namespace = var.namespace
}

# Random ID for unique resource naming
resource "random_id" "secret" {
  byte_length = 5
}

# Cloud-init secret (includes Docker & Ansible setup)
resource "harvester_cloudinit_secret" "cloud-config" {
  name      = "cloud-config-${random_id.secret.hex}"
  namespace = var.namespace

  user_data = templatefile("cloud-init-template.yml", {
    public_key_openssh = data.harvester_ssh_key.mysshkey.public_key,
    lecturer_key       = file("${path.module}/lecturer_key.pub"),
    install_docker     = true,
    install_ansible    = true
  })
}

# Management Node
resource "harvester_virtualmachine" "mgmtvm" {
  count                = 1
  name                 = "${var.username}-mgmt-${random_id.secret.hex}"
  namespace            = var.namespace
  restart_after_update = true
  description          = "Management_Node_for_Quantum_Circuit_Simulation"
  cpu                  = 2
  memory               = "4Gi"
  efi                  = true
  secure_boot          = false
  run_strategy         = "RerunOnFailure"
  hostname             = "${var.username}-mgmt-${random_id.secret.hex}"
  reserved_memory      = "100Mi"
  machine_type         = "q35"

  network_interface {
    name           = "nic-1"
    wait_for_lease = true
    type           = "bridge"
    network_name   = var.network_name
  }

  disk {
    name        = "rootdisk"
    type        = "disk"
    size        = "10Gi"
    bus         = "virtio"
    boot_order  = 1
    image       = data.harvester_image.img.id
    auto_delete = true
  }

  cloudinit {
    user_data_secret_name = harvester_cloudinit_secret.cloud-config.name
  }

  tags = {
    role            = "management"
    description     = "Orchestrates_worker_nodes_and_distributes_workloads"
    install_ansible = "true"
    install_docker  = "true"
  }
}

# Worker Nodes (Quantum Simulation Nodes)
resource "harvester_virtualmachine" "worker" {
  count                = 4
  name                 = "${var.username}-worker-${format("%02d", count.index + 1)}-${random_id.secret.hex}"
  namespace            = var.namespace
  restart_after_update = true
  description          = "Worker_Node_for_Quantum_Circuit_Execution"
  cpu                  = 4
  memory               = "32Gi"
  efi                  = true
  secure_boot          = false
  run_strategy         = "RerunOnFailure"
  hostname             = "${var.username}-worker-${format("%02d", count.index + 1)}-${random_id.secret.hex}"
  reserved_memory      = "100Mi"
  machine_type         = "q35"

  network_interface {
    name           = "nic-1"
    wait_for_lease = true
    type           = "bridge"
    network_name   = var.network_name
  }

  disk {
    name        = "rootdisk"
    type        = "disk"
    size        = "50Gi"
    bus         = "virtio"
    boot_order  = 1
    image       = data.harvester_image.img.id
    auto_delete = true
  }

  disk {
    name        = "datadisk"
    type        = "disk"
    size        = "200Gi"
    bus         = "virtio"
    auto_delete = true
  }

  cloudinit {
    user_data_secret_name = harvester_cloudinit_secret.cloud-config.name
  }

  tags = {
    role           = "worker"
    description    = "Runs_distributed_quantum_circuit_simulations"
    install_docker = "true"
    install_qiskit = "true"
    install_mpi    = "true"
    install_spark  = "true"
    install_dask   = "true"
    install_quest  = "true"
  }
}