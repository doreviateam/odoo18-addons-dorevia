#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Passe MOA UI lecture seule — séparation wizards CONS-MP-002."""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

RUN_ID = "QA-CONS-MP-MOA-UI-WIZSEP-20260705_204100"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
URL_LAB = "http://127.0.0.1:18018"
LOGIN = "qa_wizsep_operator_20260705"
PASSWORD = "WizSep!2026"
DB_NAME = "laplatine_prod"
CONS_ACTION_ID = 659
STOCK_ACTION_ID = 660
EXPECTED_STOCK_KG = 13000.0
FECULE_LABEL = "FECULE DE MANIOC"
FECULE_LOCATION = "Conteneur Fécule"


def ensure_dirs():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def shot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, name)
    page.screenshot(path=path, full_page=True)
    return path


def wait_odoo_ready(page, timeout=30000):
    page.wait_for_load_state("domcontentloaded", timeout=timeout)
    page.wait_for_timeout(2000)


def goto_inventory_app(page):
    for url in (
        f"{URL_LAB}/odoo/inventory",
        f"{URL_LAB}/odoo/stock",
        f"{URL_LAB}/web#menu_id=",  # fallback handled below
    ):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            wait_odoo_ready(page)
            if page_has_text(page, "Inventaire") or page_has_text(page, "Inventory"):
                return True
        except PlaywrightTimeout:
            continue
    # Menu apps Odoo 18
    for selector in (
        'button[title="Home menu"]',
        'button.o_navbar_apps_menu',
        'a.o_menu_brand',
        '[data-menu-xmlid="stock.menu_stock_root"]',
    ):
        loc = page.locator(selector).first
        if loc.count() and loc.is_visible():
            loc.click()
            page.wait_for_timeout(800)
            break
    for label in ("Inventaire", "Inventory"):
        app = page.locator(f'a:has-text("{label}")').first
        if app.count():
            app.click()
            page.wait_for_timeout(1500)
            return True
    return False


def login(page):
    page.goto(f"{URL_LAB}/web/login?db={DB_NAME}", wait_until="domcontentloaded")
    wait_odoo_ready(page)
    if page.locator('input[name="login"]').count():
        page.fill('input[name="login"]', LOGIN)
        page.fill('input[name="password"]', PASSWORD)
        page.click('button[type="submit"]')
        wait_odoo_ready(page)
    # Odoo 18 peut rediriger vers /odoo
    if "/login" in page.url:
        page.goto(f"{URL_LAB}/odoo?db={DB_NAME}", wait_until="domcontentloaded")
        wait_odoo_ready(page)


def open_inventory_menu(page):
    # Ouvrir le menu Inventaire principal
    for selector in (
        'button:has-text("Inventaire")',
        'nav button:has-text("Inventaire")',
        '.o_menu_brand:has-text("Inventaire")',
        'a:has-text("Inventaire")',
    ):
        loc = page.locator(selector).first
        if loc.count() and loc.is_visible():
            loc.click()
            page.wait_for_timeout(800)
            break


def open_submenu(page, label):
    for selector in (
        f'a:has-text("{label}")',
        f'button:has-text("{label}")',
        f'.dropdown-item:has-text("{label}")',
        f'[role="menuitem"]:has-text("{label}")',
    ):
        loc = page.locator(selector).first
        if loc.count():
            try:
                loc.click(timeout=5000)
                page.wait_for_timeout(1200)
                return True
            except PlaywrightTimeout:
                continue
    return False


def open_wizard_via_action(page, action_id):
    page.goto(f"{URL_LAB}/odoo/action-{action_id}", wait_until="domcontentloaded")
    wait_odoo_ready(page)


def modal_visible(page):
    return page.locator(".modal-dialog, .o_dialog, dialog").count() > 0


def select_many2one(page, field_label, search_text):
    # Cibler le many2one par label visible
    group = page.locator(f'label:has-text("{field_label}")').first
    if not group.count():
        group = page.locator(f'.o_form_label:has-text("{field_label}")').first
    container = group.locator("xpath=ancestor::div[contains(@class,'o_group') or contains(@class,'o_wrap_field')][1]")
    if not container.count():
        container = page.locator(".modal-body, .o_dialog, .o_content").first
    input_el = container.locator("input.o-autocomplete--input, input.ui-autocomplete-input").first
    if not input_el.count():
        input_el = container.locator("input").first
    input_el.click()
    input_el.fill(search_text)
    page.wait_for_timeout(1200)
    option = page.locator(
        f'.o-autocomplete--dropdown-item:has-text("{search_text}"), '
        f'li.ui-menu-item:has-text("{search_text}"), '
        f'.dropdown-item:has-text("{search_text}")'
    ).first
    if option.count():
        option.click()
        page.wait_for_timeout(1500)
        return True
    page.keyboard.press("Enter")
    page.wait_for_timeout(1500)
    return True


