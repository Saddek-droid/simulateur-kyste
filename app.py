@st.cache_data
def load_data():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    excel_path = os.path.join(base_path, "Kyste.xlsx")
    if not os.path.exists(excel_path):
        st.error(f"Fichier Excel introuvable : {excel_path}")
        st.stop()
    
    # ✅ CORRECTION 1 : Forcer le moteur openpyxl (obligatoire sur Linux/Cloud)
    excel_file = pd.ExcelFile(excel_path, engine='openpyxl')
    sheet_names = excel_file.sheet_names
    
    dict_facteurs = {}
    for sheet in sheet_names:
        # ✅ CORRECTION 2 : Utiliser l'objet ExcelFile au lieu de recharger le chemin
        df = pd.read_excel(excel_file, sheet_name=sheet, engine='openpyxl')
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
