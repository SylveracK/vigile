"""
app.py — VIGILE · Intelligence Politique Française
Application Streamlit principale.

Lancement local :  streamlit run app.py
Déploiement     :  Streamlit Cloud (streamlit.io)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz
from groq import Groq
import time

from sources.rss_medias import fetch_flux, sources_disponibles, CATEGORIES
from sources.alertes import (
detecter_alertes,
compter_par_theme,
themes_disponibles,
mots_par_theme,
MOTS_CLES_PAR_THEME,
COULEURS_NIVEAU,
NIVEAUX_PRIORITE,
)

# ── Configuration de la page ─────────────────────────────────────────────────

st.set_page_config(
page_title=“VIGILE — Intelligence Politique”,
page_icon=“🇫🇷”,
layout=“wide”,
initial_sidebar_state=“expanded”,
)

PARIS_TZ = pytz.timezone(“Europe/Paris”)

# ── CSS personnalisé ─────────────────────────────────────────────────────────

st.markdown(”””

<style>
/* Police et fond global */
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@700;800&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace; }

/* Header */
.vigile-header {
    background: linear-gradient(135deg, #0a0c10, #111318);
    border: 1px solid #1e2230;
    border-radius: 10px;
    padding: 20px 28px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.vigile-title {
    font-family: 'Syne', sans-serif;
    font-size: 28px;
    font-weight: 800;
    letter-spacing: .12em;
    color: #e2e6f0;
    margin: 0;
}
.vigile-sub { font-size: 11px; color: #4a5268; letter-spacing: .2em; }

/* Cartes métriques */
.metric-card {
    background: #111318;
    border: 1px solid #1e2230;
    border-radius: 8px;
    padding: 16px;
    text-align: center;
    margin-bottom: 10px;
}
.metric-val {
    font-family: 'Syne', sans-serif;
    font-size: 32px;
    font-weight: 700;
    line-height: 1;
}
.metric-lbl { font-size: 10px; color: #8892aa; letter-spacing: .1em; margin-top: 4px; }

/* Badges d'alerte */
.alerte-critique { background: rgba(232,48,74,.12); border-left: 3px solid #e8304a; padding: 10px 14px; border-radius: 0 6px 6px 0; margin-bottom: 8px; }
.alerte-haute    { background: rgba(245,166,35,.10); border-left: 3px solid #f5a623; padding: 10px 14px; border-radius: 0 6px 6px 0; margin-bottom: 8px; }
.alerte-normale  { background: rgba(59,110,240,.10); border-left: 3px solid #3b6ef0; padding: 10px 14px; border-radius: 0 6px 6px 0; margin-bottom: 8px; }
.alerte-basse    { background: rgba(34,201,158,.08); border-left: 3px solid #22c99e; padding: 10px 14px; border-radius: 0 6px 6px 0; margin-bottom: 8px; }

.alerte-titre  { font-size: 13px; color: #e2e6f0; margin-bottom: 3px; }
.alerte-meta   { font-size: 10px; color: #4a5268; }
.alerte-theme  { font-size: 9px; letter-spacing: .12em; }

/* Articles */
.article-card {
    background: #111318;
    border: 1px solid #1e2230;
    border-radius: 7px;
    padding: 14px;
    margin-bottom: 10px;
    transition: border-color .2s;
}
.article-titre { font-size: 14px; color: #e2e6f0; margin-bottom: 5px; line-height: 1.4; }
.article-extrait { font-size: 11px; color: #8892aa; line-height: 1.6; margin-bottom: 8px; }
.article-meta { font-size: 9px; color: #4a5268; }

/* Tags */
.tag {
    display: inline-block;
    font-size: 8px;
    letter-spacing: .12em;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 3px;
    margin-right: 5px;
}
.tag-national   { background: rgba(59,110,240,.12);  color: #3b6ef0; border: 1px solid rgba(59,110,240,.3); }
.tag-executif   { background: rgba(232,121,249,.10); color: #e879f9; border: 1px solid rgba(232,121,249,.3); }
.tag-economie   { background: rgba(245,158,11,.10);  color: #f59e0b; border: 1px solid rgba(245,158,11,.3); }
.tag-international { background: rgba(34,201,158,.10); color: #22c99e; border: 1px solid rgba(34,201,158,.3); }
.tag-investigation { background: rgba(168,85,247,.10); color: #a855f7; border: 1px solid rgba(168,85,247,.3); }
.tag-general    { background: rgba(74,82,104,.15);   color: #8892aa; border: 1px solid rgba(74,82,104,.3); }

/* Ticker */
.ticker-wrap {
    background: rgba(232,48,74,.06);
    border: 1px solid rgba(232,48,74,.15);
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 11px;
    color: #e8304a;
    margin-bottom: 16px;
    overflow: hidden;
}

/* Section titre */
.section-title {
    font-size: 9px;
    letter-spacing: .2em;
    text-transform: uppercase;
    color: #4a5268;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid #1e2230;
}

/* Analyse IA */
.ia-block {
    background: linear-gradient(135deg, rgba(59,110,240,.05), rgba(34,201,158,.03));
    border: 1px solid rgba(59,110,240,.2);
    border-radius: 8px;
    padding: 16px;
    margin-top: 12px;
}
.ia-label { font-size: 8px; letter-spacing: .2em; text-transform: uppercase; color: #3b6ef0; margin-bottom: 8px; }
.ia-text { font-size: 13px; line-height: 1.8; color: #8892aa; font-style: italic; }

div[data-testid="stSidebar"] { background: #0d0f14; border-right: 1px solid #1e2230; }
</style>

“””, unsafe_allow_html=True)

# ── Helpers ──────────────────────────────────────────────────────────────────

def tag_html(categorie: str) -> str:
mapping = {
“National”: “tag-national”, “Exécutif”: “tag-executif”,
“Économie”: “tag-economie”, “International”: “tag-international”,
“Investigation”: “tag-investigation”,
}
cls = mapping.get(categorie, “tag-general”)
return f’<span class="tag {cls}">{categorie}</span>’

def alerte_classe(priorite: int) -> str:
return {1: “alerte-critique”, 2: “alerte-haute”, 3: “alerte-normale”, 4: “alerte-basse”}.get(priorite, “alerte-normale”)

def age_article(date) -> str:
“”“Retourne une durée lisible depuis la publication.”””
try:
maintenant = datetime.now(PARIS_TZ)
if hasattr(date, “tzinfo”) and date.tzinfo is None:
date = PARIS_TZ.localize(date)
delta = maintenant - date
minutes = int(delta.total_seconds() / 60)
if minutes < 1:    return “À l’instant”
if minutes < 60:   return f”Il y a {minutes} min”
heures = minutes // 60
if heures < 24:    return f”Il y a {heures}h”
jours = heures // 24
return f”Il y a {jours}j”
except Exception:
return “”

@st.cache_data(ttl=900)  # Cache 15 minutes
def charger_articles(sources_selectionnees):
“”“Charge et met en cache les articles RSS.”””
return fetch_flux(sources=sources_selectionnees, max_par_source=10)

def appel_ia(prompt: str) -> str:
“”“Appelle Groq (gratuit) pour une analyse IA.”””
try:
api_key = st.secrets.get(“GROQ_API_KEY”, “”)
if not api_key:
return “⚠️ Clé GROQ_API_KEY non configurée dans les secrets Streamlit.”
client = Groq(api_key=api_key)
response = client.chat.completions.create(
model=“llama-3.1-8b-instant”,
messages=[
{
“role”: “system”,
“content”: “Tu es un analyste politique expert en politique française et relations internationales. Analyses concises, précises, sans parti pris. Toujours en français. 3-4 phrases maximum.”
},
{
“role”: “user”,
“content”: prompt
}
],
max_tokens=600,
temperature=0.4,
)
return response.choices[0].message.content
except Exception as e:
return f”Erreur Groq : {e}”

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
st.markdown(”### 🇫🇷 VIGILE”)
st.markdown(’<div style="font-size:9px;color:#4a5268;letter-spacing:.15em">INTELLIGENCE POLITIQUE</div>’, unsafe_allow_html=True)
st.divider()

```
# Heure Paris
now_paris = datetime.now(PARIS_TZ)
st.markdown(f'<div style="font-size:10px;color:#4a5268">🕐 {now_paris.strftime("%H:%M:%S")} · Paris</div>', unsafe_allow_html=True)
st.markdown(f'<div style="font-size:10px;color:#4a5268">📅 {now_paris.strftime("%A %d %B %Y")}</div>', unsafe_allow_html=True)
st.divider()

# Sélection des sources
st.markdown("**Sources actives**")
toutes_sources = sources_disponibles()
sources_choisies = st.multiselect(
    "Médias",
    options=toutes_sources,
    default=["Le Monde", "Le Figaro", "France Info", "RFI", "Les Échos", "Libération", "Elysée", "Gouvernement"],
    label_visibility="collapsed",
)

st.divider()

# Mots-clés personnalisés
st.markdown("**🎯 Mots-clés personnalisés**")
mots_custom_raw = st.text_area(
    "Un mot-clé par ligne",
    placeholder="49.3\nLe Pen\ngrève\nbudget\n...",
    height=120,
    label_visibility="collapsed",
)
mots_custom = [m.strip() for m in mots_custom_raw.split("\n") if m.strip()]

st.divider()

# Fenêtre temporelle alertes
st.markdown("**⏱ Fenêtre d'alertes**")
heures_alerte = st.slider("Dernières N heures", 1, 72, 24, label_visibility="collapsed")

st.divider()

# Bouton de rafraîchissement
if st.button("🔄 Rafraîchir les données", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.markdown('<div style="font-size:9px;color:#2e3450;margin-top:8px">Mise à jour auto toutes les 15 min</div>', unsafe_allow_html=True)
```

# ── Header principal ─────────────────────────────────────────────────────────

col_logo, col_live = st.columns([3, 1])
with col_logo:
st.markdown(”””
<div class="vigile-header">
<div>
<div class="vigile-title">🇫🇷 VIGILE</div>
<div class="vigile-sub">INTELLIGENCE POLITIQUE FRANÇAISE · TEMPS RÉEL</div>
</div>
</div>
“””, unsafe_allow_html=True)
with col_live:
st.markdown(f”””
<div class="metric-card" style="margin-top:0">
<div style="font-size:9px;color:#22c99e;letter-spacing:.15em">● EN DIRECT</div>
<div style="font-size:11px;color:#4a5268;margin-top:4px">{now_paris.strftime(’%H:%M’)}</div>
<div style="font-size:9px;color:#2e3450">{now_paris.strftime(’%d/%m/%Y’)}</div>
</div>
“””, unsafe_allow_html=True)

# ── Chargement des données ───────────────────────────────────────────────────

with st.spinner(“📡 Collecte des flux RSS en cours…”):
df_articles = charger_articles(tuple(sources_choisies) if sources_choisies else tuple(sources_disponibles()[:8]))

df_alertes = detecter_alertes(df_articles, mots_custom, heures_alerte) if not df_articles.empty else pd.DataFrame()

# ── Métriques globales ───────────────────────────────────────────────────────

nb_articles  = len(df_articles)
nb_alertes   = len(df_alertes)
nb_critiques = len(df_alertes[df_alertes[“priorite”] == 1]) if not df_alertes.empty else 0
nb_sources   = df_articles[“source”].nunique() if not df_articles.empty else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
st.markdown(f’<div class="metric-card"><div class="metric-val" style="color:#3b6ef0">{nb_articles}</div><div class="metric-lbl">Articles collectés</div></div>’, unsafe_allow_html=True)
with c2:
st.markdown(f’<div class="metric-card"><div class="metric-val" style="color:#e8304a">{nb_alertes}</div><div class="metric-lbl">Alertes actives</div></div>’, unsafe_allow_html=True)
with c3:
st.markdown(f’<div class="metric-card"><div class="metric-val" style="color:#f5a623">{nb_critiques}</div><div class="metric-lbl">Alertes critiques</div></div>’, unsafe_allow_html=True)
with c4:
st.markdown(f’<div class="metric-card"><div class="metric-val" style="color:#22c99e">{nb_sources}</div><div class="metric-lbl">Sources actives</div></div>’, unsafe_allow_html=True)

# ── Ticker alertes critiques ──────────────────────────────────────────────────

if not df_alertes.empty:
critiques = df_alertes[df_alertes[“priorite”] <= 2].head(5)
if not critiques.empty:
ticker_items = “ · “.join([f”⚡ {r[‘titre’][:80]}…” for _, r in critiques.iterrows()])
st.markdown(f’<div class="ticker-wrap">🔴 ALERTES · {ticker_items}</div>’, unsafe_allow_html=True)

# ── Onglets principaux ───────────────────────────────────────────────────────

tabs = st.tabs([
“📡 Flux en direct”,
“🚨 Alertes”,
“📊 Statistiques”,
“✦ Analyse IA”,
“⚙️ Mots-clés”,
])

# ════════════════════════════════════════════════════════════════

# ONGLET 1 — FLUX EN DIRECT

# ════════════════════════════════════════════════════════════════

with tabs[0]:
col_flux, col_sidebar = st.columns([2, 1])

```
with col_flux:
    st.markdown('<div class="section-title">Derniers articles — toutes sources</div>', unsafe_allow_html=True)

    # Filtres
    f1, f2, f3 = st.columns(3)
    with f1:
        filtre_cat = st.selectbox("Catégorie", ["Toutes"] + list(set(CATEGORIES.values())), key="fcat")
    with f2:
        filtre_src = st.selectbox("Source", ["Toutes"] + sorted(df_articles["source"].unique().tolist() if not df_articles.empty else []), key="fsrc")
    with f3:
        filtre_recherche = st.text_input("🔍 Recherche", placeholder="mot-clé...", key="frecherche")

    # Appliquer les filtres
    df_affiche = df_articles.copy() if not df_articles.empty else pd.DataFrame()
    if not df_affiche.empty:
        if filtre_cat != "Toutes":
            df_affiche = df_affiche[df_affiche["categorie"] == filtre_cat]
        if filtre_src != "Toutes":
            df_affiche = df_affiche[df_affiche["source"] == filtre_src]
        if filtre_recherche:
            mask = (
                df_affiche["titre"].str.contains(filtre_recherche, case=False, na=False) |
                df_affiche["extrait"].str.contains(filtre_recherche, case=False, na=False)
            )
            df_affiche = df_affiche[mask]

    if df_affiche.empty:
        st.info("Aucun article trouvé avec ces filtres.")
    else:
        for _, row in df_affiche.head(40).iterrows():
            age = age_article(row["date"])
            tag = tag_html(row["categorie"])
            lien = f'<a href="{row["url"]}" target="_blank" style="color:#4a5268;font-size:9px">↗ Lire l\'article</a>' if row.get("url") else ""
            st.markdown(f"""
            <div class="article-card">
                <div class="article-titre">{row['titre']}</div>
                <div class="article-extrait">{row['extrait']}</div>
                <div class="article-meta">{tag} <span style="color:#4a5268">{row['source']} · {age}</span> &nbsp; {lien}</div>
            </div>
            """, unsafe_allow_html=True)

with col_sidebar:
    st.markdown('<div class="section-title">Top sources</div>', unsafe_allow_html=True)
    if not df_articles.empty:
        src_counts = df_articles["source"].value_counts().head(10)
        fig_src = px.bar(
            src_counts,
            orientation="h",
            color_discrete_sequence=["#3b6ef0"],
            labels={"value": "Articles", "index": "Source"},
        )
        fig_src.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#8892aa", font_size=10,
            margin=dict(l=0, r=0, t=0, b=0), height=280,
            showlegend=False, yaxis=dict(tickfont=dict(size=9)),
        )
        fig_src.update_xaxes(gridcolor="#1e2230", zerolinecolor="#1e2230")
        fig_src.update_yaxes(gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_src, use_container_width=True)

    st.markdown('<div class="section-title" style="margin-top:8px">Répartition thématique</div>', unsafe_allow_html=True)
    if not df_articles.empty:
        cat_counts = df_articles["categorie"].value_counts()
        fig_pie = px.pie(
            values=cat_counts.values,
            names=cat_counts.index,
            color_discrete_sequence=["#3b6ef0", "#e8304a", "#f5a623", "#22c99e", "#a855f7", "#8892aa"],
            hole=0.55,
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font_color="#8892aa", font_size=9,
            margin=dict(l=0, r=0, t=0, b=0), height=220,
            legend=dict(font=dict(size=9)),
            showlegend=True,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent")
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown('<div class="section-title" style="margin-top:8px">Volume par heure</div>', unsafe_allow_html=True)
    if not df_articles.empty:
        df_h = df_articles.copy()
        try:
            df_h["heure"] = pd.to_datetime(df_h["date"], utc=True).dt.floor("h")
            heure_counts = df_h.groupby("heure").size().reset_index(name="n")
            fig_h = px.area(
                heure_counts, x="heure", y="n",
                color_discrete_sequence=["#3b6ef0"],
            )
            fig_h.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#8892aa", font_size=9,
                margin=dict(l=0, r=0, t=0, b=0), height=160,
                showlegend=False,
            )
            fig_h.update_xaxes(gridcolor="#1e2230", tickformat="%Hh")
            fig_h.update_yaxes(gridcolor="#1e2230")
            st.plotly_chart(fig_h, use_container_width=True)
        except Exception:
            pass
```

# ════════════════════════════════════════════════════════════════

# ONGLET 2 — ALERTES

# ════════════════════════════════════════════════════════════════

with tabs[1]:
if df_alertes.empty:
st.info(“✅ Aucune alerte déclenchée sur les dernières {} heures.”.format(heures_alerte))
else:
# Résumé par thème
st.markdown(’<div class="section-title">Alertes par thème</div>’, unsafe_allow_html=True)
themes_counts = compter_par_theme(df_alertes)

```
    cols_themes = st.columns(min(len(themes_counts), 4))
    for i, (theme, count) in enumerate(sorted(themes_counts.items(), key=lambda x: NIVEAUX_PRIORITE.get(x[0], 5))):
        with cols_themes[i % len(cols_themes)]:
            couleur = COULEURS_NIVEAU.get(NIVEAUX_PRIORITE.get(theme, 5), "#8892aa")
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size:18px;font-weight:700;color:{couleur}">{count}</div>
                <div style="font-size:10px;color:#8892aa;margin-top:3px">{theme}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Liste des alertes
    col_a1, col_a2 = st.columns([3, 1])
    with col_a1:
        st.markdown('<div class="section-title">Détail des alertes</div>', unsafe_allow_html=True)
        filtre_theme_alerte = st.selectbox(
            "Filtrer par thème",
            ["Tous"] + list(themes_counts.keys()),
            key="falerte_theme",
        )

        df_a_affiche = df_alertes.copy()
        if filtre_theme_alerte != "Tous":
            df_a_affiche = df_a_affiche[df_a_affiche["theme"] == filtre_theme_alerte]

        for _, alerte in df_a_affiche.iterrows():
            cls = alerte_classe(alerte["priorite"])
            age = age_article(alerte["date"])
            lien = f'<a href="{alerte["url"]}" target="_blank" style="color:#4a5268">↗</a>' if alerte.get("url") else ""
            st.markdown(f"""
            <div class="{cls}">
                <div class="alerte-titre">{alerte['titre']} {lien}</div>
                <div class="alerte-meta">
                    <span style="color:{alerte['couleur']}">{alerte['theme']}</span>
                    &nbsp;·&nbsp; Mot-clé : <strong>{alerte['mot_cle']}</strong>
                    &nbsp;·&nbsp; {alerte['source']} &nbsp;·&nbsp; {age}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_a2:
        st.markdown('<div class="section-title">Répartition</div>', unsafe_allow_html=True)
        if not df_alertes.empty:
            prio_labels = {1: "🔴 Critique", 2: "🟠 Haute", 3: "🔵 Normale", 4: "🟢 Basse"}
            prio_counts = df_alertes["priorite"].map(prio_labels).value_counts()
            fig_prio = px.pie(
                values=prio_counts.values,
                names=prio_counts.index,
                color_discrete_sequence=["#e8304a", "#f5a623", "#3b6ef0", "#22c99e"],
                hole=0.5,
            )
            fig_prio.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", font_color="#8892aa", font_size=9,
                margin=dict(l=0, r=0, t=0, b=0), height=220,
            )
            st.plotly_chart(fig_prio, use_container_width=True)
