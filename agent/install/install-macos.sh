#!/usr/bin/env bash
# Petrix Agent — Installeur macOS
set -e
PETRIX_SERVER=""
PETRIX_TOKEN=""

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --server) PETRIX_SERVER="$2"; shift ;;
    --token)  PETRIX_TOKEN="$2";  shift ;;
  esac
  shift
done

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   Petrix Agent — Installeur macOS    ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Homebrew si absent
if ! command -v brew &>/dev/null; then
  echo "[*] Installation de Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Python
if ! command -v python3 &>/dev/null; then
  echo "[*] Installation de Python3..."
  brew install python3
fi

# nmap (optionnel)
if ! command -v nmap &>/dev/null; then
  echo "[*] Installation de nmap..."
  brew install nmap 2>/dev/null || true
fi

# petrix-agent
echo "[*] Installation de petrix-agent..."
python3 -m pip install --upgrade "git+https://gitlab.com/petrix1/petrix.git#subdirectory=agent" --quiet

# Config
CONFIG_DIR="$HOME/.petrix-agent"
mkdir -p "$CONFIG_DIR"
cat > "$CONFIG_DIR/config.env" <<EOF
PETRIX_SERVER=$PETRIX_SERVER
PETRIX_TOKEN=$PETRIX_TOKEN
EOF

cat > "$CONFIG_DIR/run.sh" <<'EOF'
#!/usr/bin/env bash
source "$HOME/.petrix-agent/config.env"
petrix-agent --server "$PETRIX_SERVER" --token "$PETRIX_TOKEN" "$@"
EOF
chmod +x "$CONFIG_DIR/run.sh"

echo "[✓] Petrix Agent installé."
echo "  Lancer : ~/.petrix-agent/run.sh"
echo ""

read -p "Lancer un scan maintenant ? [O/n] " confirm
if [[ "$confirm" != "n" ]]; then
  petrix-agent --server "$PETRIX_SERVER" --token "$PETRIX_TOKEN"
fi
