import json
import pandas as pd
import streamlit as st
from pathlib import Path
import html
import os
from urllib.parse import quote_plus


st.set_page_config(page_title="Détection Constitution de Sociétés HORECA", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
JSON_PATH = BASE_DIR / "public" / "all_leads.json"


def get_file_mtime(path):
    return Path(path).stat().st_mtime


@st.cache_data
def load_data(path, mtime):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


def display_value(value):
    if pd.isna(value) or str(value).lower() == "nan" or str(value).strip() == "":
        return "Non disponible"
    return value


mtime = get_file_mtime(JSON_PATH)
df = load_data(JSON_PATH, mtime)

df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce")
df["moniteur_run_date"] = pd.to_datetime(df.get("moniteur_run_date"), errors="coerce")
df["bce_confirmed_at"] = pd.to_datetime(df.get("bce_confirmed_at"), errors="coerce")
df["days_to_confirmation"] = pd.to_numeric(df.get("days_to_confirmation"), errors="coerce")
df = df.dropna(subset=["publication_date"])

available_dates = sorted(df["publication_date"].dt.date.unique(), reverse=True)

st.markdown("""
<div style="
    padding:20px;
    border-radius:10px;
    background: linear-gradient(90deg, #1f2937, #111827);
    color:white;
    text-align:center;
">
    <h1 style="margin:0;">🍽️ Détection des sociétés HORECA</h1>
    <p style="margin:10px 0 0 0; font-size:16px; opacity:0.8;">
        Analyse sur base des annexes du Moniteur Belge<br>
        Contrôle ultérieur via la BCE
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.expander("ℹ️ Comprendre le classement des leads", expanded=False):
    st.markdown("""
| Classement | Signification |
|---|---|
| **HORECA fort — objet social** | L'objet social contient une phrase claire d'activité HORECA : restaurant, café, snack, catering, etc. |
| **HORECA probable — début objet social** | Plusieurs mots HORECA sont détectés au début de l'objet social, mais sans phrase principale parfaitement claire. |
| **Activité mixte — à vérifier** | HORECA est présent, mais mélangé avec d'autres activités. À vérifier manuellement. |
| **HORECA fort — nom** | Le nom de la société contient plusieurs signaux HORECA. |
| **Non prioritaire** | Pas de signal HORECA fort ou activité principale non HORECA. |
    """)

with st.expander("ℹ️ Comprendre l’intérêt de ces leads", expanded=False):
    st.markdown("""
### Une détection en amont de la BCE

Les sociétés présentées ici sont identifiées à partir des publications du **Moniteur belge**, qui constitue la source officielle lors de la constitution d’une entreprise.

Ces informations apparaissent généralement **avant leur mise à jour dans la Banque-Carrefour des Entreprises (BCE)**.

---

### Un décalage exploitable

Dans la pratique :

- La constitution est publiée au Moniteur belge
- La mise à jour dans la BCE intervient avec un certain délai
- **Ce décalage crée une fenêtre d’anticipation**
---

### Intérêt opérationnel

Cette avance permet :

- d’identifier rapidement les nouvelles sociétés actives dans le secteur HORECA
- d’initier une prise de contact dès le lancement de l’activité
- de se positionner avant l’apparition dans les bases de données classiques

---

### Indicateur de délai

Le champ *« délai de confirmation »* correspond au nombre de jours entre :

- la détection via le Moniteur belge
- la confirmation de l’activité dans la BCE

Ce délai reflète concrètement l’avance disponible pour la prospection.
""")

selected_date = st.selectbox(
    "Date de publication",
    available_dates,
    index=0
)

df = df[df["publication_date"].dt.date == selected_date]
df["has_vat"] = df["vat"].notna() & (df["vat"].astype(str).str.lower() != "nan")
confirmed_df = df[df["bce_status"] == "confirmed_horeca"]
avg_days = confirmed_df["days_to_confirmation"].dropna().mean()

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total", len(df))

col2.metric(
    "BCE confirmés",
    len(df[df["bce_status"] == "confirmed_horeca"])
)

col3.metric(
    "Leads Moniteur",
    len(df[df["has_vat"] & df["bce_status"].str.contains("pending", na=False)])
)

to_validate_mask = (
    (~df["has_vat"])
    & (df["bce_status"].astype(str).str.contains("pending", na=False))
)

displayable_mask = ~(
    df["name"].isna()
    & ~df["has_vat"]
    & df["company_number"].isna()
)

col4.metric(
    "À valider",
    len(df[to_validate_mask])
)

col5.metric(
    "BCE rejetés",
    len(df[df["bce_status"] == "not_horeca"])
)

col6.metric(
    "Délai moyen",
    "-" if pd.isna(avg_days) else f"{avg_days:.1f} j"
)

view = st.radio(
    "Vue rapide",
    ["Confirmés BCE", "Leads Moniteur", "À valider", "Rejetés BCE"],
    horizontal=True
)

if view == "Confirmés BCE":
    df = df[df["bce_status"] == "confirmed_horeca"]

elif view == "Leads Moniteur":
    df = df[df["has_vat"] & df["bce_status"].str.contains("pending", na=False)]
    # TRI IMPORTANT
    df["horeca_score"] = pd.to_numeric(df["horeca_score"], errors="coerce").fillna(0)

    df = df.sort_values(
        by=["horeca_score"],
        ascending=False
    )

elif view == "À valider":
    count = len(df[to_validate_mask])

    if count == 0:
        st.info("Aucun lead à valider.")
    else:
        st.info(f"{count} leads en attente de validation (TVA manquante).")

    st.stop()

elif view == "Rejetés BCE":
    df = df[df["bce_status"] == "not_horeca"]

filtered = df.copy()

st.subheader("Résultats")

for _, row in filtered.iterrows():

    title = f"{row.get('name')} — {row.get('vat')} — {row.get('bce_status')}"

    with st.expander(title):
        c1, c2 = st.columns([1, 2])

        with c1:
            st.write("**Nom :**", display_value(row.get("name")))
            st.write("**TVA :**", display_value(row.get("vat")))

            address = row.get("bce_registered_office_address")
            has_address = not pd.isna(address) and str(address).lower() != "nan" and str(address).strip() != ""

            st.write("**Adresse du siège :**", display_value(address))

            if has_address and row.get("has_vat"):
                query = quote_plus(str(address))

                st.markdown(
                    f"""
                     [Google Maps](https://www.google.com/maps/search/?api=1&query={query})  
                     [OpenStreetMap](https://www.openstreetmap.org/search?query={query})
                    """
                )
            st.write("**Classement :**", row.get("horeca_status_label", row.get("horeca_status")))
            st.write("**Catégorie :**", row.get("horeca_category"))

            bce_url = row.get("bce_enterprise_url")
            if bce_url:
                st.markdown(f"[🔗 Voir sur la BCE]({bce_url})")

            st.write("**Statut Technique Moniteur :**", row.get("horeca_status"))

            status = row.get("bce_status")

            if status == "confirmed_horeca":
                st.success("BCE : HORECA confirmé")
            elif status == "not_horeca":
                st.error("BCE : non horeca")
            elif not row.get("has_vat"):
                st.info("⏳ En attente de validation (TVA manquante)")
            elif status:
                st.warning(f"BCE : {status}")
            else:
                st.info("BCE : non vérifié")

            days = row.get("days_to_confirmation")

            if status == "confirmed_horeca" and pd.notna(days):
                st.write("**Délai confirmation :**", f"{int(days)} jour(s)")
            elif status == "confirmed_horeca":
                st.write("**Délai confirmation :**", "Confirmé, délai inconnu")
            else:
                st.write("**Délai confirmation :**", "Non confirmé")

            run_date = row.get("moniteur_run_date")
            confirmed_at = row.get("bce_confirmed_at")

            st.write(
                "**Run Moniteur :**",
                "-" if pd.isna(run_date) else run_date.date().isoformat()
            )

            st.write(
                "**Confirmation BCE :**",
                "-" if pd.isna(confirmed_at) else confirmed_at.date().isoformat()
            )

            st.write("**Codes NACE :**", row.get("bce_nace_codes"))

            st.button(
                "Analyser ce lead avec IA — bientôt disponible",
                key=f"ai_{row.get('file')}",
                disabled=True
            )

        with c2:
            objet = row.get("objet_social", "")

            if objet:
                objet_safe = "..." + html.escape(str(objet).strip()) + "..."
                st.write("**Objet social :**")
                st.markdown(
                    f"""
                    <div style="
                        border: 2px solid #3b82f6;
                        border-radius: 8px;
                        padding: 12px;
                        background-color: #f9fafb;
                        font-size: 14px;
                        line-height: 1.5;
                        white-space: pre-wrap;
                    ">
                        {objet_safe}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.info("Objet social non disponible.")