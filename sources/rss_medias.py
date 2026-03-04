"""
sources/rss_medias.py
Collecte les flux RSS des principaux médias français.
Aucune clé API requise — tout est public.
"""

import feedparser
import pandas as pd
from datetime import datetime
from dateutil import parser as dateparser
import pytz

# ── Catalogue des flux RSS ──────────────────────────────────────────────────

FLUX_RSS = {
    # Généralistes nationaux
    "Le Monde":           "https://www.lemonde.fr/rss/une.xml",
    "Le Monde Politique": "https://www.lemonde.fr/politique/rss_full.xml",
    "Le Figaro":          "https://www.lefigaro.fr/rss/figaro_politique.xml",
    "France Info":        "https://www.francetvinfo.fr/politique.rss",
    "RFI":                "https://www.rfi.fr/fr/podcasts/politique-internationale/rss",
    "Libération":         "https://www.liberation.fr/arc/outboundfeeds/rss-all/",
    "L'Express":          "https://www.lexpress.fr/rss/politique.xml",
    "Le Point":           "https://www.lepoint.fr/politique/rss.xml",
    # Économie & société
    "Les Échos":          "https://www.lesechos.fr/rss/rss_une.xml",
    "La Tribune":         "https://www.latribune.fr/rss/une.xml",
    # Médias alternatifs
    "Mediapart":          "https://www.mediapart.fr/articles/feed",
    # International sur France
    "RFI Monde":          "https://www.rfi.fr/fr/rss",
    # Officiel
    "Elysée":             "https://www.elysee.fr/rss/declarations.rss",
    "Gouvernement":       "https://www.gouvernement.fr/rss/actualites.xml",
}

CATEGORIES = {
    "Le Monde":           "National",
    "Le Monde Politique": "National",
    "Le Figaro":          "National",
    "France Info":        "National",
    "RFI":                "International",
    "Libération":         "National",
    "L'Express":          "National",
    "Le Point":           "National",
    "Les Échos":          "Économie",
    "La Tribune":         "Économie",
    "Mediapart":          "Investigation",
    "RFI Monde":          "International",
    "Elysée":             "Exécutif",
    "Gouvernement":       "Exécutif",
}

PARIS_TZ = pytz.timezone("Europe/Paris")


def _parse_date(entry) -> datetime:
    """Extrait et normalise la date d'une entrée RSS."""
    for attr in ("published", "updated", "created"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                dt = dateparser.parse(raw)
                if dt and dt.tzinfo is None:
                    dt = pytz.utc.localize(dt)
                return dt.astimezone(PARIS_TZ)
            except Exception:
                continue
    return datetime.now(PARIS_TZ)


def _clean_text(text: str, max_len: int = 280) -> str:
    """Nettoie et tronque un texte HTML brut."""
    import re
    text = re.sub(r"<[^>]+>", "", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len] + "…" if len(text) > max_len else text


def fetch_flux(sources: list[str] | None = None, max_par_source: int = 8) -> pd.DataFrame:
    """
    Récupère les articles des flux RSS sélectionnés.

    Args:
        sources:         Liste de noms de médias à interroger (None = tous)
        max_par_source:  Nombre maximum d'articles par source

    Returns:
        DataFrame avec colonnes : titre, extrait, source, categorie, url, date
    """
    cibles = sources if sources else list(FLUX_RSS.keys())
    articles = []

    for nom in cibles:
        url = FLUX_RSS.get(nom)
        if not url:
            continue
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_par_source]:
                articles.append({
                    "titre":     _clean_text(entry.get("title", "Sans titre"), 120),
                    "extrait":   _clean_text(
                        entry.get("summary", entry.get("description", "")), 280
                    ),
                    "source":    nom,
                    "categorie": CATEGORIES.get(nom, "Général"),
                    "url":       entry.get("link", ""),
                    "date":      _parse_date(entry),
                })
        except Exception as e:
            articles.append({
                "titre":     f"[Indisponible] {nom}",
                "extrait":   f"Flux temporairement inaccessible : {e}",
                "source":    nom,
                "categorie": CATEGORIES.get(nom, "Général"),
                "url":       url,
                "date":      datetime.now(PARIS_TZ),
            })

    if not articles:
        return pd.DataFrame(
            columns=["titre", "extrait", "source", "categorie", "url", "date"]
        )

    df = pd.DataFrame(articles)
    df = df.sort_values("date", ascending=False).reset_index(drop=True)
    return df


def sources_disponibles() -> list[str]:
    """Retourne la liste de toutes les sources configurées."""
    return list(FLUX_RSS.keys())
