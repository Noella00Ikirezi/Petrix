#!/usr/bin/env bash
# Petrix Agent — Installeur Linux
# Usage: bash install-linux.sh --server https://petrix.noellahome.org --token <TOKEN>

set -e
PETRIX_SERVER=""
PETRIX_TOKEN=""

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --server) PETRIX_SERVER="$2"; shift ;;
    --token)  PETRIX_TOKEN="$2";  shift ;;
    *) echo "Option inconnue: $1"; exit 1 ;;
  esac
  shift
done

if [[ -z "$PETRIX_SERVER" || -z "$PETRIX_TOKEN" ]]; then
  echo "Usage: bash install-linux.sh --server URL --token TOKEN"
  exit 1
fi

echo ""
echo "╔══════════════════════════════════════╗"
echo "║       Petrix Agent — Installeur      ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Vérifier / installer Python
if ! command -v python3 &>/dev/null; then
  echo "[*] Installation de Python3..."
  if command -v apt-get &>/dev/null; then
    sudo apt-get install -y python3 python3-pip
  elif command -v yum &>/dev/null; then
    sudo yum install -y python3 python3-pip
  elif command -v dnf &>/dev/null; then
    sudo dnf install -y python3 python3-pip
  else
    echo "[!] Gestionnaire de paquets non supporté. Installez Python 3.9+ manuellement."
    exit 1
  fi
fi

# Vérifier pip
if ! command -v pip3 &>/dev/null && ! python3 -m pip --version &>/dev/null; then
  echo "[*] Installation de pip..."
  python3 -m ensurepip --upgrade || curl -sS https://bootstrap.pypa.io/get-pip.py | python3
fi

# Installer nmap (optionnel mais recommandé)
if ! command -v nmap &>/dev/null; then
  echo "[*] Installation de nmap..."
  if command -v apt-get &>/dev/null; then
    sudo apt-get install -y nmap 2>/dev/null || true
  elif command -v yum &>/dev/null; then
    sudo yum install -y nmap 2>/dev/null || true
  fi
fi

# Installer petrix-agent
echo "[*] Installation de petrix-agent..."
python3 -m pip install --upgrade "git+https://gitlab.com/petrix1/petrix.git#subdirectory=agent" --quiet

# Sauvegarder la config
CONFIG_DIR="$HOME/.petrix-agent"
mkdir -p "$CONFIG_DIR"
cat > "$CONFIG_DIR/config.env" <<EOF
PETRIX_SERVER=$PETRIX_SERVER
PETRIX_TOKEN=$PETRIX_TOKEN
EOF

# Créer un script de lancement
cat > "$CONFIG_DIR/run.sh" <<'EOF'
#!/usr/bin/env bash
source "$HOME/.petrix-agent/config.env"
petrix-agent --server "$PETRIX_SERVER" --token "$PETRIX_TOKEN" "$@"
EOF
chmod +x "$CONFIG_DIR/run.sh"

echo ""
echo "[✓] Petrix Agent installé avec succès."
echo ""
echo "  Lancer un scan : ~/.petrix-agent/run.sh"
echo "  Cible spécifique : ~/.petrix-agent/run.sh --target 192.168.1.0/24"
echo ""

# Lancer immédiatement
read -p "Lancer un scan maintenant ? [O/n] " confirm
if [[ "$confirm" != "n" && "$confirm" != "N" ]]; then
  petrix-agent --server "$PETRIX_SERVER" --token "$PETRIX_TOKEN"
fi
