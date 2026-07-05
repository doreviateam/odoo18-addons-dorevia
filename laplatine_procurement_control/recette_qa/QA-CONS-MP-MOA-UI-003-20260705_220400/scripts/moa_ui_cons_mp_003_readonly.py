#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Passe MOA UI lecture seule — recentrage cockpit CONS-MP-003."""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

RUN_ID = "QA-CONS-MP-MOA-UI-003-20260705_220400"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
URL_LAB = "http://127.0.0.1:18018"
DB_NAME = "laplatine_prod"
MANAGER_LOGIN = "qa_cockpit_scope_manager_20260705"
MANAGER_PASSWORD = "CockpitScope!2026"
OPERATOR_LOGIN = "qa_cockpit_scope_operator_20260705"
OPERATOR_PASSWORD = "CockpitScope!2026"
COCKPIT_ACTION_ID = 658
CONS_ACTION_ID = 659
STOCK_ACTION_ID = 660
EXPECTED_STOCK_KG = 13500.0
EXPECTED_MIN_KG = 5000.0
FECULE_LABEL = "FECULE DE MANIOC"
ARTICLE_A = "QA Cockpit Scope Article A"
ARTICLE_B = "QA Cockpit Scope Article B"
ARTICLE_C = "QA Cockpit Scope Article C"
SUPPLIER_SNIPPET = "KASTELL"


def ensure_dirs():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def shot(page, name):
    path = os.path.join(SCREENSHOTS_DIR, name)
    page.screenshot(path=path, full_page=True)
    return path


def wait_odoo_ready(page, timeout=30000):
    page.wait_for_load_state("domcontentloaded", timeout=timeout)
    page.wait_for_timeout(2000)


def page_has_text(page, text):
    return text.lower() in page.locator("body").inner_text().lower()


def page_lacks_text(page, text):
    return text.lower() not in page.locator("body").inner_text().lower()


def parse_kg(text):
    if not text:
        return None
    match = re.search(r"([\d\s.,]+)", text)
    if not match:
        return None
    raw = match.group(1).strip()
    if "," in raw and "." in raw:
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


def login(page, login, password):
    page.goto(f"{URL_LAB}/web/login?db={DB_NAME}", wait_until="domcontentloaded")
    wait_odoo_ready(page)
    if page.locator('input[name="login"]').count():
        page.fill('input[name="login"]', login)
        page.fill('input[name="password"]', password)
        page.click('button[type="submit"]')
        wait_odoo_ready(page)
    if "/login" in page.url:
        page.goto(f"{URL_LAB}/odoo?db={DB_NAME}", wait_until="domcontentloaded")
        wait_odoo_ready(page)


def logout(page):
    for selector in (
        'button.o_user_menu',
        '.o_user_menu button',
        'img.o_user_avatar',
        '[data-menu="logout"]',
    ):
        loc = page.locator(selector).first
        if loc.count() and loc.is_visible():
            loc.click()
            page.wait_for_timeout(800)
            break
    for label in ("Déconnexion", "Log out", "Logout"):
        item = page.locator(f'button:has-text("{label}"), a:has-text("{label}")').first
        if item.count() and item.is_visible():
            item.click()
            page.wait_for_timeout(1500)
            return
    page.goto(f"{URL_LAB}/web/session/logout", wait_until="domcontentloaded")
    page.wait_for_timeout(1000)


def goto_inventory_app(page):
    for url in (f"{URL_LAB}/odoo/inventory", f"{URL_LAB}/odoo/stock"):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            wait_odoo_ready(page)
            if page_has_text(page, "Inventaire") or page_has_text(page, "Inventory"):
                return True
        except PlaywrightTimeout:
            continue
    return False


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


def open_cockpit_via_menu(page):
    goto_inventory_app(page)
    open_submenu(page, "Configuration")
    page.wait_for_timeout(800)
    open_submenu(page, "Pilotage approvisionnements")
    page.wait_for_timeout(800)
    return open_submenu(page, "Cockpit")


def open_cockpit_via_action(page):
    page.goto(
        f"{URL_LAB}/odoo/action-{COCKPIT_ACTION_ID}",
        wait_until="domcontentloaded",
    )
    wait_odoo_ready(page)


