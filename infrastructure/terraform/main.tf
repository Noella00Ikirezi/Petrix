terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ---------------------------------------------------------------------------
# Clé SSH partagée pour toutes les VMs de démo
# ---------------------------------------------------------------------------
resource "aws_key_pair" "demo" {
  key_name   = "petrix-demo-targets"
  public_key = var.ssh_public_key
}

# ---------------------------------------------------------------------------
# Security Group — cibles de démo
# Autorise SSH depuis le backend Petrix + ton IP locale
# ---------------------------------------------------------------------------
resource "aws_security_group" "demo_targets" {
  name        = "petrix-demo-targets"
  description = "Acces SSH pour audit hardening Petrix"

  ingress {
    description = "SSH depuis Petrix backend"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${var.petrix_ec2_ip}/32"]
  }

  ingress {
    description = "SSH depuis machine locale (demo)"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${var.local_ip}/32"]
  }

  ingress {
    description = "RDP Windows (optionnel)"
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["${var.local_ip}/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "petrix-demo-targets", Project = "petrix" }
}

# ---------------------------------------------------------------------------
# AMIs — dernières versions automatiquement
# ---------------------------------------------------------------------------
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter { name = "virtualization-type"; values = ["hvm"] }
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }
  filter { name = "virtualization-type"; values = ["hvm"] }
}

data "aws_ami" "windows" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["Windows_Server-2022-English-Full-Base-*"]
  }
  filter { name = "virtualization-type"; values = ["hvm"] }
}

# ---------------------------------------------------------------------------
# VM 1 — Ubuntu 22.04 (Linux cible intentionnellement mal configurée)
# ---------------------------------------------------------------------------
resource "aws_instance" "ubuntu_target" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.micro"
  key_name               = aws_key_pair.demo.key_name
  vpc_security_group_ids = [aws_security_group.demo_targets.id]

  # Intentionnellement mal configuré pour rendre l'audit intéressant
  user_data = <<-EOF
    #!/bin/bash
    # Activer SSH par mot de passe (vulnérabilité volontaire pour la démo)
    sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
    sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
    echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
    echo "X11Forwarding yes" >> /etc/ssh/sshd_config

    # Créer l'utilisateur demo avec mot de passe simple
    useradd -m -s /bin/bash petrix-demo || true
    echo "petrix-demo:${var.demo_password}" | chpasswd
    usermod -aG sudo petrix-demo

    # Autoriser sudo sans mot de passe (mauvaise pratique volontaire)
    echo "petrix-demo ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/petrix-demo

    # Désactiver le pare-feu (ufw)
    ufw disable 2>/dev/null || true

    # Redémarrer SSH
    systemctl restart sshd
  EOF

  tags = {
    Name    = "petrix-demo-ubuntu"
    OS      = "linux"
    Distro  = "ubuntu-22.04"
    Project = "petrix"
    Role    = "hardening-target"
  }
}

# ---------------------------------------------------------------------------
# VM 2 — Amazon Linux 2023 (Linux propre pour comparer)
# ---------------------------------------------------------------------------
resource "aws_instance" "amazonlinux_target" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t3.micro"
  key_name               = aws_key_pair.demo.key_name
  vpc_security_group_ids = [aws_security_group.demo_targets.id]

  user_data = <<-EOF
    #!/bin/bash
    # Config SSH par défaut — laissée telle quelle pour comparer avec Ubuntu
    # Créer un utilisateur demo
    useradd -m -s /bin/bash petrix-demo || true
    echo "petrix-demo:${var.demo_password}" | chpasswd
    usermod -aG wheel petrix-demo
    echo "petrix-demo ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/petrix-demo
  EOF

  tags = {
    Name    = "petrix-demo-amazonlinux"
    OS      = "linux"
    Distro  = "amazon-linux-2023"
    Project = "petrix"
    Role    = "hardening-target"
  }
}

# ---------------------------------------------------------------------------
# VM 3 — Windows Server 2022 (SSH via OpenSSH natif)
# ---------------------------------------------------------------------------
resource "aws_instance" "windows_target" {
  ami                    = data.aws_ami.windows.id
  instance_type          = "t3.small"
  key_name               = aws_key_pair.demo.key_name
  vpc_security_group_ids = [aws_security_group.demo_targets.id]

  # Activer OpenSSH sur Windows via PowerShell
  user_data = <<-EOF
    <powershell>
    # Installer OpenSSH
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
    Start-Service sshd
    Set-Service -Name sshd -StartupType Automatic

    # Configurer le shell par défaut pour SSH
    New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell `
      -Value "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" `
      -PropertyType String -Force

    # Créer un utilisateur de démo
    $Password = ConvertTo-SecureString "${var.demo_password}" -AsPlainText -Force
    New-LocalUser "petrix-demo" -Password $Password -FullName "Petrix Demo" -PasswordNeverExpires
    Add-LocalGroupMember -Group "Administrators" -Member "petrix-demo"

    # Autoriser le mot de passe dans SSH (pour la démo)
    (Get-Content C:\ProgramData\ssh\sshd_config) -replace '#PasswordAuthentication yes', 'PasswordAuthentication yes' |
      Set-Content C:\ProgramData\ssh\sshd_config
    Restart-Service sshd
    </powershell>
  EOF

  tags = {
    Name    = "petrix-demo-windows"
    OS      = "windows"
    Distro  = "windows-server-2022"
    Project = "petrix"
    Role    = "hardening-target"
  }
}
