variable "aws_region" {
  default = "eu-west-1"
}

variable "petrix_ec2_ip" {
  description = "IP publique du serveur Petrix (pour autoriser les audits SSH)"
  default     = "3.255.126.244"
}

variable "local_ip" {
  description = "Ton IP locale pour accès SSH direct (demo)"
}

variable "ssh_public_key" {
  description = "Clé publique SSH pour accéder aux VMs de démo"
}

variable "demo_password" {
  description = "Mot de passe utilisateur petrix-demo sur les VMs"
  sensitive   = true
}