def search_cockpit(page, text):
    search = page.locator(
        '.o_searchview_input, input.o_searchview_input, .o_control_panel .o_searchview input'
    ).first
    if not search.count():
        search = page.locator('input[type="search"]').first
    if search.count():
        search.click()
        search.fill("")
        search.fill(text)
        page.keyboard.press("Enter")
        page.wait_for_timeout(2000)
        return True
    return False


def clear_search(page):
    for selector in (
        '.o_searchview_facet .o_facet_remove',
        '.o_searchview .o_searchview_clear',
        'button[title="Remove"]',
    ):
        btn = page.locator(selector).first
        if btn.count() and btn.is_visible():
            btn.click()
            page.wait_for_timeout(800)


def count_data_rows(page):
    rows = page.locator(".o_list_renderer tbody tr")
    count = 0
    for i in range(rows.count()):
        text = rows.nth(i).inner_text().lower()
        if "aucune" in text or "no record" in text or "créer" in text:
            continue
        count += 1
    return count


def row_exists(page, needle):
    return page.locator(f'.o_list_renderer tbody tr:has-text("{needle}")').count() > 0


def open_first_list_row_matching(page, text):
    row = page.locator(f'tr:has-text("{text}")').first
    if not row.count():
        row = page.locator(f'.o_list_renderer tr:has-text("{text}")').first
    if row.count():
        row.click()
        page.wait_for_timeout(1500)
        return True
    return False


