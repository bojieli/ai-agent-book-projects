#!/usr/bin/env python3
"""Validate and build the static site's browser-side translation catalog.

The site contains all book editions in one MkDocs build. MkDocs Material can
only use one ``theme.language`` per build, so its generated chrome is Chinese
and translated editions localize it in the browser. This hook combines:

* Material for MkDocs' own locale catalogs (search, actions, footer, etc.); and
* ``extras/site-nav-i18n.json`` (book navigation and custom controls).

Run ``python scripts/site_i18n.py`` after installing ``requirements-docs.txt``
to audit every language. During ``mkdocs build`` the same validation runs and
the hook emits ``_web/extras/site-i18n.generated.js`` for the browser.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
MKDOCS_CONFIG = ROOT / "mkdocs.yml"
CUSTOM_CATALOG = ROOT / "extras" / "site-nav-i18n.json"
GENERATED_CATALOG = ROOT / "_web" / "extras" / "site-i18n.generated.js"

# Material strings that the configured theme features can render. Search
# result strings are updated dynamically, while the rest occur in the initial
# document or in tooltips/dialogs.
REQUIRED_UI_KEYS = (
    "action.edit",
    "action.skip",
    "action.view",
    "clipboard.copy",
    "clipboard.copied",
    "footer",
    "footer.next",
    "footer.previous",
    "header",
    "nav",
    "search",
    "search.placeholder",
    "search.share",
    "search.reset",
    "search.result.initializer",
    "search.result.placeholder",
    "search.result.none",
    "search.result.one",
    "search.result.other",
    "search.result.more.one",
    "search.result.more.other",
    "search.result.term.missing",
    "select.language",
    "source",
    "source.file.contributors",
    "source.file.date.created",
    "source.file.date.updated",
    "tabs",
    "toc",
    "top",
)

CUSTOM_GROUPS = {
    "sidebar": ("show", "hide"),
    "palette": ("light", "dark"),
}

HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


class CatalogError(RuntimeError):
    """Raised when the checked-in translation catalog is incomplete."""


def configured_languages(config_text: str) -> dict[str, dict[str, str]]:
    """Read inline ``extra.languages`` entries without a YAML dependency."""
    match = re.search(r"(?ms)^  languages:\s*\n(?P<body>.*?)(?=^nav:\s*$)", config_text)
    if not match:
        raise CatalogError("mkdocs.yml: could not find extra.languages")
    languages: dict[str, dict[str, str]] = {}
    for code, attributes in re.findall(
        r"(?m)^    ([a-zA-Z][a-zA-Z0-9_-]*):\s*\{([^}]*)\}\s*$",
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
        raise CatalogError(f"Could not parse Material locale: {path}")
    end = text.find("}[key]", start_match.start())
    if end < 0:
        raise CatalogError(f"Could not parse Material locale: {path}")
    try:
        values = ast.literal_eval(text[start_match.start() : end + 1])
    except (SyntaxError, ValueError) as exc:
        raise CatalogError(f"Could not parse Material locale: {path}: {exc}") from exc
    if not isinstance(values, dict):
        raise CatalogError(f"Material locale is not a mapping: {path}")
    return values


def load_custom_catalog() -> dict[str, dict[str, Any]]:
    try:
        data = json.loads(CUSTOM_CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"Could not read {CUSTOM_CATALOG}: {exc}") from exc
    if not isinstance(data, dict):
        raise CatalogError(f"{CUSTOM_CATALOG}: top level must be an object")
    return data


def _check_nonempty(errors: list[str], code: str, field: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{code}: {field} must be a non-empty string")


def build_catalog() -> dict[str, Any]:
    """Validate all sources and return the compact browser catalog."""
    config_text = MKDOCS_CONFIG.read_text(encoding="utf-8")
    configured = configured_languages(config_text)
    codes = list(configured)
    nav_labels = canonical_nav_labels(config_text)
    custom = load_custom_catalog()
    languages_dir = material_languages_dir()
    errors: list[str] = []

    missing_codes = sorted(set(codes) - set(custom))
    extra_codes = sorted(set(custom) - set(codes))
    if missing_codes:
        errors.append(f"catalog is missing configured languages: {', '.join(missing_codes)}")
    if extra_codes:
        errors.append(f"catalog has unconfigured languages: {', '.join(extra_codes)}")

    browser_languages: dict[str, Any] = {}
    for code in codes:
        entry = custom.get(code)
        if not isinstance(entry, dict):
            continue

        material_locale = entry.get("material_locale")
        _check_nonempty(errors, code, "material_locale", material_locale)
        if not isinstance(material_locale, str) or not material_locale:
            continue
        try:
            material_ui = load_material_locale(material_locale, languages_dir)
        except CatalogError as exc:
            errors.append(str(exc))
            continue
        overrides = entry.get("ui_overrides", {})
        if not isinstance(overrides, dict):
            errors.append(f"{code}: ui_overrides must be an object")
            overrides = {}
        unknown_overrides = sorted(set(overrides) - set(material_ui))
        if unknown_overrides:
            errors.append(
                f"{code}: ui_overrides has unknown Material keys: "
                + ", ".join(unknown_overrides)
            )
        effective_ui = {**material_ui, **overrides}

        ui: dict[str, str] = {}
        for key in REQUIRED_UI_KEYS:
            value = effective_ui.get(key)
            _check_nonempty(errors, code, f"Material UI key {key}", value)
            if isinstance(value, str):
                ui[key] = value

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
            values = entry.get(group)
            if not isinstance(values, dict):
                errors.append(f"{code}: {group} must be an object")
                values = {}
            controls[group] = {}
            for field in fields:
                value = values.get(field)
                _check_nonempty(errors, code, f"{group}.{field}", value)
                if isinstance(value, str):
                    controls[group][field] = value

        # Chinese characters in a non-CJK catalog almost always mean a label
        # was copied but not translated. Japanese and Traditional Chinese are
        # excluded because Han characters are part of those target languages.
        if code not in {"zh", "zhtw", "ja"}:
            custom_values = list(nav.values()) + list(ui.values())
            for values in controls.values():
                custom_values.extend(values.values())
            leaked = [value for value in custom_values if isinstance(value, str) and HAN_RE.search(value)]
            if leaked:
                errors.append(f"{code}: Chinese text remains in custom UI: {leaked[0]!r}")

        browser_languages[code] = {
            "locale": effective_ui.get("language", material_locale),
            "direction": effective_ui.get("direction", "ltr"),
            "nav": {label: nav[label] for label in nav_labels if label in nav},
            "ui": ui,
            **controls,
        }

        # Every path produced by the language switcher must have a source
        # Markdown file. This catches naming drift such as a translated
        # reference-answer file retaining its old non-ASCII filename.
        language_config = configured[code]
        prefix = language_config.get("prefix")
        if not prefix:
            errors.append(f"{code}: mkdocs language config has no prefix")
            continue
        book_dir = ROOT / prefix.rstrip("/")
        suffix = language_config.get("suffix", "")
        prose_slugs = ["introduction", *(f"chapter{n}" for n in range(1, 11)), "afterword", "reference-answers"]
        for slug in prose_slugs:
            source = book_dir / f"{slug}{suffix}.md"
            if not source.is_file():
                errors.append(
                    f"{code}: switcher URL has no source file: {source.relative_to(ROOT)}"
                )
        readme_suffix = language_config.get("readmeSuffix")
        if readme_suffix:
            for number in range(1, 11):
                source = ROOT / f"chapter{number}" / f"README.{readme_suffix}.md"
                if not source.is_file():
                    errors.append(
                        f"{code}: experiment-index URL has no source file: {source.relative_to(ROOT)}"
                    )

    if errors:
        raise CatalogError("Static-site i18n validation failed:\n  - " + "\n  - ".join(errors))

    default = "zh"
    if default not in browser_languages:
        raise CatalogError(f"Default language {default!r} is not configured")

    # Languages with a translated site homepage (root index.<code>.md).
    # The language switcher maps home <-> home for these editions and keeps
    # the introduction-page fallback for the rest. The default edition's
    # homepage is the root index.md itself.
    home_pages = [code for code in codes if (ROOT / f"index.{code}.md").is_file()]

    return {
        "default": default,
        "languages": browser_languages,
        "canonicalNav": nav_labels,
        "homePages": home_pages,
    }


def write_browser_catalog(catalog: dict[str, Any]) -> None:
    GENERATED_CATALOG.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(catalog, ensure_ascii=False, separators=(",", ":"))
    GENERATED_CATALOG.write_text(
        "// Generated by scripts/site_i18n.py; do not edit.\n"
        f"window.SITE_I18N={payload};\n",
        encoding="utf-8",
    )


def on_config(config: Any, **_: Any) -> Any:
    """MkDocs hook: fail the build on drift and emit the browser catalog."""
    try:
        write_browser_catalog(build_catalog())
    except CatalogError as exc:
        from mkdocs.exceptions import ConfigurationError

        raise ConfigurationError(str(exc)) from exc
    return config


def main() -> int:
    try:
        catalog = build_catalog()
    except CatalogError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        "Static-site i18n catalog is complete: "
        f"{len(catalog['languages'])} languages, "
        f"{len(catalog['canonicalNav'])} navigation labels each."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
