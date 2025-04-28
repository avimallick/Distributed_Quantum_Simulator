variable "img_display_name" {
  type    = string
  default = "ubuntu-22.04-20241206-jammy-server-cloudimg-amd64.img"
}

variable "namespace" {
  type    = string
  default = "ucab252-comp0235-ns"
}

variable "network_name" {
  type    = string
  default = "ucab252-comp0235-ns/ds4eng"
}

variable "username" {
  type    = string
  default = "ucab252"
}

variable "keyname" {
  type    = string
  default = "ubuntu-cnc"
}

variable "vm_count" {
  type    = number
  default = 4
}

variable "install_ansible" {
  type    = bool
  default = true
}