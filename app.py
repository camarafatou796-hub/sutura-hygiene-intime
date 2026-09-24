import streamlit as st
import pandas as pd

# Configuration de la page de l'application
st.set_page_config(
    page_title="Sutura Hygiène Intime",
    page_icon="🌸",
    layout="centered"
)

# Chargement des données avec nettoyage rigoureux des prix
@st.cache_data
def charger_donnees():
    df = pd.read_excel("catalogue_global_menstruel.xlsx")
    df['Type_produit'] = df['Type_produit'].fillna("Autre").astype(str)
    df['Categorie'] = df['Categorie'].fillna("Non spécifié").astype(str)
    df['Plateforme'] = df['Plateforme'].fillna("Non spécifié").astype(str)
    df['Taille_Format'] = df['Taille_Format'].fillna("Standard / Non spécifié").astype(str)
    
    # Nettoyage robuste de la colonne Prix pour forcer la conversion en nombre
    if 'Prix_FCFA' in df.columns:
        df['Prix_FCFA'] = df['Prix_FCFA'].astype(str).str.replace(r'[^0-9.]', '', regex=True)
        df['Prix_FCFA'] = pd.to_numeric(df['Prix_FCFA'], errors='coerce')
    
    return df

df = charger_donnees()

# En-tête de l'application
st.title("🌸 Sutura Hygiène Intime")
st.write("Trouvez la protection hygiénique idéale adaptée à vos critères et votre budget.")

st.markdown("---")

# --- FORMULAIRE / QUESTIONNAIRE ---
st.subheader("1. Vos critères de recherche")

types_disponibles = ["Tous"] + sorted(df['Type_produit'].dropna().unique().tolist())
choix_type = st.selectbox("Quel type de produit recherchez-vous ?", types_disponibles)

categories_disponibles = ["Toutes"] + sorted(df['Categorie'].dropna().unique().tolist())
choix_cat = st.selectbox("Préférez-vous du jetable ou du lavable/réutilisable ?", categories_disponibles)

# NOUVEAU : Critère de recherche pour la Taille / Format
tailles_disponibles = ["Tous / Indifférent"] + sorted(df['Taille_Format'].dropna().unique().tolist())
choix_taille = st.selectbox("Quelle taille ou quel format préférez-vous ?", tailles_disponibles)

# Sécurisation des bornes du budget
prix_valides = df['Prix_FCFA'].dropna()
max_prix_catalogue = int(prix_valides.max()) if not prix_valides.empty else 50000
min_prix_catalogue = int(prix_valides.min()) if not prix_valides.empty else 500

choix_budget = st.slider(
    "Quel est votre budget maximum (en FCFA) ?", 
    min_value=min_prix_catalogue, 
    max_value=max_prix_catalogue, 
    value=min_prix_catalogue if min_prix_catalogue > 1800 else 1800, 
    step=100
)

plateformes_disponibles = ["Toutes"] + sorted(df['Plateforme'].dropna().unique().tolist())
choix_plateforme = st.selectbox("Avez-vous une préférence de plateforme ou de magasin ?", plateformes_disponibles)

st.markdown("---")

# --- FILTRAGE ET RECOMMANDATION ---
if st.button("🔍 Trouver mes produits recommandés", type="primary"):
    resultats = df.copy()
    
    if choix_type != "Tous":
        resultats = resultats[resultats['Type_produit'] == choix_type]
        
    if choix_cat != "Toutes":
        resultats = resultats[resultats['Categorie'] == choix_cat]
        
    # Application du filtre Taille / Format si l'utilisateur a fait un choix spécifique
    if choix_taille != "Tous / Indifférent":
        resultats = resultats[resultats['Taille_Format'] == choix_taille]
        
    # Filtrage strict sur le budget nettoyé
    resultats = resultats[resultats['Prix_FCFA'] <= choix_budget]
        
    if choix_plateforme != "Toutes":
        resultats = resultats[resultats['Plateforme'] == choix_plateforme]
        
    st.subheader("✨ Résultats et Recommandations")
    
    if len(resultats) == 0:
        st.warning(f"Aucun produit ne correspond à vos critères (Budget max : {choix_budget} FCFA). Essayez d'élargir vos filtres (notamment la taille ou le budget).")
    else:
        st.success(f"Nous avons trouvé **{len(resultats)}** produit(s) correspondant à vos attentes.")
        
        resultats = resultats.sort_values(by='Prix_FCFA', ascending=True)
        top_suggestions = resultats.head(5)
        
        for i, (index, prod) in enumerate(top_suggestions.iterrows(), 1):
            nom = prod.get('Nom_original', prod.get('Nom', 'Nom non disponible'))
            marque = prod.get('Marque', 'N/A')
            prix = prod.get('Prix_FCFA', 'N/A')
            plateforme = prod.get('Plateforme', 'N/A')
            taille_prod = prod.get('Taille_Format', 'N/A') # Récupération pour l'affichage
            
            # Gestion robuste du lien (cherche plusieurs noms de colonnes possibles)
            lien = prod.get('Lien_acces_produit', prod.get('Lien', '#'))
            
            with st.container():
                st.markdown(f"### Choix n°{i} : {nom}")
                st.write(f"• **Marque :** {marque}")
                st.write(f"• **Taille / Format :** {taille_prod}")
                st.write(f"• **Prix :** {prix} FCFA *(Vendu par : {plateforme})*")
                
                if pd.notna(lien) and str(lien).startswith("http"):
                    st.markdown(f"[🔗 Accéder directement au produit]({lien})", unsafe_allow_html=True)
                else:
                    st.write("🔗 *Lien direct non disponible pour ce produit*")
                st.markdown("---")