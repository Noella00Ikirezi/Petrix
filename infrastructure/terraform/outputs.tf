output "targets" {
  description = "Infos de connexion pour les cibles Petrix"
  value = {
    ubuntu = {
      ip       = aws_instance.ubuntu_target.public_ip
      os_type  = "linux"
      username = "petrix-demo"
      note     = "Config SSH intentionnellement vulnérable — audit intéressant"
    }
    amazon_linux = {
      ip       = aws_instance.amazonlinux_target.public_ip
      os_type  = "linux"
      username = "petrix-demo"
      note     = "Config SSH par défaut — bon score attendu"
    }
    windows = {
      ip       = aws_instance.windows_target.public_ip
      os_type  = "windows"
      username = "petrix-demo"
      note     = "Windows Server 2022 avec OpenSSH"
    }
  }
}

output "petrix_targets_json" {
  description = "Copier-coller dans Petrix pour créer les targets"
  value = jsonencode([
    {
      name     = "Ubuntu 22.04 (demo)"
      host     = aws_instance.ubuntu_target.public_ip
      port     = 22
      username = "petrix-demo"
      os_type  = "linux"
    },
    {
      name     = "Amazon Linux 2023 (demo)"
      host     = aws_instance.amazonlinux_target.public_ip
      port     = 22
      username = "petrix-demo"
      os_type  = "linux"
    },
    {
      name     = "Windows Server 2022 (demo)"
      host     = aws_instance.windows_target.public_ip
      port     = 22
      username = "petrix-demo"
      os_type  = "windows"
    }
  ])
}

output "cost_estimate" {
  value = "~$0.07/heure pour les 3 VMs (t3.micro x2 + t3.small x1). Penser à 'terraform destroy' après la démo."
}