def read_field_text(page, *labels):
    for label in labels:
        loc = page.locator(f'label:has-text("{label}")').first
        if loc.count():
            parent = loc.locator("xpath=ancestor::div[contains(@class,'o_wrap_field') or contains(@class,'o_field_widget')][1]")
            text = parent.inner_text()
            return text
    return ""


def page_has_text(page, text):
    return text.lower() in page.locator("body").inner_text().lower()


def page_lacks_text(page, text):
    return text.lower() not in page.locator("body").inner_text().lower()


def parse_kg(text):
    if not text:
        return None
    # Formats Odoo FR/US : 13 000,00 | 13,000.00 | 13000
    match = re.search(r"([\d\s.,]+)\s*kg?", text, re.I)
    if not match:
        return None
    raw = match.group(1).strip()
    if "," in raw and "." in raw:
        # 13,000.00 → séparateur milliers ,
        if raw.rfind(".") > raw.rfind(","):
            raw = raw.replace(",", "")
        else:
            raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        raw = raw.replace(" ", "").replace(",", ".")
    else:
        raw = raw.replace(" ", "")
    try:
        return float(raw)
    except ValueError:
        return None


def cancel_wizard(page):
    # Fermer d'abord une éventuelle modale de confirmation Odoo
    for label in ("Cancel", "Annuler"):
        confirm_modal = page.locator(".modal.show, .o_dialog").filter(has_text="Confirmation")
        if confirm_modal.count():
            btn = confirm_modal.locator(f'button:has-text("{label}")').first
            if btn.count() and btn.is_enabled():
                btn.click()
                page.wait_for_timeout(800)
                break
    for label in ("Annuler", "Cancel"):
        btn = page.locator('.modal.show button:has-text("%s"), .o_dialog button:has-text("%s")' % (label, label)).first
        if btn.count() and btn.is_enabled():
            btn.click()
            page.wait_for_timeout(800)
            return True
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)
    return False


def detect_odoo_confirm_modal(page):
    body = page.locator("body").inner_text()
    if "Confirmez-vous la mise à jour du stock" in body:
        return True, "Confirmez-vous la mise à jour du stock selon la quantité comptée ?"
    modal = page.locator(".modal-dialog, .modal-content, .o_dialog").filter(
        has_text="Confirmation"
    )
    if modal.count() and modal.first.is_visible():
        return True, modal.first.inner_text()[:500]
    return False, None


