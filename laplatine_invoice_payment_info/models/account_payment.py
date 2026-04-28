from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import re
import unicodedata

DISPLAY_PAYMENT_MODE_SELECTION = [
    ("cash", "Espèces"),
    ("card", "Carte bancaire"),
    ("transfer", "Virement"),
    ("check", "Chèque"),
    ("other", "Autre"),
]

_NON_ALPHA_RE = re.compile(r"[^a-z]+")


def _normalize_journal_label(text):
    """Normalisation robuste pour matcher 'Espèces' même avec ponctuation/apostrophe typographique."""
    if not text:
        return ""

    # Apostrophes typographiques / quotes -> RIEN (sinon "l'espece" casse le token 'espece')
    cleaned = (
        str(text)
        .replace("’", "")
        .replace("‘", "")
        .replace("'", "")
        .replace("`", "")
    )

    # Accent-insensible : NFKD + suppression des marques diacritiques
    decomposed = unicodedata.normalize("NFKD", cleaned)
    stripped_chars = []
    for ch in decomposed:
        if unicodedata.category(ch) == "Mn":
            continue
        stripped_chars.append(ch)
    asciiish = "".join(stripped_chars)

    lowered = asciiish.lower()
    lowered = _NON_ALPHA_RE.sub("", lowered)
    return lowered


def laplatine_journal_is_cash_like(journal):
    """Journal configure comme caisse pour ce besoin La Platine.

    Odoo distingue journal Banque vs Caisse ; dans certains dossiers, le journal
    peut s'appeler 'Espèces' tout en restant type banque. On couvre donc :
    - type == cash (journal caisse standard)
    - nom/code contenant 'espece' / 'espèce' (sans accents / casse)
    """
    if not journal:
        return False

    if journal.type == "cash":
        return True

    name_key = _normalize_journal_label(journal.name)
    code_key = _normalize_journal_label(journal.code)

    # Tolère espèce/espèces/espece… après normalisation (ex: 'Espèces' -> 'especes').
    return ("espece" in name_key) or ("especes" in name_key) or ("espece" in code_key) or ("especes" in code_key)


def laplatine_allowed_codes_for_journal(journal):
    """Codes Selection « Info facture » autorisés pour ce journal."""
    if laplatine_journal_is_cash_like(journal):
        return {"cash"}
    return {code for code, _label in DISPLAY_PAYMENT_MODE_SELECTION if code != "cash"}


class AccountPayment(models.Model):
    _inherit = "account.payment"

    laplatine_display_payment_mode = fields.Selection(
        selection=DISPLAY_PAYMENT_MODE_SELECTION,
        string="Info facture",
        help="Information client affichée sur la facture PDF.",
    )

    def _laplatine_allowed_codes(self):
        self.ensure_one()
        return laplatine_allowed_codes_for_journal(self.journal_id)

    @api.onchange("journal_id")
    def _onchange_journal_id_laplatine_display_payment_mode(self):
        allowed = self._laplatine_allowed_codes()
        if self.laplatine_display_payment_mode not in allowed:
            self.laplatine_display_payment_mode = False

    @api.constrains("journal_id", "laplatine_display_payment_mode")
    def _check_laplatine_display_payment_mode(self):
        for pay in self:
            if not pay.laplatine_display_payment_mode:
                continue
            allowed = pay._laplatine_allowed_codes()
            if pay.laplatine_display_payment_mode not in allowed:
                raise ValidationError(
                    _("La valeur « Info facture » n'est pas compatible avec le journal sélectionné.")
                )