```

# ════════════════════════════════════════════════════════════════

# ONGLET 3 — STATISTIQUES

# ════════════════════════════════════════════════════════════════

with tabs[2]:
if df_articles.empty:
st.info(“Aucun article chargé.”)
else:
st.markdown(’<div class="section-title">Analyse du corpus</div>’, unsafe_allow_html=True)

```
    c_s1, c_s2 = st.columns(2)

    with c_s1:
        # Articles par source — barres
        src_c = df_articles["source"].value_counts().reset_index()
        src_c.columns = ["Source", "Articles"]
        fig_s = px.bar(
            src_c, x="Articles", y="Source", orientation="h",
            color="Articles",
            color_continuous_scale=[[0, "#1e2230"], [1, "#3b6ef0"]],
            title="Articles par source",
        )
        fig_s.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#8892aa", title_font_color="#8892aa", title_font_size=11,
            margin=dict(l=0, r=0, t=30, b=0), height=320,
            showlegend=False, coloraxis_showscale=False,
            yaxis=dict(tickfont=dict(size=9)),
        )
        fig_s.update_xaxes(gridcolor="#1e2230")
        fig_s.update_yaxes(gridcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_s, use_container_width=True)

    with c_s2:
        # Mots-clés alertes déclenchés
        if not df_alertes.empty:
            mk_counts = df_alertes["mot_cle"].value_counts().head(15).reset_index()
            mk_counts.columns = ["Mot-clé", "Occurrences"]
            fig_mk = px.bar(
                mk_counts, x="Occurrences", y="Mot-clé", orientation="h",
                color="Occurrences",
                color_continuous_scale=[[0, "#1e2230"], [1, "#e8304a"]],
                title="Mots-clés les plus détectés",
            )
            fig_mk.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#8892aa", title_font_color="#8892aa", title_font_size=11,
                margin=dict(l=0, r=0, t=30, b=0), height=320,
                showlegend=False, coloraxis_showscale=False,
                yaxis=dict(tickfont=dict(size=9)),
            )
            fig_mk.update_xaxes(gridcolor="#1e2230")
            fig_mk.update_yaxes(gridcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_mk, use_container_width=True)

    # Timeline des publications
    st.markdown('<div class="section-title" style="margin-top:8px">Timeline des publications (dernières 48h)</div>', unsafe_allow_html=True)
    try:
        df_time = df_articles.copy()
        df_time["heure"] = pd.to_datetime(df_time["date"], utc=True).dt.floor("H")
        df_time_grp = df_time.groupby(["heure", "categorie"]).size().reset_index(name="n")
        fig_t = px.bar(
            df_time_grp, x="heure", y="n", color="categorie",
            color_discrete_map={
                "National": "#3b6ef0", "Exécutif": "#e879f9",
                "Économie": "#f59e0b", "International": "#22c99e",
                "Investigation": "#a855f7", "Général": "#4a5268",
            },
        )
        fig_t.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#8892aa", margin=dict(l=0, r=0, t=0, b=0), height=220,
            legend=dict(font=dict(size=9)),
        )
        fig_t.update_xaxes(gridcolor="#1e2230", tickformat="%Hh %d/%m")
        fig_t.update_yaxes(gridcolor="#1e2230")
        st.plotly_chart(fig_t, use_container_width=True)
    except Exception:
        pass
