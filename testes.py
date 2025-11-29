"""Extrai a infobox de um item do Factorio Wiki e imprime campos em PT-BR."""

from __future__ import annotations

import argparse
from pathlib import Path

from IA import wiki_fetcher

HTML_PATH = Path("wooden_chest.html")
TMP_PATH = HTML_PATH.with_name(f"{HTML_PATH.name}.tmp")

FIELDS = [
    ("Recipe", "Receita"),
    ("Total raw", "Total bruto"),
    ("Map color", "Cor do mapa"),
    ("Storage size", "Tamanho do armazenamento"),
    ("Health", "Saúde"),
    ("Resistances", "Resistências"),
    ("Stack size", "Tamanho da pilha"),
    ("Rocket capacity", "Capacidade do foguete"),
    ("Dimensions", "Dimensões"),
    ("Energy consumption", "Consumo de energia"),
    ("Drain", "Dreno"),
    ("Rotation speed", "Velocidade de rotação"),
    ("Mining time", "Tempo de mineração"),
    ("Prototype type", "Tipo de protótipo"),
    ("Internal name", "Nome interno"),
    ("Required technologies", "Tecnologias necessárias"),
    ("Boosting technologies", "Impulsionando tecnologias"),
    ("Produced by", "Produzido por"),
    ("Consumed by", "Consumido por"),
]


def download_html(slug: str) -> None:
    html = wiki_fetcher.fetch_page_html(slug)
    TMP_PATH.write_text(html, encoding="utf-8")
    TMP_PATH.replace(HTML_PATH)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extrai infobox do Factorio Wiki")
    parser.add_argument("slug", nargs="?", default="steel-chest", help="Slug do item, ex: steel-chest")
    args = parser.parse_args()

    download_html(args.slug)
    print(f"HTML salvo com sucesso em '{HTML_PATH}'\n")

    html_content = HTML_PATH.read_text(encoding="utf-8")
    info = wiki_fetcher.parse_infobox_from_html(html_content)

    print("=" * 50)
    print("INFORMAÇÕES EXTRAÍDAS:")
    print("=" * 50)
    for english_key, label in FIELDS:
        value = info.get(english_key, "Não disponível") or "Não disponível"
        print(f"\n{label}:")
        print(value)
        print("-" * 50)


if __name__ == "__main__":
    main()