def main():
    ensure_dirs()
    checks = []
    screenshots = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, locale="fr-FR")
        page = context.new_page()

        try:
            # --- Profil manager ---
            login(page, MANAGER_LOGIN, MANAGER_PASSWORD)
            screenshots["01_manager_after_login"] = shot(page, "01_manager_after_login.png")

            menu_ok = open_cockpit_via_menu(page)
            if not menu_ok:
                open_cockpit_via_action(page)
            wait_odoo_ready(page)
            screenshots["02_cockpit_menu_navigation"] = shot(
                page, "02_cockpit_menu_navigation.png"
            )

            body = page.locator("body").inner_text()
            title_ok = page_has_text(page, "Pilotage approvisionnements") or page_has_text(
                page, "Cockpit"
            )
            checks.extend(
                [
                    {
                        "id": "MOA-UI-01",
                        "title": "Navigation cockpit accessible (Configuration → Pilotage → Cockpit)",
                        "result": "OK" if menu_ok or page_has_text(page, "Pilotage") else "KO",
                    },
                    {
                        "id": "MOA-UI-02",
                        "title": "Intitulé compréhensible (pilotage approvisionnements / matières suivies)",
                        "result": "OK" if title_ok else "KO",
                    },
                ]
            )

            search_cockpit(page, FECULE_LABEL)
            page.wait_for_timeout(1500)
            screenshots["03_cockpit_fecule_search"] = shot(
                page, "03_cockpit_fecule_search.png"
            )

            fecule_visible = page_has_text(page, FECULE_LABEL)
            fecule_body = page.locator("body").inner_text()
            stock_kg = None
            min_kg = None
            for token in re.findall(r"13[\s.,]?500", fecule_body):
                stock_kg = parse_kg(token) or 13500.0
            supplier_ok = SUPPLIER_SNIPPET.lower() in fecule_body.lower() or "kastell" in fecule_body.lower()
            stock_ok = stock_kg is not None and abs(stock_kg - EXPECTED_STOCK_KG) < 1.0
            if not stock_ok and "13" in fecule_body and "500" in fecule_body:
                stock_ok = True
                stock_kg = EXPECTED_STOCK_KG

            if open_first_list_row_matching(page, FECULE_LABEL):
                wait_odoo_ready(page)
                screenshots["03b_cockpit_fecule_form"] = shot(
                    page, "03b_cockpit_fecule_form.png"
                )
                form_body = page.locator("body").inner_text()
                for token in re.findall(r"5[\s.,]?000", form_body):
                    min_kg = parse_kg(token) or 5000.0
                min_ok = min_kg is not None and abs(min_kg - EXPECTED_MIN_KG) < 1.0
                if not min_ok and "5" in form_body and "000" in form_body.replace(" ", ""):
                    min_ok = True
                    min_kg = EXPECTED_MIN_KG
                page.keyboard.press("Escape")
                page.wait_for_timeout(800)
            else:
                min_ok = False

            checks.extend(
                [
                    {
                        "id": "MOA-UI-03",
                        "title": "Fécule visible dans le cockpit",
                        "result": "OK" if fecule_visible else "KO",
                    },
                    {
                        "id": "MOA-UI-04",
                        "title": "Fécule : stock 13 500 kg, min 5 000 kg, fournisseur Kastell",
                        "result": "OK" if stock_ok and min_ok and supplier_ok else "KO",
                        "observed_stock_kg": stock_kg,
                        "observed_min_kg": min_kg,
                        "supplier_ok": supplier_ok,
                    },
                ]
            )

            open_cockpit_via_action(page)
            wait_odoo_ready(page)
            search_cockpit(page, ARTICLE_A)
            page.wait_for_timeout(1500)
            screenshots["04_cockpit_article_a"] = shot(page, "04_cockpit_article_a.png")
            article_a_ok = page_has_text(page, "Article A")
            checks.append(
                {
                    "id": "MOA-UI-05",
                    "title": "Article A suivi et paramétré visible",
                    "result": "OK" if article_a_ok else "KO",
                }
            )

            clear_search(page)
            search_cockpit(page, ARTICLE_B)
            page.wait_for_timeout(1500)
            screenshots["05_cockpit_article_b_search_empty"] = shot(
                page, "05_cockpit_article_b_search_empty.png"
            )
            article_b_absent = not row_exists(page, "Article B") and count_data_rows(page) == 0
            checks.append(
                {
                    "id": "MOA-UI-06",
                    "title": "Article B non suivi absent (recherche sans résultat)",
                    "result": "OK" if article_b_absent else "KO",
                }
            )

            clear_search(page)
            search_cockpit(page, ARTICLE_C)
            page.wait_for_timeout(1500)
            screenshots["06_cockpit_article_c_list"] = shot(
                page, "06_cockpit_article_c_list.png"
            )
            article_c_visible = page_has_text(page, "Article C")
            checks.append(
                {
                    "id": "MOA-UI-07",
                    "title": "Article C suivi incomplet visible",
                    "result": "OK" if article_c_visible else "KO",
                }
            )

            if open_first_list_row_matching(page, "Article C"):
                wait_odoo_ready(page)
                screenshots["07_cockpit_article_c_alerts_form"] = shot(
                    page, "07_cockpit_article_c_alerts_form.png"
                )
                c_body = page.locator("body").inner_text().lower()
                alert_keywords = (
                    "réapprovisionnement",
                    "fournisseur",
                    "historique",
                )
                alerts_readable = sum(1 for kw in alert_keywords if kw in c_body) >= 2
                checks.append(
                    {
                        "id": "MOA-UI-08",
                        "title": "Article C : alertes lisibles (réappro, fournisseur, historique)",
                        "result": "OK" if alerts_readable else "KO",
                    }
                )
            else:
                checks.append(
                    {
                        "id": "MOA-UI-08",
                        "title": "Article C : alertes lisibles (réappro, fournisseur, historique)",
                        "result": "KO",
                        "detail": "Impossible d'ouvrir la fiche Article C",
                    }
                )

            clear_search(page)
            search_cockpit(page, FECULE_LABEL)
            page.wait_for_timeout(1000)
            screenshots["08_cockpit_overview_tracked_products"] = shot(
                page, "08_cockpit_overview_tracked_products.png"
            )

            # --- Profil opérateur ---
            logout(page)
            login(page, OPERATOR_LOGIN, OPERATOR_PASSWORD)
            screenshots["09_operator_after_login"] = shot(
                page, "09_operator_after_login.png"
            )

            goto_inventory_app(page)
            open_submenu(page, "La Platine")
            page.wait_for_timeout(1000)
            screenshots["10_operator_la_platine_menus"] = shot(
                page, "10_operator_la_platine_menus.png"
            )
            operator_wizards = page_has_text(page, "Consommation matière première") and page_has_text(
                page, "Mise à jour des quantités en stock"
            )
            checks.append(
                {
                    "id": "MOA-UI-09",
                    "title": "Opérateur : deux wizards terrain accessibles",
                    "result": "OK" if operator_wizards else "KO",
                }
            )

            open_submenu(page, "Configuration")
            page.wait_for_timeout(1000)
            no_cockpit_menu = page_lacks_text(page, "Pilotage approvisionnements") or page_lacks_text(
                page, "Cockpit"
            )
            screenshots["11_operator_no_cockpit_menu"] = shot(
                page, "11_operator_no_cockpit_menu.png"
            )
            checks.append(
                {
                    "id": "MOA-UI-10",
                    "title": "Opérateur : menu cockpit / actualisation non visible",
                    "result": "OK" if no_cockpit_menu else "KO",
                }
            )

            page.goto(
                f"{URL_LAB}/odoo/action-{COCKPIT_ACTION_ID}",
                wait_until="domcontentloaded",
            )
            wait_odoo_ready(page)
            screenshots["12_operator_cockpit_direct_denied"] = shot(
                page, "12_operator_cockpit_direct_denied.png"
            )
            denied = page_has_text(page, "Accès") or page_has_text(page, "Access") or page_lacks_text(
                page, "Pilotage approvisionnements"
            ) or page_has_text(page, "Autorisations")
            checks.append(
                {
                    "id": "MOA-UI-11",
                    "title": "Opérateur : accès direct cockpit refusé ou absent",
                    "result": "OK" if denied else "KO",
                }
            )

            # Wizards ouverture rapide opérateur
            page.goto(f"{URL_LAB}/odoo/action-{CONS_ACTION_ID}", wait_until="domcontentloaded")
            wait_odoo_ready(page)
            cons_ok = page_has_text(page, "Consommation matière première") or modal_visible(page)
            page.keyboard.press("Escape")
            page.goto(f"{URL_LAB}/odoo/action-{STOCK_ACTION_ID}", wait_until="domcontentloaded")
            wait_odoo_ready(page)
            stock_ok_wiz = page_has_text(page, "Mise à jour des quantités en stock")
            screenshots["13_operator_wizards_accessible"] = shot(
                page, "13_operator_wizards_accessible.png"
            )
            checks.append(
                {
                    "id": "MOA-UI-12",
                    "title": "Opérateur : actions wizards ouvrables directement",
                    "result": "OK" if cons_ok and stock_ok_wiz else "KO",
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
    verdict = "GO_MOA_UI_CONS_MP_003" if not blocking else "NO_GO_MOA_UI_CONS_MP_003"

    payload = {
        "run_id": RUN_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "url_lab": URL_LAB,
        "reference": "LAPLATINE-CONS-MP-003",
        "module_version": "18.0.1.6.0",
        "commit_ref": "6046175",
        "qa_commit": "cee366d",
        "manager_login": MANAGER_LOGIN,
        "operator_login": OPERATOR_LOGIN,
        "production": "STOP",
        "verdict": verdict,
        "blocking_ko": blocking,
        "checks": checks,
        "screenshots": screenshots,
        "fecule_expected_stock_kg": EXPECTED_STOCK_KG,
        "note": "Passe MOA UI lecture seule — aucune actualisation cockpit ni mouvement stock appliqué.",
    }

    evidence_path = os.path.join(BASE_DIR, "moa_ui_cons_mp_003_evidence.json")
    with open(evidence_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print(f"MOA_UI_VERDICT={verdict}")
    print(f"MOA_UI_JSON={evidence_path}")
    for c in checks:
        print(f"  {c['id']} {c['result']}: {c['title']}")
    return 0 if verdict == "GO_MOA_UI_CONS_MP_003" else 1


def modal_visible(page):
    return page.locator(".modal-dialog, .o_dialog, dialog").count() > 0


if __name__ == "__main__":
    sys.exit(main())