```

# ════════════════════════════════════════════════════════════════

# ONGLET 4 — ANALYSE IA

# ════════════════════════════════════════════════════════════════

with tabs[3]:
st.markdown(’<div class="section-title">Analyses IA — propulsées par Claude (Anthropic)</div>’, unsafe_allow_html=True)

```
# Extraire les titres récents pour contexte
titres_recents = ""
if not df_articles.empty:
    titres_recents = "\n".join(
        f"- [{r['source']}] {r['titre']}" 
        for _, r in df_articles.head(20).iterrows()
    )

c_ia1, c_ia2 = st.columns(2)

with c_ia1:
    st.markdown("**☀️ Briefing du jour**")
    if st.button("Générer le briefing matinal", key="briefing_btn", use_container_width=True):
        with st.spinner("Analyse en cours..."):
            prompt = f"""Génère un briefing politique matinal complet sur la France basé sur ces actualités récentes :
```

{titres_recents}

Structure le briefing en 4 parties :

1. Urgences du jour (1-2 points)
1. Situation parlementaire
1. Point diplomatique
1. Économie & société

Sois factuel, concis, analytique. En français.”””
analyse = appel_ia(prompt)
st.markdown(f’<div class="ia-block"><div class="ia-label">✦ Briefing VIGILE</div><div class="ia-text">{analyse}</div></div>’, unsafe_allow_html=True)

```
    st.markdown("---")

    st.markdown("**📊 Analyse thématique**")
    theme_ia = st.selectbox(
        "Choisir le thème",
        ["Budget & Finances", "Diplomatie", "Défense", "Social", "Justice", "Europe", "Présidentielle 2027"],
        key="theme_ia_select",
    )
    if st.button("Analyser ce thème", key="theme_btn", use_container_width=True):
        with st.spinner("Analyse en cours..."):
            articles_theme = "\n".join(
                f"- {r['titre']}"
                for _, r in df_articles.head(30).iterrows()
                if theme_ia.lower().split(" ")[0].lower() in r["titre"].lower() or
                   theme_ia.lower().split(" ")[0].lower() in r["extrait"].lower()
            ) or "Pas d'articles spécifiques trouvés, analyse générale."
            prompt = f"Analyse la situation française sur le thème '{theme_ia}' en 2025, en tenant compte de ces actualités récentes : {articles_theme}. 4 phrases maximum, style analytique."
            analyse = appel_ia(prompt)
        st.markdown(f'<div class="ia-block"><div class="ia-label">✦ Analyse {theme_ia}</div><div class="ia-text">{analyse}</div></div>', unsafe_allow_html=True)

with c_ia2:
    st.markdown("**🚨 Synthèse des alertes**")
    if st.button("Analyser les alertes actives", key="alertes_btn", use_container_width=True):
        with st.spinner("Analyse en cours..."):
            if df_alertes.empty:
                st.info("Aucune alerte à analyser.")
            else:
                alertes_txt = "\n".join(
                    f"- [{a['theme']}] {a['titre']} (mot-clé: {a['mot_cle']})"
                    for _, a in df_alertes.head(15).iterrows()
                )
                prompt = f"""Analyse ces alertes politiques françaises détectées :
