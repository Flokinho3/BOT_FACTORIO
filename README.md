
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
export FACTORIO_RCON_HOST=localhost
export FACTORIO_RCON_PORT=27015
export FACTORIO_RCON_PASSWORD="senha"
export OLLAMA_MODEL="Yuno:latest"

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
# ollama daemon &

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

## Instalação dinâmica (recomendada)

Adicionei um fluxo simples para tornar a instalação mais dinâmica e reproduzível.

- `requirements.txt`: lista de dependências Python do projeto.
- `scripts/install.sh`: cria um virtualenv, instala dependências e mostra próximos passos.
- `.env.example`: exemplo das variáveis de ambiente usadas pelo projeto.

Passos rápidos:

```bash
# tornar o script executável e executá-lo (recomendado)
chmod +x scripts/install.sh
./scripts/install.sh

# Ative o virtualenv (separado)
source .venv/bin/activate

# copie o exemplo de variáveis e ajuste se necessário
cp .env.example .env
edit .env  # ou use seu editor preferido

# execute
python3 main.py
```

Observações importantes:

- O pacote `ollama` instalado via `pip` é o cliente Python; o daemon/CLI do Ollama deve estar instalado separadamente seguindo https://ollama.com/.
- Se preferir usar `poetry` ou outro gerenciador, adapte `requirements.txt` conforme sua ferramenta.

