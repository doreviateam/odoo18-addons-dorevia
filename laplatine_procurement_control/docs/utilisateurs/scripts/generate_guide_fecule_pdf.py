#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere le PDF utilisateur fécule (Vérena / Ethel)."""
from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
OUT_PDF = ROOT / "GUIDE_UTILISATEUR_FECULE_VERENA_ETHEL.pdf"
CAPTURES = ROOT / "captures" / "guide_fecule"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

COLOR_TITLE = (45, 55, 72)
COLOR_ACCENT = (139, 105, 20)
COLOR_BOX = (245, 247, 250)
COLOR_BOX_BORDER = (200, 205, 215)
COLOR_WARN = (255, 243, 224)


class GuideFeculePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=18)
        self.add_font("Arial", "", FONT_REG)
        self.add_font("Arial", "B", FONT_BOLD)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Arial", "B", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, "SARL La Platine - Guide fécule de manioc", align="C")
        self.ln(4)
        self.set_draw_color(*COLOR_BOX_BORDER)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font("Arial", "", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 8, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, number: str, title: str):
        self.ln(3)
        self.set_fill_color(*COLOR_ACCENT)
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 13)
        self.cell(0, 10, f"  {number}. {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def sub_title(self, text: str):
        self.set_font("Arial", "B", 11)
        self.set_text_color(*COLOR_TITLE)
        self.multi_cell(0, 6, text)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def body(self, text: str):
        self.set_font("Arial", "", 10.5)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def path_box(self, text: str):
        y = self.get_y()
        self.set_fill_color(*COLOR_BOX)
        self.set_draw_color(*COLOR_BOX_BORDER)
        self.set_font("Arial", "B", 10.5)
        self.rect(10, y, 190, 10, style="DF")
        self.set_xy(12, y + 2.5)
        self.cell(0, 6, text)
        self.ln(12)

    def example_box(self, lines: list[str]):
        y = self.get_y()
        height = 6 + len(lines) * 5.5
        self.set_fill_color(*COLOR_BOX)
        self.set_draw_color(*COLOR_BOX_BORDER)
        self.rect(10, y, 190, height, style="DF")
        self.set_xy(12, y + 3)
        self.set_font("Arial", "", 10)
        for line in lines:
            self.cell(0, 5.5, line, new_x="LMARGIN", new_y="NEXT")
            self.set_x(12)
        self.ln(4)

    def bullet(self, text: str, bold_prefix: str = ""):
        self.set_font("Arial", "", 10.5)
        x = self.get_x()
        self.cell(6, 5.5, "-")
        if bold_prefix:
            self.set_font("Arial", "B", 10.5)
            self.write(5.5, bold_prefix)
            self.set_font("Arial", "", 10.5)
            self.write(5.5, text[len(bold_prefix) :] if text.startswith(bold_prefix) else text)
        else:
            self.write(5.5, text)
        self.ln(6)

    def summary_table(self):
        rows = [
            ("Je retire de la fécule pour produire", "Consommation matière première"),
            ("Je compte la fécule restante", "Mise à jour des quantités en stock"),
            (
                "Une alerte de stock minimum apparaît",
                "Je termine l'enregistrement et je note le niveau affiché",
            ),
            ("Je ne suis pas sûre de la quantité", "J'annule avant de valider"),
        ]
        col1 = 95
        col2 = 95
        self.set_font("Arial", "B", 10)
        self.set_fill_color(*COLOR_TITLE)
        self.set_text_color(255, 255, 255)
        self.cell(col1, 8, "  Situation", border=1, fill=True)
        self.cell(col2, 8, "  Action", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.set_font("Arial", "", 9.5)
        fill = False
        for left, right in rows:
            if fill:
                self.set_fill_color(*COLOR_BOX)
            y0 = self.get_y()
            x0 = self.get_x()
            self.multi_cell(col1, 5.5, f"  {left}", border="LTR" if not fill else 1, fill=fill)
            y1 = self.get_y()
            h = y1 - y0
            self.set_xy(x0 + col1, y0)
            self.multi_cell(col2, 5.5, f"  {right}", border=1, fill=fill)
            self.set_xy(x0, max(y0 + h, self.get_y()))
            fill = not fill
        self.ln(3)

    def screenshot(self, filename: str, caption: str = "", width: float = 190):
        path = CAPTURES / filename
        if not path.exists():
            self.set_font("Arial", "I", 9)
            self.cell(0, 6, f"[Capture manquante : {filename}]", new_x="LMARGIN", new_y="NEXT")
            return
        if self.get_y() > 230:
            self.add_page()
        self.ln(2)
        self.image(str(path), w=width, x=10)
        self.ln(2)
        if caption:
            self.set_font("Arial", "", 9)
            self.set_text_color(90, 90, 90)
            self.multi_cell(0, 4, caption.replace("\u2014", "-"), align="C")
            self.set_text_color(0, 0, 0)
        self.ln(2)


def build_pdf() -> Path:
    pdf = GuideFeculePDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # --- Page 1 : couverture + à retenir ---
    pdf.set_font("Arial", "B", 22)
    pdf.set_text_color(*COLOR_TITLE)
    pdf.cell(0, 12, "Fécule de manioc", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", "", 14)
    pdf.set_text_color(*COLOR_ACCENT)
    pdf.cell(0, 8, "Guide d'utilisation", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, "Pour Vérena et Ethel", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "SARL La Platine", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "À retenir", new_x="LMARGIN", new_y="NEXT")
    pdf.summary_table()

    pdf.set_fill_color(*COLOR_BOX)
    pdf.set_draw_color(*COLOR_ACCENT)
    pdf.set_font("Arial", "B", 11)
    y = pdf.get_y() + 2
    pdf.rect(10, y, 190, 14, style="DF")
    pdf.set_xy(12, y + 4)
    pdf.multi_cell(
        186,
        5,
        "Je prélève = Consommation.     Je compte = Mise à jour du stock.",
        align="C",
    )
    pdf.ln(10)

    pdf.sub_title("Où trouver les deux fonctions ?")
    pdf.body(
        "Dans le menu Inventaire, ouvrir La Platine. Deux choix sont disponibles :"
    )
    pdf.bullet("Consommation matière première", "Consommation matière première")
    pdf.body("   quand vous retirez de la fécule pour la production.")
    pdf.bullet("Mise à jour des quantités en stock", "Mise à jour des quantités en stock")
    pdf.body("   quand vous avez compté la fécule restante.")
    pdf.screenshot("01_menu_la_platine.png", "Les deux menus sous Inventaire > La Platine")

    # --- Section 1 ---
    pdf.add_page()
    pdf.section_title("1", "Consommation de fécule")
    pdf.sub_title("Quand utiliser cet écran ?")
    pdf.body(
        "À chaque fois qu'une quantité de fécule de manioc est retirée du stock "
        "pour la production."
    )
    pdf.sub_title("Comment faire ?")
    pdf.path_box("Inventaire  >  La Platine  >  Consommation matière première")
    steps = [
        ("Choisir ", "FÉCULE DE MANIOC", " dans la liste."),
        ("Vérifier l'", "emplacement", " proposé (ne pas le modifier sauf consigne contraire)."),
        ("Lire la ", "Quantité disponible (kg)", "."),
        (
            "Saisir la ",
            "Quantité prélevée (kg)",
            " : la quantité retirée, pas ce qu'il reste.",
        ),
        ("Cliquer sur ", "Enregistrer la consommation", "."),
        ("Lire le message de confirmation ", "(quantité prélevée et stock restant)", "."),
    ]
    for i, parts in enumerate(steps, 1):
        pdf.set_font("Arial", "", 10.5)
        pdf.cell(8, 5.5, f"{i}.")
        if len(parts) == 3:
            pdf.write(5.5, parts[0])
            pdf.set_font("Arial", "B", 10.5)
            pdf.write(5.5, parts[1])
            pdf.set_font("Arial", "", 10.5)
            pdf.write(5.5, parts[2])
        pdf.ln(6)

    pdf.ln(2)
    pdf.sub_title("Exemple")
    pdf.example_box(
        [
            "Quantité disponible : 15 000,00 kg   (lue à l'écran)",
            "Quantité prélevée :       25,00 kg   (ce que vous saisissez)",
            "Stock restant :       14 975,00 kg   (indiqué dans la confirmation)",
        ]
    )
    pdf.screenshot(
        "02_consommation_fecule.png",
        "FÉCULE DE MANIOC sélectionnée - quantité disponible et quantité prélevée",
    )
    pdf.screenshot(
        "03_confirmation_consommation.png",
        "Message de confirmation après Enregistrer la consommation",
    )
    pdf.body(
        "Important : la quantité saisie correspond à la fécule retirée du stock, "
        "pas à la quantité restante."
    )

    # --- Section 2 ---
    pdf.add_page()
    pdf.section_title("2", "Mise à jour de la quantité en stock")
    pdf.sub_title("Quand utiliser cet écran ?")
    pdf.body(
        "Après un comptage physique, lorsque la quantité de fécule réellement "
        "présente est différente de celle affichée à l'écran."
    )
    pdf.sub_title("Comment faire ?")
    pdf.path_box("Inventaire  >  La Platine  >  Mise à jour des quantités en stock")
    steps2 = [
        "Choisir FÉCULE DE MANIOC.",
        "Vérifier l'emplacement.",
        "Lire la Quantité enregistrée dans Odoo.",
        "Saisir la Quantité réellement comptée : le total présent après comptage, pas l'écart.",
        "Renseigner le Motif (ex. Comptage du 05/07/2026).",
        "Cliquer sur Mettre à jour le stock.",
        "Confirmer dans la fenêtre qui s'ouvre.",
    ]
    for i, step in enumerate(steps2, 1):
        pdf.set_x(10)
        pdf.set_font("Arial", "", 10.5)
        pdf.multi_cell(190, 5.5, f"{i}. {step}")
    pdf.ln(2)
    pdf.sub_title("Exemple")
    pdf.example_box(
        [
            "Quantité enregistrée dans Odoo : 14 997,00 kg",
            "Quantité réellement comptée :    14 950,00 kg   (saisir le total compté)",
            "Écart calculé :                      -47,00 kg   (calculé automatiquement)",
        ]
    )
    pdf.screenshot(
        "04_mise_a_jour_fecule.png",
        "Quantité Odoo, quantité comptée, écart et motif",
    )
    pdf.screenshot(
        "05_confirmation_mise_a_jour.png",
        "Fenêtre de confirmation avant validation",
    )
    pdf.set_font("Arial", "B", 10.5)
    pdf.cell(0, 5.5, "A saisir : 14 950,00 kg", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", "B", 10.5)
    pdf.set_text_color(180, 40, 40)
    pdf.cell(0, 5.5, "Ne pas saisir : -47,00 kg (l'écart seul)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)

    # --- Section 3 ---
    pdf.add_page()
    pdf.section_title("3", "Alerte de stock minimum")
    pdf.body(
        "Après Enregistrer la consommation ou Mettre à jour le stock, un message "
        "peut apparaître si le stock de fécule est faible par rapport au minimum défini."
    )
    pdf.screenshot(
        "06_alerte_stock_minimum.png",
        "Alerte Seuil de réapprovisionnement atteint dans le message de confirmation",
        width=140,
    )
    pdf.sub_title("Ce qu'il faut savoir")
    pdf.bullet("L'alerte s'affiche dans l'écran que vous utilisez. Pas besoin d'aller ailleurs.")
    pdf.bullet("L'enregistrement n'est pas bloqué : l'opération est bien prise en compte.")
    pdf.bullet("L'alerte vous informe que le niveau de fécule est bas par rapport au minimum.")

    pdf.ln(4)
    pdf.section_title("4", "En cas de doute")
    pdf.bullet("Quantité incertaine : cliquer sur Annuler et recommencer après vérification.")
    pdf.bullet(
        "Mauvais écran : revenir au menu La Platine et choisir l'autre fonction "
        "(voir le tableau À retenir en page 1)."
    )

    pdf.ln(8)
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(130, 130, 130)
    pdf.multi_cell(
        0,
        4,
        "Document LAPLATINE-CONS-MP-USER-001 - Version juillet 2026 - "
        "Réservé à un usage interne SARL La Platine.",
        align="C",
    )

    pdf.output(str(OUT_PDF))
    return OUT_PDF


if __name__ == "__main__":
    path = build_pdf()
    print(f"PDF genere : {path}")
