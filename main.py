from rcon_client import FactorioRCON
import ollama
import time
import json
import os
from IA.FILES import FACTORY_SCRIPT_OUTPUT_FILE, FACTORY_SCRIPT_OUTPUT_DIR
import os
import uuid

# Configuration from environment (safer for deployments)
# Defaults kept for local development convenience.
HOST = os.getenv("FACTORIO_RCON_HOST", "127.0.0.1")
PORT = int(os.getenv("FACTORIO_RCON_PORT", "27015"))
PASSWORD = os.getenv("FACTORIO_RCON_PASSWORD", "senha")
# Ollama model override (env)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "Yuno:latest")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


# garante que o diretório script-output exista (se possível)
try:
    os.makedirs(FACTORY_SCRIPT_OUTPUT_DIR, exist_ok=True)
except Exception:
    pass

# ---------------------------------------------------------------------------
# Memória de conversas (persistida em JSON)
# ---------------------------------------------------------------------------
MEMORY_FILE = os.path.join(os.path.dirname(__file__), "IA", "MEMORIAS", "memorias.json")
# número máximo de interações a manter no contexto da IA
MAX_MEMORY = 200

# Mensagem SYSTEM explícita para garantir contexto em cada chamada
SYSTEM_PROMPT = (
    "Você é Monika, uma IA de suporte dentro do jogo Factorio."
    " Sempre responda estritamente no contexto do universo Factorio, usando"
    " terminologia do jogo (ex: minério de ferro, cobre, bichos, caldeiras, braços robóticos, trem, ciência, foguete)."
    " Use BBCode para itens/entidades quando apropriado: [item=...], [entity=...], [technology=...]."
    " Se o pedido for fora do contexto do jogo, responda educadamente que não pode ajudar com isso e direcione para assuntos de automação/fábrica."
)

def load_memory():
    """Carrega a lista de interações armazenadas em `memorias.json`.
    Se o arquivo não existir ou estiver corrompido, retorna lista vazia.
    """
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Espera que o JSON seja um dict com chave 'interactions' ou uma lista direta
            if isinstance(data, dict) and "interactions" in data:
                return data["interactions"]
            if isinstance(data, list):
                return data
    except Exception as e:
        print(f"[{now()}] ERROR loading memory file: {e}")
    return []


def is_factorio_text(s: str) -> bool:
    if not s:
        return False
    s = s.lower()
    keywords = [
        "minério", "ferro", "cobre", "bicho", "bichos", "assembler", "foguete",
        "rocket", "trem", "train", "ciência", "science", "engenheiro", "fábrica",
        "factory", "poluição", "mod", "caldeira", "braço", "inserter", "belts",
    ]
    return any(k in s for k in keywords)


def sanitize_history(history: list, max_items: int) -> list:
    """Filtra a história mantendo interações que parecem relacionadas ao Factorio.

    Estratégia simples:
    - Mantém interações onde prompt ou response contêm palavras-chaves de Factorio.
    - Se nenhum item parecer relacionado, devolve os últimos `max_items` (fallback).
    - Limita a saída a `max_items` itens.
    """
    if not history:
        return []

    related = []
    for entry in history:
        p = (entry.get("prompt") or "")
        r = (entry.get("response") or "")
        if is_factorio_text(p) or is_factorio_text(r):
            related.append(entry)

    if not related:
        # fallback: retorna os últimos max_items
        return history[-max_items:]

    # garante limite
    return related[-max_items:]

def save_memory(interactions):
    """Persiste a lista de interações em `memorias.json` de forma atômica."""
    tmp = MEMORY_FILE + ".tmp"
    try:
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"interactions": interactions}, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, MEMORY_FILE)
    except Exception as e:
        print(f"[{now()}] ERROR saving memory file: {e}")


def safe_for_command(s: str) -> str:
    # Remove quebras de linha e aspas problemáticas para envio via RCON
    return s.replace('\n', ' ').replace('\r', ' ').replace('"', "'")


def extract_message_from_rcon(raw: str) -> str:
    """Tenta extrair 'player: message' do output bruto do RCON.

    Estratégia:
    - divide em linhas e procura a última linha que contém ': '
    - tenta remover prefixos como timestamps ou tags '[CHAT]'
    - se não encontrar, retorna o raw sem mudanças (strip)
    """
    if not raw:
        return ""

    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if not lines:
        return raw.strip()

    # Procura da última para frente por uma linha com ': '
    for ln in reversed(lines):
        # exemplo: '2025-11-28 12:56:05 [CHAT] thiago: ola'
        # remover prefixos entre colchetes
        cleaned = ln
        # se tiver [CHAT] ou similar
        if '] ' in cleaned and '[' in cleaned:
            # pega parte após o último '] '
            parts = cleaned.split('] ')
            cleaned = parts[-1]

        # agora busca pattern 'name: message'
        if ': ' in cleaned:
            return cleaned  # já no formato 'player: message'

    # fallback: retorna última linha
    return lines[-1]


