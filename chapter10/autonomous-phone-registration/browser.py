"""Real Playwright Computer Use surface for registration forms."""

from __future__ import annotations

import asyncio
from typing import List, Optional

from models import FieldSpec


class RecoverableFillError(RuntimeError):
    """A page-specific field failure that may be reported without aborting the call."""


class RegistrationBrowser:
    """Owns a real Chromium browser/context/page and exposes form operations.

    The selector assigned during discovery is generated from the element itself and
    remains internal. Values are never included in screenshots or trace files.
    """

    def __init__(self, url: str, *, headless: bool = False, submit: bool = False):
        self.url = url
        self.headless = headless
        self.submit_enabled = submit
        self._playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.closed = False

    async def open(self) -> None:
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        await self.page.goto(self.url, wait_until="domcontentloaded", timeout=60_000)

    async def discover_fields(self) -> List[FieldSpec]:
        if self.page is None:
            raise RuntimeError("browser is not open")
        raw = await self.page.locator(
            "input:not([type=hidden]):not([disabled]), select:not([disabled]), textarea:not([disabled])"
        ).evaluate_all(
            """els => els.map((el, i) => {
              const id = el.id || '';
              const explicit = id ? document.querySelector(`label[for="${CSS.escape(id)}"]`) : null;
              const wrapping = el.closest('label');
              const aria = el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || '';
              const label = (explicit?.innerText || wrapping?.innerText || aria || el.placeholder || el.name || id || `field_${i}`).trim();
              const selector = ((el.type === 'radio' || el.type === 'checkbox') && el.name) ?
                `input[name="${CSS.escape(el.name)}"]` : id ? `#${CSS.escape(id)}` :
                (el.name ? `${el.tagName.toLowerCase()}[name="${CSS.escape(el.name)}"]` :
                 `${el.tagName.toLowerCase()}:nth-of-type(${i + 1})`);
              return {
                name: el.name || id || `field_${i}`,
                label,
                input_type: el.tagName === 'SELECT' ? 'select' : (el.type || el.tagName.toLowerCase()),
                required: !!el.required || el.getAttribute('aria-required') === 'true',
                selector,
                format_hint: el.title || el.placeholder || '',
                pattern: el.pattern || '',
                options: el.tagName === 'SELECT' ? [...el.options].map(o => o.text.trim()).filter(Boolean) :
                  ((el.type === 'radio' || el.type === 'checkbox') ? [el.value, label].filter(Boolean) : [])
              };
            })"""
        )
        # Radio buttons with the same name are one logical field.
        fields: List[FieldSpec] = []
        seen: set[str] = set()
        for item in raw:
            spec = FieldSpec.from_dict(item)
            if spec.name in seen:
                existing = next(f for f in fields if f.name == spec.name)
                existing.options = list(dict.fromkeys(existing.options + spec.options))
                continue
            seen.add(spec.name)
            fields.append(spec)
        return fields

    @property
    async def title(self) -> str:
        return await self.page.title() if self.page else ""

    async def fill(self, field: FieldSpec, value: str) -> None:
        if self.page is None:
            raise RuntimeError("browser is not open")
        from playwright.async_api import Error as PlaywrightError

        try:
            locator = self.page.locator(field.selector).first
            await locator.scroll_into_view_if_needed()
            kind = field.input_type.lower()
            if kind == "select":
                try:
                    await locator.select_option(label=value)
                except PlaywrightError:
                    await locator.select_option(value=value)
            elif kind in {"checkbox", "radio"}:
                group = self.page.locator(field.selector)
                wanted = value.strip().casefold()
                chosen = None
                for i in range(await group.count()):
                    item = group.nth(i)
                    raw_value = (await item.get_attribute("value") or "").strip()
                    item_id = await item.get_attribute("id")
                    label = ""
                    if item_id:
                        label_node = self.page.locator(f'label[for="{item_id}"]').first
                        if await label_node.count():
                            label = (await label_node.inner_text()).strip()
                    if wanted in {raw_value.casefold(), label.casefold()}:
                        chosen = item
                        break
                if chosen is None:
                    raise RecoverableFillError(
                        f"{field.name} has no matching page option"
                    )
                await chosen.check()
            else:
                await locator.fill(value)
        except RecoverableFillError:
            raise
        except PlaywrightError as exc:
            # Do not include the value or raw Playwright text: either may contain
            # user-supplied form data that must not enter logs or traces.
            raise RecoverableFillError(
                f"browser could not fill {field.name}: {type(exc).__name__}"
            ) from exc

    async def submit(self) -> bool:
        if not self.submit_enabled:
            return False
        if self.page is None:
            raise RuntimeError("browser is not open")
        button = self.page.locator(
            'button[type="submit"], input[type="submit"], button:has-text("注册"), button:has-text("Register")'
        ).first
        if await button.count() == 0:
            raise RuntimeError("页面没有可识别的提交按钮")
        await button.click()
        await asyncio.sleep(1)
        return True

    async def close(self) -> None:
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        self.closed = True

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
