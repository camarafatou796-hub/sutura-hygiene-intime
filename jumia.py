import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import unicodedata

urls_jumia = [
    "https://www.jumia.sn/catalog/?q=serviettes+hygieniques",
    "https://www.jumia.sn/catalog/?q=protege+slips",
    "https://www.jumia.sn/catalog/?q=culotte+menstruelle",
    "https://www.jumia.sn/catalog/?q=tampon+hygienique",
    "https://www.jumia.sn/catalog/?q=coupe+menstruelle"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9"
}

def normaliser(texte):
    if not texte:
        return ""
    texte = unicodedata.normalize("NFD", str(texte).lower())
    return "".join(c for c in texte if unicodedata.category(c) != "Mn")

# Mots-clés pour exclure formellement les produits non concernés
mots_exclus = [
    "couche adulte", "couches adulte", "incontinence", "adulte",
    "masseur", "massage", "appareil", "ceinture lombaire", "chaleur"
]

# Mots interdits en tant que "Marque" (termes génériques)
mots_interdits_marques = ["kit", "lot", "culotte", "serviette", "serviettes", "protege", "coupe", "tampon", "proteges", "paquet"]

# Liste des marques connues
marques_connues = [
    "boni bravo lady", "always", "nana", "kotex", "libresse", "discreet", "saforelle", 
    "masmi", "dadoo", "apiafrique", "dim", "her underwear", "naturella",
    "carefree", "eva", "bella", "vess", "tampax", "o.b.", "organyc", "indas"
]

def determiner_marque(nom):
    nom_n = normaliser(nom)
    for marque in marques_connues:
        if marque in nom_n:
            if "boni" in marque or "bravo" in marque:
                return "Boni Bravo Lady"
            return marque.capitalize()
            
    mots = str(nom).strip().split()
    if mots:
        premier_mot = mots[0].strip(".,:;()[]")
        premier_mot_n = normaliser(premier_mot)
        
        if premier_mot_n in mots_interdits_marques or len(premier_mot) <= 2 or not premier_mot[0].isupper():
            return "Non spécifié"
        
        if len(premier_mot) > 2 and premier_mot[0].isupper():
            return premier_mot.capitalize()
            
    return "Non spécifié"

def determiner_type_produit_jumia(nom):
    nom_n = str(nom).lower()
    if "protege" in nom_n or "slip" in nom_n:
        return "Protège-slip"
    elif "culotte" in nom_n:
        return "Culotte menstruelle"
    elif "tampon" in nom_n:
        return "Tampon hygiénique"
    elif "coupe" in nom_n or "cup" in nom_n:
        return "Coupe menstruelle"
    else:
        # Par défaut, tout le reste (serviettes, packs maternité, etc.) va dans serviette hygiénique
        return "Serviette hygiénique"

def determiner_categorie(nom):
    nom_n = normaliser(nom)
    if "lavable" in nom_n or "reutilisable" in nom_n or "culotte" in nom_n or "coupe" in nom_n or "cup" in nom_n:
        return "Lavable"
    return "Jetable"

def extraire_nombre_pieces(nom):
    match = re.search(r'(?:x|boite de|paquet de|lot de)?\s*(\d+)\s*(?:pieces|pces|units|unités|tampons|serviettes)?', nom, re.IGNORECASE)
    if match:
        nombre = int(match.group(1))
        if 1 <= nombre <= 500:
            return nombre
    return None

def extraire_taille(nom):
    nom_n = normaliser(nom)
    if "nuit" in nom_n or "night" in nom_n:
        return "Nuit"
    elif "maxi" in nom_n:
        return "Maxi"
    elif "super" in nom_n:
        return "Super"
    elif "normal" in nom_n:
        return "Normal"
    elif "mini" in nom_n:
        return "Mini"
    return "Standard / Non spécifié"

produits_recuperes = []

for url in urls_jumia:
    print(f"Scraping en cours : {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('article', class_='prd')
            
            for article in articles:
                name_elem = article.find('h3', class_='name')
                nom = name_elem.text.strip() if name_elem else ""
                
                # 1. Exclusion stricte
                nom_n = normaliser(nom)
                if any(exclu in nom_n for exclu in mots_exclus):
                    continue
                
                # 2. Extraction du prix actuel ('prc')
                price_elem = article.find('div', class_='prc')
                prix_str = price_elem.text.strip() if price_elem else ""
                chiffres_trouves = re.findall(r'\d+', prix_str)
                
                prix = None
                if chiffres_trouves:
                    prix_candidat = int(''.join(chiffres_trouves))
                    if prix_candidat > 50000:
                        str_cand = str(prix_candidat)
                        if len(str_cand) >= 7:
                            prix_candidat = int(str_cand[:4])
                        else:
                            prix_candidat = None
                    prix = prix_candidat

                # 3. Extraction de l'ancien prix ('old')
                old_price_elem = article.find('div', class_='old')
                ancien_prix = None
                if old_price_elem:
                    old_prix_str = old_price_elem.text.strip()
                    old_chiffres = re.findall(r'\d+', old_prix_str)
                    if old_chiffres:
                        old_candidat = int(''.join(old_chiffres))
                        if old_candidat <= 50000:
                            ancien_prix = old_candidat
                
                link_elem = article.find('a', class_='core')
                if link_elem and 'href' in link_elem.attrs:
                    lien = "https://www.jumia.sn" + link_elem['href']
                else:
                    lien = ""
                
                if nom:
                    type_p = determiner_type_produit_jumia(nom)
                    produits_recuperes.append({
                        "Nom_original": nom,
                        "Marque": determiner_marque(nom),
                        "Type_produit": type_p,
                        "Categorie": determiner_categorie(nom),
                        "Nombre_pieces": extraire_nombre_pieces(nom),
                        "Taille_Format": extraire_taille(nom),
                        "Prix_FCFA": prix,
                        "Ancien_prix_FCFA": ancien_prix,
                        "Plateforme": "Jumia",
                        "Lien_acces_produit": lien
                    })
    except Exception as e:
        print(f"Erreur : {e}")

if produits_recuperes:
    df = pd.DataFrame(produits_recuperes).drop_duplicates(subset=["Lien_acces_produit"])
    
    # Sécurité supplémentaire sur les exclusions
    for exclu in mots_exclus:
        df = df[~df['Nom_original'].str.lower().str.contains(exclu, na=False)]
        
    nom_fichier = "produits_jumia_protection_menstruelle.xlsx"
    df.to_excel(nom_fichier, index=False)
    print(f"✨ Succès ! {len(df)} produits propres enregistrés dans '{nom_fichier}'.")
else:
    print("Aucun produit récupéré.")