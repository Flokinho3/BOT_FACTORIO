
# BOT_FACTORIO — Setup rápido

Pré-requisitos mínimos:

- Python 3.8+
- `ollama` CLI/daemon instalado e um modelo disponível (ex.: `Yuno:latest`).
- Factorio 2.0 (com mod)

Instalação e execução local (exemplo):

```bash
# criar e ativar virtualenv
python3 -m venv .venv
source .venv/bin/activate

# instalar dependências Python (se existir requirements)
pip install ollama

# garantir que o daemon do Ollama esteja em execução
# +ollama daemon &

# (opcional) baixar/instalar modelo local
ollama pull Yuno:latest

# definir variáveis de ambiente se quiser sobrescrever os defaults
export FACTORIO_RCON_HOST=127.0.0.1
export FACTORIO_RCON_PORT=27015
export FACTORIO_RCON_PASSWORD="senha"
export OLLAMA_MODEL="Yuno:latest"

# executar o bot
python3 main.py
```

Logs e troubleshooting
- Procure por linhas com `Connected to RCON`, `RAW_RECEIVED`, `EXTRACTED`, `GENERATED:` e `WROTE:` para seguir o fluxo.
- Se o bot não se conectar, verifique os valores de `FACTORIO_RCON_*` e se o servidor Factorio está com RCON habilitado.

