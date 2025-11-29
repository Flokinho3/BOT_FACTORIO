"""Utilities to inject structured item context into prompts before sending them to the LLM."""

from __future__ import annotations

import copy
import json
import os
import re
from functools import lru_cache
from typing import Dict, List, Optional

ITEM_TAG = re.compile(r"\[item=([^\]\s]+)\]", re.IGNORECASE)
ITEM_DATA_PATH = os.getenv(
    "FACTORIO_ITEM_DATA",
    os.path.join(os.path.dirname(__file__), "item_data.json"),
)


def _normalize_slug(raw: str) -> str:
    slug = raw.strip().lower().replace(" ", "-")
    return slug


def _display_name(slug: str) -> str:
    tokens = [part.capitalize() for part in slug.replace("-", " ").split() if part]
    return " ".join(tokens) if tokens else slug


@lru_cache(maxsize=1)
def _load_item_data() -> Dict[str, dict]:
    try:
        with open(ITEM_DATA_PATH, "r", encoding="utf-8") as handler:
            payload = json.load(handler)
            return payload if isinstance(payload, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception as exc:
        print(f"[item_context] ERROR loading {ITEM_DATA_PATH}: {exc}")
        return {}


def _save_item_data(data: Dict[str, dict]) -> None:
    directory = os.path.dirname(ITEM_DATA_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp_path = ITEM_DATA_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as handler:
        json.dump(data, handler, ensure_ascii=False, indent=2)
        handler.flush()
        if hasattr(os, "fsync"):
            os.fsync(handler.fileno())
    os.replace(tmp_path, ITEM_DATA_PATH)


def _auto_add_item(slug: str) -> Optional[dict]:
    try:
        from IA import wiki_fetcher
    except Exception as exc:
        print(f"[item_context] ERROR importing wiki_fetcher: {exc}")
        return None

    try:
        payload = wiki_fetcher.build_item_payload(slug)
    except Exception as exc:
        print(f"[item_context] ERROR fetching wiki data for {slug}: {exc}")
        return None

    if not payload:
        return None

    data = dict(_load_item_data())
    data[slug] = payload
    try:
        _save_item_data(data)
    except Exception as exc:
        print(f"[item_context] ERROR saving updated item_data.json: {exc}")
        return None

    _load_item_data.cache_clear()
    return copy.deepcopy(payload)


def _get_item_payload(slug: str) -> Optional[dict]:
    data = _load_item_data()
    entry = data.get(slug) if data else None
    if not entry:
        entry = _auto_add_item(slug)
        if not entry:
            return None
    cloned = copy.deepcopy(entry)
    cloned.setdefault("slug", slug)
    cloned.setdefault("name", _display_name(slug))
    return cloned


def extract_item_slugs(prompt: str) -> List[str]:
    if not prompt:
        return []
    found = []
    seen = set()
    for match in ITEM_TAG.findall(prompt):
        slug = _normalize_slug(match)
        if not slug or slug in seen:
            continue
        seen.add(slug)
        found.append(slug)
    return found


def build_item_context(prompt: str) -> Optional[str]:
    slugs = extract_item_slugs(prompt)
    if not slugs:
        return None
    blocks: List[str] = []
    for slug in slugs:
        payload = _get_item_payload(slug)
        if not payload:
            continue
        json_blob = json.dumps(payload, ensure_ascii=False, indent=2)
        blocks.append(f"[item_info]\n{json_blob}\n[/item_info]")
    if not blocks:
        return None
    combined = "\n\n".join(blocks)
    header = "### CONTEXTO AUTOMATICO (gerado pelo parser)"
    return f"{header}\n\n{combined}"


def augment_prompt_with_context(prompt: str) -> str:
    try:
        ctx = build_item_context(prompt)
    except Exception as exc:
        print(f"[item_context] ERROR building context: {exc}")
        return prompt
    if not ctx:
        return prompt
    return f"{ctx}\n\n### MENSAGEM DO USUÁRIO\n{prompt}"
