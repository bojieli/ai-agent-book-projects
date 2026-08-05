"""i18n catalog generation and audit helper for MkDocs site translation."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MKDOCS_CONFIG = ROOT / "mkdocs.yml"
CUSTOM_CATALOG = ROOT / "extras" / "site-nav-i18n.json"
GENERATED_CATALOG = ROOT / "_web" / "extras" / "site-i18n.generated.js"

# Material strings that the configured theme features can render. Search
# keys match standard Material translation tokens. Custom keys cover custom
# header/footer/control elements added by theme overrides.
MATERIAL_KEYS = [
    "actions.select.language",
    "footer.next",
    "footer.previous",
    "header",
    "nav",
    "search",
    "search.placeholder",
    "search.share",
    "search.result.initializer",
    "search.result.placeholder",
    "search.result.none",
    "search.result.one",
    "search.result.other",
    "search.result.term.missing",
    "select.language",

    # Material search configuration tokens used by search JS
    "search.config.pipeline",
    "search.config.separator",
]

CUSTOM_GROUPS = {
    "header": ["title", "tagline", "badge", "backToBook"],
    "home": ["heroTitle", "heroDesc", "startReading", "starOnGithub", "chapterCount"],
    "footer": ["builtWith", "copyrightNotice", "terms"],
}

HAN_RE = re.compile(r"[\u4e00-\u9fff]")


class CatalogError(Exception):
    pass


def load_custom_catalog() -> dict:
    if not CUSTOM_CATALOG.is_file():
        raise CatalogError(f"Missing catalog file: {CUSTOM_CATALOG}")
    try:
        return json.loads(CUSTOM_CATALOG.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CatalogError(f"Malformed catalog JSON: {CUSTOM_CATALOG}: {exc}") from exc


def configured_languages(config_text: str) -> dict[str, dict[str, str]]:
    """Read inline ``extra.languages`` entries without a YAML dependency."""
    match = re.search(r"(?ms)^  languages:\s*\n(?P<body>.*?)(?=^nav:\s*$)", config_text)
    if not match:
        raise CatalogError("mkdocs.yml: could not find extra.languages")
    languages: dict[str, dict[str, str]] = {}
    for code, attributes in re.findall(
        r"(?m)^\s{4}(\w[\w-]*):\s*\n(?P<attrs>(?:\s{6}\w+:\s*.*(?:\n|$))+)",
        match.group("body"),
    ):
        parsed: dict[str, str] = {}
        for key in ("prefix", "suffix", "readmeSuffix"):
            value = re.search(rf"(?:^|,)\s*{key}:\s*([^,]+)", attributes)
            if value:
                parsed[key] = value.group(1).strip().strip("\"'")
        languages[code] = parsed
    if not languages:
        raise CatalogError("mkdocs.yml: no inline extra.languages entries found")
    return languages


def canonical_nav_labels(config_text: str) -> list[str]:
    """Discover the named entries in the canonical MkDocs nav tree."""
    match = re.search(r"(?ms)^nav:\s*\n(?P<body>.*)$", config_text)
    if not match:
        raise CatalogError("mkdocs.yml: could not find nav")

    labels: list[str] = []
    pattern = re.compile(r'''(?m)^\s*-\s+(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|''|\\.)*)'|([^:\n]+)):(?:\s|$)''')
    for double_q, single_q, unquoted in pattern.findall(match.group("body")):
        if double_q:
            label = double_q.replace(r'\"', '"').replace(r'\\', '\\').strip()
        elif single_q:
            label = single_q.replace(r"\'", "'").replace("''", "'").replace(r'\\', '\\').strip()
        else:
            label = (unquoted or "").strip().strip("\"'")
        if label and label not in labels:
            labels.append(label)
    if not labels:
        raise CatalogError("mkdocs.yml: no named nav entries found")
    return labels


def material_languages_dir() -> Path:
    try:
        import material
    except ImportError as exc:  # pragma: no cover - depends on caller's env
        raise CatalogError(
            "mkdocs-material is required; install requirements-docs.txt first"
        ) from exc
    return Path(material.__file__).resolve().parent / "templates" / "partials" / "languages"


def load_material_locale(locale: str, languages_dir: Path) -> dict[str, str]:
    path = languages_dir / f"{locale}.html"
    if not path.is_file():
        raise CatalogError(f"Material locale does not exist: {path}")

    text = path.read_text(encoding="utf-8")
    start_match = re.search(r'\{\s*\n\s*"language"\s*:', text)
    if not start_match:
        raise CatalogError(f"Material locale missing language dict: {path}")

    end_index = text.rfind("}")
    if end_index == -1 or end_index < start_match.start():
        raise CatalogError(f"Material locale missing closing brace: {path}")

    json_text = text[start_match.start() : end_index + 1]
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise CatalogError(f"Invalid JSON in Material locale {path}: {exc}") from exc

    values: dict[str, str] = {}
    for key in MATERIAL_KEYS:
        node = data
        for part in key.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                node = None
                break
        if isinstance(node, str):
            values[key] = node

    return values


def _check_nonempty(errors: list[str], code: str, key: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{code}: {key} must be a non-empty string")


def audit_catalog() -> dict:
    if not MKDOCS_CONFIG.is_file():
        raise CatalogError(f"Missing config file: {MKDOCS_CONFIG}")

    config_text = MKDOCS_CONFIG.read_text(encoding="utf-8")
    configured = configured_languages(config_text)
    codes = list(configured)
    nav_labels = canonical_nav_labels(config_text)
    custom = load_custom_catalog()
    languages_dir = material_languages_dir()
    errors: list[str] = []

    languages_entry = custom.get("languages")
    if not isinstance(languages_entry, dict):
        raise CatalogError("Catalog root missing object field: languages")

    home_pages: dict[str, str] = {}
    browser_languages: dict[str, dict[str, str]] = {}

    for code in codes:
        if code not in languages_entry:
            errors.append(f"Catalog missing configured language entry: {code}")
            continue

        entry = languages_entry[code]
        if not isinstance(entry, dict):
            errors.append(f"Language entry is not an object: {code}")
            continue

        name = entry.get("name")
        _check_nonempty(errors, code, "name", name)

        prefix = configured[code].get("prefix", "")
        suffix = configured[code].get("suffix", "")
        home_pages[code] = f"{prefix}/" if prefix else "index.html"

        browser_languages[code] = {
            "name": name if isinstance(name, str) else code,
            "prefix": prefix,
            "suffix": suffix,
        }

        nav = entry.get("nav")
        if not isinstance(nav, dict):
            errors.append(f"{code}: nav must be an object")
            nav = {}
        missing_nav = [label for label in nav_labels if label not in nav]
        extra_nav = [label for label in nav if label not in nav_labels]
        if missing_nav:
            errors.append(f"{code}: missing nav labels: {', '.join(missing_nav)}")
        if extra_nav:
            errors.append(f"{code}: unknown nav labels: {', '.join(extra_nav)}")
        for label in nav_labels:
            _check_nonempty(errors, code, f"nav.{label}", nav.get(label))

        controls: dict[str, dict[str, str]] = {}
        for group, fields in CUSTOM_GROUPS.items():
            section = entry.get(group)
            if not isinstance(section, dict):
                errors.append(f"{code}: missing object section {group}")
                section = {}
            parsed_section: dict[str, str] = {}
            for field in fields:
                val = section.get(field)
                _check_nonempty(errors, code, f"{group}.{field}", val)
                if isinstance(val, str):
                    parsed_section[field] = val
            controls[group] = parsed_section

        ui = load_material_locale(code, languages_dir)
        effective_ui = entry.get("ui")
        if isinstance(effective_ui, dict):
            for k, v in effective_ui.items():
                if isinstance(v, str) and v.strip():
                    ui[k] = v

        if code not in {"zh", "zhtw", "ja"}:
            custom_values = list(nav.values()) + list(ui.values())
            for values in controls.values():
                custom_values.extend(values.values())
            leaked = [value for value in custom_values if isinstance(value, str) and HAN_RE.search(value)]
            if leaked:
                errors.append(f"{code}: contains un-translated Chinese characters: {leaked[:3]}")

        browser_languages[code]["catalog"] = {
            "direction": effective_ui.get("direction", "ltr"),
            "nav": {label: nav[label] for label in nav_labels if label in nav},
            "ui": ui,
            **controls,
        }

    extra_codes = [code for code in languages_entry if code not in codes]
    if extra_codes:
        errors.append(f"Catalog contains unconfigured languages: {', '.join(extra_codes)}")

    if errors:
        bullet_list = "\n  - ".join(errors)
        raise CatalogError(f"i18n catalog validation failed with {len(errors)} error(s):\n  - {bullet_list}")

    return {
        "languages": browser_languages,
        "canonicalNav": nav_labels,
        "homePages": home_pages,
    }


def build_catalog() -> str:
    catalog = audit_catalog()
    raw = json.dumps(catalog, ensure_ascii=False, indent=2)
    return f"window.__BOOK_I18N__ = {raw};\n"


def write_catalog() -> Path:
    text = build_catalog()
    GENERATED_CATALOG.parent.mkdir(parents=True, exist_ok=True)
    GENERATED_CATALOG.write_text(text, encoding="utf-8")
    return GENERATED_CATALOG


def main() -> int:
    try:
        path = write_catalog()
    except CatalogError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    catalog = audit_catalog()
    print(
        f"Wrote {path} covering "
        f"{len(catalog['languages'])} languages, "
        f"{len(catalog['canonicalNav'])} navigation labels each."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
