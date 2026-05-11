import json
import pandas as pd
import streamlit as st
from pathlib import Path
import folium
from streamlit_folium import st_folium

BASE_DIR = Path(__file__).resolve().parent
JSON_PATH = BASE_DIR / "public" / "all_leads_geocoded.json"
REPORTS_DIR = BASE_DIR / "exports"

FORM_ENDPOINT = "https://formspree.io/f/TON_ID"

st.set_page_config(
    page_title="Détection précoce de nouvelles sociétés",
    layout="wide"
)

def get_file_mtime(path):
    return Path(path).stat().st_mtime


@st.cache_data
def load_data(path, mtime):
    with open(path, encoding="utf-8") as f:
        return pd.DataFrame(json.load(f))


def score(value):
    value = pd.to_numeric(value, errors="coerce")
    return 0 if pd.isna(value) else value


mtime = get_file_mtime(JSON_PATH)
df = load_data(JSON_PATH, mtime)

st.markdown("""
<div style="
    padding:22px;
    border-radius:12px;
    background: linear-gradient(90deg, #1f2937, #111827);
    color:white;
    text-align:center;
">
    <h1 style="margin:0;">📊 Détection précoce de nouvelles sociétés</h1>
    <p style="margin:10px 0 0 0; font-size:16px; opacity:0.85;">
        Analyse automatique des annexes du Moniteur belge<br>
        Classification des activités avant attribution BCE / NACE
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

map_df = df.dropna(subset=["lat", "lng"]).copy()

m = folium.Map(
    location=[50.85, 4.35],
    zoom_start=8,
    tiles="OpenStreetMap"
)

for _, row in map_df.iterrows():
    horeca_score = score(row.get("horeca_score"))
    pharmacy_score = score(row.get("pharmacy_score"))

    if pharmacy_score > 0:
        color = "green"
        activity = "Pharmacie"
    elif horeca_score > 0:
        color = "orange"
        activity = "HORECA"
    else:
        color = "blue"
        activity = "Autre activité"

    popup = f"""
    <b>{row.get('name', 'Nom inconnu')}</b><br>
    Activité détectée: {activity}<br>
    TVA: {row.get('vat', '-')}<br>
    Adresse: {row.get('bce_registered_office_address', '-')}<br>
    Publication: {row.get('publication_date', '-')}<br>
    """

    folium.Marker(
        location=[row["lat"], row["lng"]],
        popup=popup,
        icon=folium.Icon(color=color)
    ).add_to(m)

st.subheader("Carte des détections")

st.markdown("""
🟢 **Pharmacie** &nbsp;&nbsp;&nbsp; 🟠 **HORECA** &nbsp;&nbsp;&nbsp; 🔵 **Autres activités**
""")

st_folium(m, width=1200, height=600)

st.markdown("""
<div style="
    margin: 45px 0;
    border-top: 2px solid rgba(37, 99, 235, 1);
"></div>
""", unsafe_allow_html=True)

st.subheader("📄 Rapports exemples")

pdf_files = sorted(REPORTS_DIR.glob("*.pdf"), reverse=True)

if not pdf_files:
    st.info("Aucun rapport exemple disponible pour le moment.")
else:
    for pdf_path in pdf_files:
        with open(pdf_path, "rb") as f:
            st.download_button(
                label=f"📄 Télécharger {pdf_path.stem.replace('_', ' ')}",
                data=f,
                file_name=pdf_path.name,
                mime="application/pdf",
                key=f"download_{pdf_path.name}"
            )

st.markdown(f"""
<div style="
    border: 2px solid #16a34a;
    background: #f0fdf4;
    border-radius: 12px;
    padding: 22px;
    margin-top: 28px;
    margin-bottom: 20px;
">
    <h3 style="margin:0; color:#166534;">📬 Recevoir les rapports complets par email</h3>

    <p style="margin:8px 0 18px 0; color:#166534;">
        Recevez automatiquement les nouvelles détections issues des annexes du Moniteur belge.
    </p>

    <form action="{FORM_ENDPOINT}" method="POST">

        <label style="font-weight:bold; color:#166534;">Adresse email</label>
        <input
            type="email"
            name="email"
            placeholder="votre@email.com"
            required
            style="
                width:100%;
                padding:12px;
                margin-top:6px;
                margin-bottom:14px;
                border-radius:8px;
                border:1px solid #bbb;
                font-size:16px;
            "
        >

        <label style="font-weight:bold; color:#166534;">Fréquence d’envoi</label>
        <select
            name="frequency"
            style="
                width:100%;
                padding:12px;
                margin-top:6px;
                margin-bottom:14px;
                border-radius:8px;
                border:1px solid #bbb;
                font-size:16px;
            "
        >
            <option>À chaque nouveau rapport</option>
            <option>Quotidien</option>
            <option>Hebdomadaire</option>
            <option>Mensuel</option>
        </select>

        <label style="font-weight:bold; color:#166534;">Types de sociétés suivies</label>

        <div style="margin-top:8px; margin-bottom:16px; color:#166534;">
            <label>
                <input type="checkbox" name="interests" value="Pharmacie" checked>
                Pharmacie
            </label><br>

            <label>
                <input type="checkbox" name="interests" value="HORECA" checked>
                HORECA
            </label><br>

            <label>
                <input type="checkbox" name="interests" value="Autres activités">
                Autres activités
            </label>
        </div>

        <button
            type="submit"
            style="
                width:100%;
                background:#16a34a;
                color:white;
                border:none;
                padding:14px;
                border-radius:10px;
                font-size:16px;
                font-weight:bold;
                cursor:pointer;
            "
        >
            📬 Demander l’accès aux rapports
        </button>

    </form>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="
    margin: 45px 0;
    border-top: 2px solid rgba(37, 99, 235, 1);
"></div>
""", unsafe_allow_html=True)

with st.expander("ℹ️ Comment fonctionne la détection ?", expanded=False):
    st.markdown("""
L’application analyse automatiquement les annexes du Moniteur belge afin d’identifier les nouvelles sociétés dès leur publication.

Les activités sont classées automatiquement, notamment pour les secteurs **HORECA** et **pharmacie**, avant que les informations ne soient pleinement structurées dans les bases classiques comme la BCE ou les codes NACE.

Les rapports complets sont destinés à un usage de veille, de prospection ou d’intelligence économique.
""")