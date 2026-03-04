"""
sources/alertes.py
Système d'alertes sur mots-clés appliqué aux articles RSS.
Aucune API externe requise.
"""

import pandas as pd
from datetime import datetime, timedelta
import pytz

PARIS_TZ = pytz.timezone("Europe/Paris")

# ── Mots-clés par thème ─────────────────────────────────────────────────────

MOTS_CLES_PAR_THEME = {
    "🔴 Constitutionnel": [
        "49.3", "motion de censure", "dissolution",
        "article 16", "référendum", "constituante",
    ],
    "⚖️ Justice": [
        "inéligibilité", "garde à vue", "mis en examen",
        "condamné", "procès", "tribunal", "perquisition",
        "parquet national financier", "PNF",
    ],
    "💰 Budget & Économie": [
        "déficit", "dette publique", "plan d'austérité",
        "plan de rigueur", "récession", "chômage",
        "inflation", "plan social", "licenciements",
    ],
    "🌍 Diplomatie": [
        "rupture diplomatique", "rappel ambassadeur",
        "déclaration de guerre", "sanctions", "traité",
        "sommet", "crise diplomatique",
    ],
    "⚡ Social": [
        "grève générale", "grève nationale", "manifestation",
        "émeutes", "état d'urgence", "couvre-feu",
        "blocage", "gilets jaunes",
    ],
    "🗳️ Électoral": [
        "sondage", "intentions de vote", "candidature",
        "présidentielle", "législatives", "dissolution",
        "second tour", "triangulaire",
    ],
    "🛡️ Sécurité & Défense": [
        "attentat", "alerte terroriste", "vigipirate",
        "OPEX", "déploiement militaire", "OTAN",
        "cyberattaque", "espionnage",
    ],
}

# Tous les mots-clés à plat avec leur thème
TOUS_MOTS_CLES: dict[str, str] = {}
for theme, mots in MOTS_CLES_PAR_THEME.items():
    for mot in mots:
        TOUS_MOTS_CLES[mot.lower()] = theme

NIVEAUX_PRIORITE = {
    "🔴 Constitutionnel": 1,
    "⚖️ Justice":         2,
    "🌍 Diplomatie":      2,
    "⚡ Social":           3,
    "💰 Budget & Économie": 3,
    "🛡️ Sécurité & Défense": 2,
    "🗳️ Électoral":       4,
}

COULEURS_NIVEAU = {1: "#e8304a", 2: "#f5a623", 3: "#3b6ef0", 4: "#22c99e"}


def detecter_alertes(
    df: pd.DataFrame,
    mots_personnalises: list[str] | None = None,
    heures_max: int = 24,
) -> pd.DataFrame:
    """
    Analyse un DataFrame d'articles et retourne les alertes déclenchées.

    Args:
        df:                  DataFrame d'articles (colonnes: titre, extrait, date)
        mots_personnalises:  Mots-clés supplémentaires définis par l'utilisateur
        heures_max:          Ne considère que les articles des N dernières heures

    Returns:
        DataFrame d'alertes avec : titre, source, theme, mot_cle, priorite, date, url
    """
    if df.empty:
        return pd.DataFrame()

    # Dictionnaire étendu avec mots personnalisés
    mots_actifs = dict(TOUS_MOTS_CLES)
    if mots_personnalises:
        for mot in mots_personnalises:
            if mot.strip():
                mots_actifs[mot.strip().lower()] = "🎯 Personnalisé"

    # Filtrer par fenêtre temporelle
    maintenant = datetime.now(PARIS_TZ)
    limite = maintenant - timedelta(hours=heures_max)

    alertes = []
    for _, row in df.iterrows():
        date_article = row["date"]
        if hasattr(date_article, "tzinfo") and date_article.tzinfo is None:
            date_article = PARIS_TZ.localize(date_article)

        if date_article < limite:
            continue

        texte = f"{row.get('titre', '')} {row.get('extrait', '')}".lower()

        for mot, theme in mots_actifs.items():
            if mot in texte:
                alertes.append({
                    "titre":    row.get("titre", ""),
                    "source":   row.get("source", ""),
                    "url":      row.get("url", ""),
                    "date":     row.get("date"),
                    "theme":    theme,
                    "mot_cle":  mot,
                    "priorite": NIVEAUX_PRIORITE.get(theme, 5),
                    "couleur":  COULEURS_NIVEAU.get(NIVEAUX_PRIORITE.get(theme, 5), "#8892aa"),
                })
                break  # Une alerte par article maximum

    if not alertes:
        return pd.DataFrame()

    df_alertes = pd.DataFrame(alertes)
    df_alertes = df_alertes.sort_values(
        ["priorite", "date"], ascending=[True, False]
    ).reset_index(drop=True)
    return df_alertes


def compter_par_theme(df_alertes: pd.DataFrame) -> dict[str, int]:
    """Retourne le nombre d'alertes par thème."""
    if df_alertes.empty:
        return {}
    return df_alertes.groupby("theme").size().to_dict()


def themes_disponibles() -> list[str]:
    """Retourne la liste de tous les thèmes configurés."""
    return list(MOTS_CLES_PAR_THEME.keys())


def mots_par_theme(theme: str) -> list[str]:
    """Retourne les mots-clés d'un thème donné."""
    return MOTS_CLES_PAR_THEME.get(theme, [])
