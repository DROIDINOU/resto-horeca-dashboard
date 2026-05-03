import json
import pandas as pd
import streamlit as st
from pathlib import Path


st.set_page_config(page_title="Détection Constitution de Sociétés HORECA", layout="wide")
BASE_DIR = Path(__file__).resolve().parent
JSON_PATH = BASE_DIR / "public" / "all_leads.json"

@st.cache_data
def load_data():
    with open(JSON_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)

df = load_data()
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
    text-align: center;
">
    <h1 style="margin:0;">🍽️ Détection des sociétés HORECA</h1>
    <p style="margin:100; font-size:16px; opacity:0.8;">
        Analyse sur base des annexes du Moniteur Belge.<br> Confirmation ultérieure via la BCE.
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
- Ce décalage crée une fenêtre d’anticipation  

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
confirmed_df = df[df["bce_status"] == "confirmed_horeca"]
avg_days = confirmed_df["days_to_confirmation"].dropna().mean()

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total", len(df))
col2.metric("BCE confirmés", len(confirmed_df))
col3.metric("BCE pending", len(df[df["bce_status"].str.contains("pending", na=False)]))
col4.metric("BCE rejetés", len(df[df["bce_status"] == "not_horeca"]))
col5.metric(
    "Délai moyen",
    "-" if pd.isna(avg_days) else f"{avg_days:.1f} j"
)
view = st.radio(
    "Vue rapide",
    ["Confirmés BCE", "Pending BCE", "Rejetés BCE", "Tous"],
    horizontal=True
)

if view == "Confirmés BCE":
    df = df[df["bce_status"] == "confirmed_horeca"]
elif view == "Pending BCE":
    df = df[df["bce_status"].str.contains("pending", na=False)]
elif view == "Rejetés BCE":
    df = df[df["bce_status"] == "not_horeca"]

filtered = df.copy()

st.subheader("Résultats")

for _, row in filtered.iterrows():

    title = f"{row.get('name')} — {row.get('vat')} — {row.get('bce_status')}"

    with st.expander(title):
        c1, c2 = st.columns([1, 2])

        with c1:
            st.write("**Nom :**", row.get("name"))
            st.write("**TVA :**", row.get("vat"))
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

        with c2:
            objet = row.get("objet_social", "")
            if objet:
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
                        {objet}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.info("Objet social non disponible.")