```

{alertes_txt}

Quels sont les signaux les plus importants ? Y a-t-il des tendances ou connexions entre ces événements ? 4 phrases maximum.”””
analyse = appel_ia(prompt)
st.markdown(f’<div class="ia-block"><div class="ia-label">✦ Synthèse des alertes</div><div class="ia-text">{analyse}</div></div>’, unsafe_allow_html=True)

```
    st.markdown("---")

    st.markdown("**💬 Question libre**")
    question_libre = st.text_area(
        "Posez votre question",
        placeholder="Ex : Quels sont les risques politiques majeurs cette semaine en France ?",
        height=100,
        key="question_libre",
    )
    if st.button("Analyser", key="question_btn", use_container_width=True):
        if question_libre:
            with st.spinner("Analyse en cours..."):
                prompt = f"""Contexte : actualités françaises du jour :
```

{titres_recents}

Question : {question_libre}

Réponds en 4 phrases maximum, en français, avec une analyse factuelle et nuancée.”””
analyse = appel_ia(prompt)
st.markdown(f’<div class="ia-block"><div class="ia-label">✦ Réponse VIGILE</div><div class="ia-text">{analyse}</div></div>’, unsafe_allow_html=True)
else:
st.warning(“Entrez une question.”)

# ════════════════════════════════════════════════════════════════

# ONGLET 5 — MOTS-CLÉS

# ════════════════════════════════════════════════════════════════

with tabs[4]:
st.markdown(’<div class="section-title">Configuration du système d'alertes</div>’, unsafe_allow_html=True)

```
col_mk1, col_mk2 = st.columns(2)

with col_mk1:
    st.markdown("**Mots-clés par thème (intégrés)**")
    for theme, mots in MOTS_CLES_PAR_THEME.items():
        couleur = COULEURS_NIVEAU.get(NIVEAUX_PRIORITE.get(theme, 5), "#8892aa")
        with st.expander(f"{theme}"):
            st.markdown(
                " &nbsp; ".join(
                    f'<span style="background:rgba(255,255,255,.05);border:1px solid #2e3450;border-radius:3px;padding:2px 8px;font-size:10px;color:#8892aa">{m}</span>'
                    for m in mots
                ),
                unsafe_allow_html=True,
            )

with col_mk2:
    st.markdown("**Mots-clés personnalisés actifs**")
    if mots_custom:
        for mot in mots_custom:
            st.markdown(
                f'<span style="background:rgba(59,110,240,.1);border:1px solid rgba(59,110,240,.3);border-radius:3px;padding:3px 10px;font-size:11px;color:#3b6ef0;display:inline-block;margin:3px">{mot}</span>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown('<div style="font-size:11px;color:#4a5268">Aucun mot-clé personnalisé. Ajoutez-en dans la sidebar.</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Statistiques de détection**")
    if not df_alertes.empty:
        st.markdown(f'<div style="font-size:12px;color:#8892aa">Total alertes déclenchées : <strong style="color:#e2e6f0">{len(df_alertes)}</strong></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:12px;color:#8892aa">Alertes critiques (priorité 1) : <strong style="color:#e8304a">{len(df_alertes[df_alertes["priorite"]==1])}</strong></div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:12px;color:#8892aa">Mots-clés uniques détectés : <strong style="color:#e2e6f0">{df_alertes["mot_cle"].nunique()}</strong></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:11px;color:#4a5268">Aucune détection sur la période sélectionnée.</div>', unsafe_allow_html=True)
```

# ── Footer ───────────────────────────────────────────────────────────────────

st.divider()
st.markdown(
‘<div style="text-align:center;font-size:9px;color:#2e3450;letter-spacing:.15em">’
‘VIGILE · Intelligence Politique Française · ’
f’Données collectées à {now_paris.strftime(”%H:%M”)} · ’
‘Sources : flux RSS publics · API Anthropic Claude’
‘</div>’,
unsafe_allow_html=True,
)