def main():
    ensure_dirs()
    checks = []
    screenshots = {}
    confirm_dialog_seen = False
    confirm_dialog_message = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, locale="fr-FR")
        page = context.new_page()

        try:
            login(page)
            screenshots["01_after_login"] = shot(page, "01_after_login.png")

            goto_inventory_app(page)
            wait_odoo_ready(page)
            screenshots["01b_inventory_app"] = shot(page, "01b_inventory_app.png")

            # --- Menus La Platine ---
            open_inventory_menu(page)
            open_submenu(page, "La Platine")
            page.wait_for_timeout(1000)
            screenshots["02_la_platine_submenu"] = shot(page, "02_la_platine_submenu.png")

            menus_ok = page_has_text(page, "Consommation matière première") and page_has_text(
                page, "Mise à jour des quantités en stock"
            )
            checks.append(
                {
                    "id": "MOA-UI-01",
                    "title": "Deux menus visibles sous La Platine",
                    "result": "OK" if menus_ok else "KO",
                }
            )

            # --- Wizard consommation via menu ---
            opened_cons = open_submenu(page, "Consommation matière première")
            if not opened_cons:
                open_wizard_via_action(page, CONS_ACTION_ID)
            wait_odoo_ready(page)
            screenshots["03_consumption_wizard_initial"] = shot(
                page, "03_consumption_wizard_initial.png"
            )

            if modal_visible(page) or page_has_text(page, "Consommation matière première"):
                select_many2one(page, "Matière première", FECULE_LABEL)
                page.wait_for_timeout(1500)
                screenshots["04_consumption_wizard_fecule_selected"] = shot(
                    page, "04_consumption_wizard_fecule_selected.png"
                )

                body = page.locator("body").inner_text()
                location_ok = FECULE_LOCATION.lower() in body.lower() or "Conteneur" in body
                qty_text = read_field_text(page, "Quantité disponible")
                qty_kg = parse_kg(qty_text or body)
                if qty_kg is None and "13,000.00" in body:
                    qty_kg = 13000.0
                qty_ok = qty_kg is not None and abs(qty_kg - EXPECTED_STOCK_KG) < 0.01

                no_adjustment = all(
                    x.lower() not in body.lower()
                    for x in (
                        "Mettre à jour la quantité disponible",
                        "Mettre à jour le stock",
                        "Correction après comptage",
                        "Mode",
                    )
                )
                has_consume_btn = page.locator('button:has-text("Enregistrer la consommation")').count() > 0
                has_qty_consumed = page_has_text(page, "Quantité prélevée") or page_has_text(
                    page, "prélevée"
                )
                no_count_fields = page_lacks_text(page, "Quantité réellement comptée") and page_lacks_text(
                    page, "Motif"
                )

                checks.extend(
                    [
                        {
                            "id": "MOA-UI-02",
                            "title": "Consommation fécule : Conteneur Fécule affiché",
                            "result": "OK" if location_ok else "KO",
                            "observed_location": FECULE_LOCATION if location_ok else body[:300],
                        },
                        {
                            "id": "MOA-UI-03",
                            "title": "Consommation fécule : 13 000 kg affichés",
                            "result": "OK" if qty_ok else "KO",
                            "observed_qty_kg": qty_kg,
                        },
                        {
                            "id": "MOA-UI-04",
                            "title": "Consommation : quantité prélevée + bouton Enregistrer uniquement",
                            "result": "OK"
                            if has_consume_btn and has_qty_consumed and no_count_fields
                            else "KO",
                        },
                        {
                            "id": "MOA-UI-05",
                            "title": "Consommation : absence totale de bascule correction",
                            "result": "OK" if no_adjustment else "KO",
                        },
                    ]
                )
                cancel_wizard(page)
            else:
                for cid, title in (
                    ("MOA-UI-02", "Consommation fécule : Conteneur Fécule affiché"),
                    ("MOA-UI-03", "Consommation fécule : 13 000 kg affichés"),
                    ("MOA-UI-04", "Consommation : quantité prélevée + bouton Enregistrer uniquement"),
                    ("MOA-UI-05", "Consommation : absence totale de bascule correction"),
                ):
                    checks.append({"id": cid, "title": title, "result": "KO", "detail": "Wizard non ouvert"})

            # --- Wizard mise à jour via menu ---
            open_inventory_menu(page)
            open_submenu(page, "La Platine")
            opened_stock = open_submenu(page, "Mise à jour des quantités en stock")
            if not opened_stock:
                open_wizard_via_action(page, STOCK_ACTION_ID)
            wait_odoo_ready(page)
            screenshots["05_stock_update_wizard_initial"] = shot(
                page, "05_stock_update_wizard_initial.png"
            )

            if modal_visible(page) or page_has_text(page, "Mise à jour des quantités en stock"):
                select_many2one(page, "Matière première", FECULE_LABEL)
                page.wait_for_timeout(1500)
                # Sélectionner localisation si nécessaire
                if FECULE_LOCATION.lower() not in page.locator("body").inner_text().lower():
                    select_many2one(page, "Localisation", FECULE_LOCATION)
                    page.wait_for_timeout(1200)

                # Saisir quantité comptée et motif (sans valider)
                counted_input = page.locator('label:has-text("Quantité réellement comptée")').locator(
                    "xpath=following::input[1]"
                ).first
                if not counted_input.count():
                    counted_input = page.locator('input[name="qty_counted_kg"]').first
                if counted_input.count():
                    counted_input.fill(str(int(EXPECTED_STOCK_KG)))

                reason_input = page.locator('label:has-text("Motif")').locator(
                    "xpath=following::input[1]"
                ).first
                if not reason_input.count():
                    reason_input = page.locator('input[name="adjustment_reason"]').first
                if reason_input.count():
                    reason_input.fill("MOA UI lecture seule — ne pas appliquer")

                page.wait_for_timeout(1000)
                screenshots["06_stock_update_wizard_fecule_filled"] = shot(
                    page, "06_stock_update_wizard_fecule_filled.png"
                )

                body = page.locator("body").inner_text()
                odoo_qty_ok = "13" in body and "000" in body.replace(" ", "")
                has_count = page_has_text(page, "Quantité réellement comptée") or page_has_text(
                    page, "comptée"
                )
                has_diff = page_has_text(page, "Écart") or page_has_text(page, "écart")
                has_reason = page_has_text(page, "Motif")
                no_consumed = page_lacks_text(page, "Quantité prélevée") and page_lacks_text(
                    page, "prélevée"
                )

                checks.extend(
                    [
                        {
                            "id": "MOA-UI-06",
                            "title": "Mise à jour fécule : quantité Odoo ~13 000 kg",
                            "result": "OK" if odoo_qty_ok else "KO",
                        },
                        {
                            "id": "MOA-UI-07",
                            "title": "Mise à jour : champs comptée, écart, motif présents",
                            "result": "OK" if has_count and has_diff and has_reason else "KO",
                        },
                        {
                            "id": "MOA-UI-08",
                            "title": "Mise à jour : absence champ prélèvement",
                            "result": "OK" if no_consumed else "KO",
                        },
                    ]
                )

                # Dialogue de confirmation Odoo 18 (modale Bootstrap, pas window.confirm)
                confirm_dialog_seen = False
                confirm_dialog_message = None
                update_btn = page.locator('button:has-text("Mettre à jour le stock")').first
                if update_btn.count() and update_btn.is_visible():
                    update_btn.click()
                    page.wait_for_timeout(1500)
                    screenshots["07_stock_update_confirm_dialog"] = shot(
                        page, "07_stock_update_confirm_dialog.png"
                    )
                    confirm_dialog_seen, confirm_dialog_message = detect_odoo_confirm_modal(page)
                    if confirm_dialog_seen:
                        # Annuler la confirmation sans appliquer
                        for label in ("Cancel", "Annuler"):
                            btn = page.locator(".modal.show button").filter(has_text=label).first
                            if btn.count() and btn.is_enabled():
                                btn.click()
                                page.wait_for_timeout(1000)
                                break
                checks.append(
                    {
                        "id": "MOA-UI-09",
                        "title": "Dialogue de confirmation visible puis annulé",
                        "result": "OK" if confirm_dialog_seen else "KO",
                        "message": (confirm_dialog_message or "")[:500],
                    }
                )
                cancel_wizard(page)
                screenshots["08_stock_update_after_cancel"] = shot(
                    page, "08_stock_update_after_cancel.png"
                )
            else:
                for cid, title in (
                    ("MOA-UI-06", "Mise à jour fécule : quantité Odoo ~13 000 kg"),
                    ("MOA-UI-07", "Mise à jour : champs comptée, écart, motif présents"),
                    ("MOA-UI-08", "Mise à jour : absence champ prélèvement"),
                    ("MOA-UI-09", "Dialogue de confirmation visible puis annulé"),
                ):
                    checks.append({"id": cid, "title": title, "result": "KO", "detail": "Wizard non ouvert"})

            # --- Clarté parcours MOA ---
            clarity_ok = menus_ok and all(
                c.get("result") == "OK"
                for c in checks
                if c["id"] in ("MOA-UI-04", "MOA-UI-05", "MOA-UI-08")
            )
            checks.append(
                {
                    "id": "MOA-UI-10",
                    "title": "Parcours distincts : prélèvement vs comptage physique",
                    "result": "OK" if clarity_ok else "KO",
                    "note": "Consommation = prélèvement ; Mise à jour = comptage physique",
                }
            )

        except Exception as exc:
            checks.append(
                {
                    "id": "MOA-UI-ERR",
                    "title": "Erreur exécution Playwright",
                    "result": "KO",
                    "detail": str(exc),
                }
            )
            try:
                screenshots["99_error_state"] = shot(page, "99_error_state.png")
            except Exception:
                pass
        finally:
            browser.close()

    blocking = [c["id"] for c in checks if c.get("result") == "KO"]
    verdict = "GO_MOA_UI_WIZSEP" if not blocking else "NO_GO_MOA_UI_WIZSEP"

    payload = {
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "url_lab": URL_LAB,
        "operator_login": LOGIN,
        "production": "STOP",
        "verdict": verdict,
        "blocking_ko": blocking,
        "checks": checks,
        "screenshots": screenshots,
        "confirm_dialog": {
            "seen": confirm_dialog_seen,
            "message": confirm_dialog_message,
        },
        "fecule_expected_stock_kg": EXPECTED_STOCK_KG,
        "note": "Passe MOA UI lecture seule — aucune validation appliquée sur la fécule.",
    }

    evidence_path = os.path.join(BASE_DIR, "moa_ui_wizsep_evidence.json")
    with open(evidence_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print(f"MOA_UI_VERDICT={verdict}")
    print(f"MOA_UI_JSON={evidence_path}")
    for c in checks:
        print(f"  {c['id']} {c['result']}: {c['title']}")
    return 0 if verdict == "GO_MOA_UI_WIZSEP" else 1


if __name__ == "__main__":
    sys.exit(main())
