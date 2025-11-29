#!/usr/bin/env bash
set -euo pipefail

# Script de instalação (cria venv, instala dependências e dá instruções adicionais)
# Uso:
#   chmod +x install.sh
#   ./install.sh

PYTHON=${PYTHON:-python3}
VENV_DIR=${VENV_DIR:-.venv}

echo "Usando python: $(command -v "$PYTHON" || echo 'não encontrado')"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python não encontrado. Instale Python 3.8+ e tente novamente." >&2
  exit 1
fi

echo "Criando virtualenv em $VENV_DIR..."
$PYTHON -m venv "$VENV_DIR"
echo "Ative com: source $VENV_DIR/bin/activate"

echo "Instalando dependências de Python..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r requirements.txt

echo "Instalação Python concluída."
echo
echo "PRÓXIMOS PASSOS (resumo):"
echo "  1) Ative o virtualenv: source $VENV_DIR/bin/activate"
echo "  2) Copie .env.example para .env e ajuste variáveis se necessário"
echo "     cp .env.example .env && edit .env"
echo "  3) Garanta que o daemon do Ollama esteja rodando (instale o CLI/daemon se necessário):"
echo "     https://ollama.com/ (siga instruções de instalação)"
echo "  4) (Opcional) Baixe o modelo: ollama pull \"${OLLAMA_MODEL:-Yuno:latest}\""
echo "  5) Execute: python3 main.py"

echo
echo "Observações:"
echo "- O pacote 'ollama' instalado via pip é o cliente Python. O daemon/CLI do Ollama ainda precisa estar instalado separadamente conforme a documentação do Ollama."
echo "- Se preferir usar um gerenciador de dependências diferente (poetry/pipx), adapte o fluxo acima."
