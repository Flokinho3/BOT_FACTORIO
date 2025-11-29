"""Fetches structured information for Factorio items from the official wiki."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString

BASE_URL = os.getenv("FACTORIO_WIKI_BASE_URL", "https://wiki.factorio.com")
USER_AGENT = os.getenv(
    "FACTORIO_WIKI_USER_AGENT",
    "MonikaBot/1.0 (+https://github.com/Flokinho3/BOT_FACTORIO)",
)
REQUEST_TIMEOUT = float(os.getenv("FACTORIO_WIKI_TIMEOUT", "30"))
DECIMAL_SEPARATOR = re.compile(r"(?<=\d)\.(?=\d)")
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def _normalize_text(text: str) -> str:
    sanitized = text.replace("\xa0", " ").strip()
    return DECIMAL_SEPARATOR.sub(",", sanitized)


def _slug_to_title(slug: str) -> str:
    parts = [segment for segment in re.split(r"[-_\s]+", slug) if segment]
    if not parts:
        return slug
    normalized = [part[0].upper() + part[1:] if len(part) > 1 else part.upper() for part in parts]
    return "_".join(normalized)


def build_wiki_url(slug: str) -> str:
    return f"{BASE_URL}/{_slug_to_title(slug)}"


def fetch_page_html(slug: str) -> str:
    url = build_wiki_url(slug)
    response = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.text


def _extract_color(cell) -> Optional[str]:
    color_box = cell.find("div", class_="template-color")
    if not color_box:
        return None
    style = color_box.get("style", "")
    match = re.search(r"background-color:\s*([^;]+)", style)
    return match.group(1) if match else None


def _extract_links(cell) -> Optional[str]:
    titles = []
    for link in cell.find_all("a"):
        title = link.get("title") or link.get_text(strip=True)
        if title:
            titles.append(title)
    if titles:
        deduped = list(dict.fromkeys(titles))
        return ", ".join(deduped)
    return None


def _extract_nested_rows(cell) -> Optional[str]:
    sub_rows = cell.find_all("tr")
    if not sub_rows:
        return None
    lines: List[str] = []
    for sub_row in sub_rows:
        entries = [
            _normalize_text(td.get_text(separator=" ", strip=True))
            for td in sub_row.find_all("td")
        ]
        entries = [entry for entry in entries if entry]
        if entries:
            lines.append("\t" + "\t".join(entries))
    return "\n".join(lines) if lines else None


def _extract_factorio_icons(cell) -> Optional[str]:
    icons = cell.find_all("div", class_="factorio-icon")
    if not icons:
        return None

    parts: List[str] = []
    for child in cell.children:
        if isinstance(child, NavigableString):
            text = _normalize_text(str(child))
            if text:
                parts.append(text)
            continue

        if getattr(child, "name", None) != "div" or "factorio-icon" not in child.get("class", []):
            nested_text = _normalize_text(child.get_text(" ", strip=True)) if hasattr(child, "get_text") else ""
            if nested_text:
                parts.append(nested_text)
            continue

        qty_node = child.find("div", class_="factorio-icon-text")
        qty_text = _normalize_text(qty_node.get_text(strip=True)) if qty_node and qty_node.get_text(strip=True) else "1"
        link = child.find("a")
        name = ""
        if link:
            name = link.get("title") or _normalize_text(link.get_text(strip=True))
        if not name:
            img = child.find("img")
            name = img.get("alt") if img and img.get("alt") else ""
        if name and qty_text in {"", "1"}:
            icon_repr = name
        elif name:
            icon_repr = f"{qty_text} {name}".strip()
        else:
            icon_repr = qty_text
        if icon_repr:
            parts.append(icon_repr)

    tokens = [part for part in parts if part]
    if not tokens:
        return None
    has_operator = any(token in {"+", "→", "<-", "->"} for token in tokens)
    separator = " " if has_operator else ", "
    combined = separator.join(tokens)
    return combined or None


def _cell_to_value(cell) -> str:
    color = _extract_color(cell)
    if color:
        return color
    icons = _extract_factorio_icons(cell)
    if icons:
        return icons
    nested = _extract_nested_rows(cell)
    if nested:
        return nested
    raw_text = cell.get_text(separator="\n", strip=True)
    lines = [_normalize_text(line) for line in raw_text.splitlines() if line.strip()]
    if lines:
        return " ".join(lines)
    links = _extract_links(cell)
    if links:
        return links
    return ""


def extract_infobox_data(soup: BeautifulSoup) -> Dict[str, str]:
    info: Dict[str, str] = {}
    reference_table = soup.find("div", class_="infobox-image")
    if not reference_table:
        return info
    table = reference_table.find_next("table")
    if not table:
        return info

    rows = table.find_all("tr")
    i = 0
    while i < len(rows):
        row = rows[i]
        header_cell = row.find("td", attrs={"colspan": "2"}, recursive=False)
        if header_cell:
            key = header_cell.get_text(strip=True)
            value = ""
            if i + 1 < len(rows):
                next_row = rows[i + 1]
                value_cell = next_row.find("td", class_="infobox-vrow-value", recursive=False) or next_row.find(
                    "td", recursive=False
                )
                if value_cell:
                    value = _cell_to_value(value_cell)
                i += 1
            if key:
                info[key] = value
            i += 1
            continue

        cells = row.find_all("td", recursive=False)
        if len(cells) == 2:
            key = cells[0].get_text(strip=True)
            value = _cell_to_value(cells[1])
            if key:
                info[key] = value
        i += 1

    return info


def _extract_display_name(soup: BeautifulSoup) -> Optional[str]:
    header = soup.select_one(".infobox-header-text span")
    if header and header.get_text(strip=True):
        return header.get_text(strip=True)
    title = soup.find("h1", id="firstHeading")
    if title and title.get_text(strip=True):
        return title.get_text(strip=True)
    return None


def _extract_summary(soup: BeautifulSoup) -> Optional[str]:
    content = soup.find("div", class_="mw-parser-output")
    if not content:
        return None
    for child in content.find_all("p", recursive=False):
        text = child.get_text(" ", strip=True)
        if text:
            return text
    return None


Number = Union[int, float]


def _parse_number(value: Optional[str]) -> Optional[Number]:
    if not value:
        return None
    match = NUMBER_RE.search(value.replace(",", ""))
    if not match:
        return None
    number = match.group(0)
    return int(number) if "." not in number else float(number)


def _split_list(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    tokens = [token.strip() for token in re.split(r",|\n|\/", value) if token.strip()]
    return tokens or None


def parse_infobox_from_html(html: str) -> Dict[str, str]:
    parser = "lxml"
    try:
        soup = BeautifulSoup(html, parser)
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
    return extract_infobox_data(soup)


def build_item_payload(slug: str) -> Optional[Dict[str, object]]:
    html = fetch_page_html(slug)
    parser = "lxml"
    try:
        soup = BeautifulSoup(html, parser)
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    infobox = extract_infobox_data(soup)
    if not infobox:
        return None

    display_name = _extract_display_name(soup) or slug.replace("-", " ").title()
    summary = _extract_summary(soup)

    payload: Dict[str, object] = {
        "slug": slug,
        "name": display_name,
        "wiki_url": build_wiki_url(slug),
        "source": "factorio_wiki_auto",
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "raw_fields": infobox,
    }
    if summary:
        payload["summary"] = summary

    prototype_type = infobox.get("Prototype type")
    if prototype_type:
        payload["prototype_type"] = prototype_type

    internal_name = infobox.get("Internal name")
    if internal_name:
        payload["internal_name"] = internal_name

    stack_size = _parse_number(infobox.get("Stack size"))
    if stack_size is not None:
        payload["stack_size"] = stack_size

    storage_size = _parse_number(infobox.get("Storage size"))
    if storage_size is not None:
        payload["inventory_size"] = storage_size
    else:
        raw_storage = infobox.get("Storage size")
        if raw_storage:
            payload["inventory_size_raw"] = raw_storage

    health = _parse_number(infobox.get("Health"))
    if health is not None:
        payload["health"] = health

    resistances = infobox.get("Resistances")
    if resistances:
        payload["resistances"] = resistances

    recipe = infobox.get("Recipe")
    if recipe:
        payload["recipe_text"] = recipe

    produced_by = _split_list(infobox.get("Produced by"))
    if produced_by:
        payload["produced_by"] = produced_by

    consumed_by = _split_list(infobox.get("Consumed by"))
    if consumed_by:
        payload["consumed_by"] = consumed_by

    tech_required = _split_list(infobox.get("Required technologies"))
    if tech_required:
        payload["tech_required"] = tech_required

    return payload
