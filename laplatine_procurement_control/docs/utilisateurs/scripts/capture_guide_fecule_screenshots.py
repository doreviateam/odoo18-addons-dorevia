#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Captures ecran guide utilisateur fécule (production)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "captures" / "guide_fecule"

URL = os.environ.get("GUIDE_CAPTURE_URL", "https://prod.sarl-la-platine.fr")
DB = os.environ.get("GUIDE_CAPTURE_DB", "laplatine_prod")
LOGIN = os.environ.get("GUIDE_CAPTURE_LOGIN", "ethel")
PASSWORD = os.environ.get("GUIDE_CAPTURE_PASSWORD", "")
CONS_ACTION = int(os.environ.get("GUIDE_CAPTURE_CONS_ACTION", "659"))
STOCK_ACTION = int(os.environ.get("GUIDE_CAPTURE_STOCK_ACTION", "660"))
FECULE = "FECULE"
LOCATION = "Conteneur"
QTY_PRELEVEE = "25"
QTY_COMPTee = "920"
MOTIF = "Comptage physique - guide utilisateur"


def wait(page, ms=1500):
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(ms)


def shot(page, name: str, selector: str | None = None):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    if selector:
        loc = page.locator(selector).first
        if loc.count() and loc.is_visible():
            loc.screenshot(path=str(path))
            return path
    page.locator(".o_action_manager, .o_content").first.screenshot(path=str(path))
    return path


def login(page):
    if not PASSWORD:
        raise RuntimeError("GUIDE_CAPTURE_PASSWORD requis")
    page.goto(f"{URL}/web/login?db={DB}", wait_until="domcontentloaded")
    wait(page)
    page.fill('input[name="login"]', LOGIN)
    page.fill('input[name="password"]', PASSWORD)
    page.click('button[type="submit"]')
    wait(page, 3000)


def goto_inventory(page):
    page.goto(f"{URL}/odoo/inventory", wait_until="domcontentloaded")
    wait(page, 2000)


def click_nav(page, label: str) -> bool:
    for sel in (
        f'nav button:has-text("{label}")',
        f'button:has-text("{label}")',
        f'.o_menu_sections button:has-text("{label}")',
        f'a:has-text("{label}")',
    ):
        loc = page.locator(sel).first
        if loc.count() and loc.is_visible():
            loc.click(timeout=5000)
            wait(page, 1000)
            return True
    return False


def open_wizard(page, action_id: int):
    page.goto(f"{URL}/odoo/action-{action_id}", wait_until="domcontentloaded")
    wait(page, 2500)


def select_field_m2o(page, field_name: str, text: str):
    widget = page.locator(f'div[name="{field_name}"] input, .o_field_widget[name="{field_name}"] input').first
    widget.click()
    widget.fill(text)
    wait(page, 1200)
    opt = page.locator(
        f'.o-autocomplete--dropdown-item:has-text("{text}"), '
        f'li.ui-menu-item:has-text("{text}"), '
        f'.dropdown-item:has-text("{text}")'
    ).first
    if opt.count():
        opt.click()
    else:
        page.keyboard.press("Enter")
    wait(page, 1800)


def fill_field(page, field_name: str, value: str):
    loc = page.locator(
        f'div[name="{field_name}"] input, .o_field_widget[name="{field_name}"] input'
    ).first
    loc.click()
    loc.fill(value)
    loc.press("Tab")
    wait(page, 1000)


def wizard_shot(page, name: str):
    for sel in (
        ".o_form_view_container",
        ".o_content",
        ".o_action_manager",
    ):
        loc = page.locator(sel).first
        if loc.count() and loc.is_visible():
            return shot(page, name, sel)
    return shot(page, name)


def main() -> int:
    paths = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1360, "height": 900}, locale="fr-FR")
        try:
            login(page)
            goto_inventory(page)

            # 01 - menu La Platine ouvert
            click_nav(page, "La Platine")
            wait(page, 800)
            paths["01"] = page.screenshot(
                path=str(OUT_DIR / "01_menu_la_platine.png"), full_page=False
            ) or OUT_DIR / "01_menu_la_platine.png"

            # 02 - consommation
            open_wizard(page, CONS_ACTION)
            select_field_m2o(page, "product_id", FECULE)
            body = page.locator("body").inner_text()
            if LOCATION.lower() not in body.lower():
                select_field_m2o(page, "location_id", LOCATION)
            fill_field(page, "qty_consumed_kg", QTY_PRELEVEE)
            wait(page, 1500)
            paths["02"] = wizard_shot(page, "02_consommation_fecule.png")

            # 03 + 06 - consommation 1 kg + notification
            fill_field(page, "qty_consumed_kg", "1")
            page.locator('button:has-text("Enregistrer la consommation")').first.click()
            wait(page, 3500)
            page.screenshot(path=str(OUT_DIR / "03_confirmation_consommation.png"), full_page=False)
            paths["03"] = OUT_DIR / "03_confirmation_consommation.png"

            notif = page.locator(".o_notification_manager, .o_notification").first
            if notif.count() and notif.is_visible():
                notif.screenshot(path=str(OUT_DIR / "06_alerte_stock_minimum.png"))
            else:
                page.screenshot(path=str(OUT_DIR / "06_alerte_stock_minimum.png"), full_page=False)
            paths["06"] = OUT_DIR / "06_alerte_stock_minimum.png"

            wait(page, 1000)
            page.keyboard.press("Escape")

            # 04 - mise a jour
            open_wizard(page, STOCK_ACTION)
            select_field_m2o(page, "product_id", FECULE)
            body = page.locator("body").inner_text()
            if LOCATION.lower() not in body.lower():
                select_field_m2o(page, "location_id", LOCATION)
            fill_field(page, "qty_counted_kg", QTY_COMPTee)
            fill_field(page, "adjustment_reason", MOTIF)
            wait(page, 1500)
            paths["04"] = wizard_shot(page, "04_mise_a_jour_fecule.png")

            # 05 - confirmation
            page.locator('button:has-text("Mettre à jour le stock")').first.click()
            wait(page, 2000)
            modal = page.locator(".modal-dialog, .modal-content").first
            if modal.count() and modal.is_visible():
                modal.screenshot(path=str(OUT_DIR / "05_confirmation_mise_a_jour.png"))
            else:
                wizard_shot(page, "05_confirmation_mise_a_jour.png")
            paths["05"] = OUT_DIR / "05_confirmation_mise_a_jour.png"

            for label in ("Annuler", "Cancel"):
                btn = page.locator(f'.modal.show button:has-text("{label}")').first
                if btn.count() and btn.is_enabled():
                    btn.click()
                    break

        finally:
            browser.close()

    print("Captures produites dans", OUT_DIR)
    for name in (
        "01_menu_la_platine.png",
        "02_consommation_fecule.png",
        "03_confirmation_consommation.png",
        "04_mise_a_jour_fecule.png",
        "05_confirmation_mise_a_jour.png",
        "06_alerte_stock_minimum.png",
    ):
        p = OUT_DIR / name
        print(f"  {'OK' if p.exists() else 'KO'} {name} ({p.stat().st_size if p.exists() else 0} bytes)")
        if not p.exists():
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
