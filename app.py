import streamlit as st
import pandas as pd
import numpy as np
import os
import sys

st.set_page_config(page_title="Simulateur Kyste Hydatique", layout="wide", page_icon="🩺")

st.title("🩺 Simulateur Clinique du Risque de Kyste Hydatique")
st.markdown("**Évaluation probabiliste basée sur les données épidémiologiques**")

# ==================== FONCTION DE NETTOYAGE ====================
def clean_percentage(val):
    if pd.isna(val):
        return 0.0
    val_str = str(val).strip()
    if '%' in val_str:
        try:
            return float(val_str.replace('%', '').strip()) / 100.0
        except ValueError:
            return 0.0
    else:
        try:
            return float(val_str)
        except ValueError:
            return 0.0

# ==================== CHARGEMENT DU FICHIER EXCEL EMBARQUÉ ====================
@st.cache_data
def load_data():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    excel_path = os.path.join(base_path, "Kyste.xlsx")
    if not os.path.exists(excel_path):
        st.error(f"⛔ Fichier Excel introuvable : `{excel_path}`\nVeuillez le placer dans le même dossier que `app.py`.")
        st.stop()
    
    excel_file = pd.ExcelFile(excel_path)
    sheet_names = excel_file.sheet_names
    
    dict_facteurs = {}
    for sheet in sheet_names:
        df = pd.read_excel(excel_path, sheet_name=sheet)
        if df.shape[1] < 2:
            continue
        col_categorie = df.columns[0]
        col_pourcentage = df.columns[1]
        
        df['prob_clean'] = df[col_pourcentage].apply(clean_percentage)
        somme_prob = df['prob_clean'].sum()
        if somme_prob > 0:
            df['prob_norm'] = df['prob_clean'] / somme_prob
        else:
            df['prob_norm'] = 1.0 / len(df)
            
        dict_facteurs[sheet] = pd.Series(df['prob_norm'].values, index=df[col_categorie].astype(str)).to_dict()
    return dict_facteurs

dict_facteurs = load_data()

# Exclure la méthode de diagnostic des facteurs prédictifs de profil
facteurs_profil = [f for f in dict_facteurs.keys() if f != "Méthode de diagnostic"]

# Initialisation des valeurs dans la session
if 'sim_values' not in st.session_state:
    st.session_state.sim_values = {}
    for f in facteurs_profil:
        st.session_state.sim_values[f] = list(dict_facteurs[f].keys())[0]

# ==================== INTERFACE ====================
col1, col2 = st.columns([1, 1.2])

with col1:
    st.header("👤 Profil du Patient Virtuel")
    selected_profile = {}
    for facteur in facteurs_profil:
        options = list(dict_facteurs[facteur].keys())
        current_val = st.session_state.sim_values.get(facteur)
        default_idx = options.index(current_val) if current_val in options else 0
        selected_profile[facteur] = st.selectbox(
            f"Facteur : {facteur}", 
            options, 
            index=default_idx, 
            key=f"select_{facteur}"
        )
    st.markdown("---")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🎲 Introduire Valeurs Aléatoires", type="primary", use_container_width=True):
            for facteur in facteurs_profil:
                options = list(dict_facteurs[facteur].keys())
                st.session_state.sim_values[facteur] = np.random.choice(options)
            st.rerun()
    with col_btn2:
        if st.button("🔄 Réinitialiser", type="secondary", use_container_width=True):
            for facteur in facteurs_profil:
                st.session_state.sim_values[facteur] = list(dict_facteurs[facteur].keys())[0]
            st.rerun()

with col2:
    st.header("📊 Estimation de l'Exposition")
    scores = []
    details_calcul = []
    for facteur, choix in selected_profile.items():
        p_choix = dict_facteurs[facteur][choix]
        scores.append(p_choix)
        details_calcul.append({"Facteur": facteur, "Valeur choisie": choix, "Poids statistique": f"{p_choix*100:.1f} %"})
        
    produit_prob = np.prod(scores)
    max_possible = np.prod([max(dict_facteurs[f].values()) for f in facteurs_profil])
    probabilite_finale = (produit_prob / max_possible) if max_possible > 0 else 0.0
    probabilite_finale = float(max(0.0, min(1.0, probabilite_finale)))  # Clamp entre 0 et 1
    
    if probabilite_finale > 0.7:
        st.error(f"**Indice de Risque Combiné Élevé**", icon="🚨")
    elif probabilite_finale > 0.3:
        st.warning(f"**Indice de Risque Combiné Modéré**", icon="⚠️")
    else:
        st.success(f"**Indice de Risque Combiné Faible**", icon="✅")
        
    st.metric(label="**Probabilité d'exposition relative**", value=f"{probabilite_finale * 100:.1f} %")
    st.progress(probabilite_finale)
    st.caption("ℹ️ *Cette probabilité représente le niveau d'exposition du profil simulé par rapport au profil maximal à risque identifié dans la base de données.*")
    st.markdown("### 📝 Poids de chaque facteur sélectionné :")
    st.dataframe(pd.DataFrame(details_calcul), use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666; margin-top: 1rem;'><strong>Powered by NewTech & Bounechada</strong></div>", unsafe_allow_html=True)