def main_loop():
    # Tentativa contínua de conexão com backoff exponencial
    backoff = 1
    max_backoff = 60
    while True:
        rcon = FactorioRCON(HOST, PORT, PASSWORD)
        try:
            rcon.connect()
            print(f"[{now()}] Connected to RCON {HOST}:{PORT}")
            # reset backoff após conexão bem-sucedida
            backoff = 1
        except Exception as e:
            print(f"[{now()}] ERROR connecting RCON: {e}; retrying in {backoff}s")
            time.sleep(backoff)
            backoff = min(max_backoff, backoff * 2)
            continue

        # Loop principal: somente executa enquanto a conexão existir
        try:
            while True:
                try:
                    prompt = rcon.command('/monika_pull')
                except Exception as e:
                    print(f"[{now()}] ERROR RCON command (will reconnect): {e}")
                    break  # sai do loop interno e tenta reconectar

                if prompt and prompt.strip() != "":
                    raw_prompt = prompt
                    prompt = extract_message_from_rcon(raw_prompt).strip()
                    print(f"[{now()}] RAW_RECEIVED: {raw_prompt}")
                    print(f"[{now()}] EXTRACTED: {prompt}")

                    resp = None
                    try:
                        # Carrega histórico de conversas, sanitiza e monta mensagens para o modelo
                        history = load_memory()
                        recent = history[-MAX_MEMORY:] if MAX_MEMORY > 0 else []
                        sanitized = sanitize_history(recent, MAX_MEMORY)

                        # Mensagens: primeiro a SYSTEM para garantir o contexto de Monika
                        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                        for entry in sanitized:
                            if entry.get("prompt"):
                                messages.append({"role": "user", "content": entry["prompt"]})
                            if entry.get("response"):
                                messages.append({"role": "assistant", "content": entry["response"]})
                        # adiciona a mensagem atual como último usuário
                        messages.append({"role": "user", "content": prompt})

                        # Log curto do system (não imprime todo o conteúdo para evitar flood)
                        try:
                            print(f"[{now()}] SENDING_SYSTEM: {SYSTEM_PROMPT[:200]}...")
                        except Exception:
                            pass

                        resp = ollama.chat(
                            model=OLLAMA_MODEL,
                            messages=messages
                        )["message"]["content"]
                    except Exception as e:
                        print(f"[{now()}] ERROR calling ollama.chat: {e}")

                    if resp is not None:
                        print(f"[{now()}] GENERATED: {resp}")

                        data = {
                            "timestamp": now(),
                            "id": str(uuid.uuid4()),
                            "prompt": prompt,
                            "response": resp
                        }

                        # Escreve de forma atômica: escreve em tmp e faz replace
                        tmp_file = FACTORY_SCRIPT_OUTPUT_FILE + ".tmp"
                        try:
                            with open(tmp_file, "w", encoding="utf-8") as f:
                                json.dump(data, f, ensure_ascii=False)
                                f.flush()
                                os.fsync(f.fileno())
                            os.replace(tmp_file, FACTORY_SCRIPT_OUTPUT_FILE)
                            print(f"[{now()}] WROTE: {FACTORY_SCRIPT_OUTPUT_FILE} (atomic)")
                        except Exception as e:
                            print(f"[{now()}] ERROR writing resposta file: {e}")

                        # Também enviar via RCON para compatibilidade (compacta a resposta)
                        try:
                            short = safe_for_command(resp)[:1000]
                            rcon.send_monika_message(short)
                            print(f"[{now()}] SENT to game via RCON (short)")
                        except Exception as e:
                            print(f"[{now()}] ERROR sending reply via RCON: {e}")

                        # ---------- Persistir na memória ----------
                        try:
                            # Carrega memória atual, adiciona nova interação e salva
                            mem = load_memory()
                            mem.append({"timestamp": now(), "prompt": prompt, "response": resp})
                            save_memory(mem)
                            print(f"[{now()}] MEMORY saved (total {len(mem)} entries)")
                        except Exception as e:
                            print(f"[{now()}] ERROR persisting memory: {e}")

                time.sleep(1)
        finally:
            try:
                rcon.close()
            except Exception:
                pass
            # se cair aqui, tenta reconectar com backoff
            print(f"[{now()}] Disconnected; reconnecting in {backoff}s")
            time.sleep(backoff)
            backoff = min(max_backoff, backoff * 2)


if __name__ == '__main__':
    main_loop()
