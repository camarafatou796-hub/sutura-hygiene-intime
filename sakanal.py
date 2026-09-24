import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import unicodedata
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# URL directe de la catégorie sur Sakanal
url_ciblee = "https://sakanal.sn/fr/52--hygiene-intime"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9"
}

# Configuration d'une session avec réessai automatique
session = requests.Session()
retries = Retry(total=3, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

def normaliser(texte):
    if not texte:
        return ""
    texte = unicodedata.normalize("NFD", str(texte).lower())
    return "".join(c for c in texte if unicodedata.category(c) != "Mn")

mots_exclus = [
    "couche", "incontinence", "bebe", "change", "lingette", "savon", 
    "gel intime", "toilette intime", "bain", "lait", "huile", "creme", "shampoing", "demaquillant"
]

marques_connues = [
    "always", "nana", "kotex", "libresse", "discreet", "saforelle", 
    "tampax", "angel", "monica", "senami", "lilas", "fairy lady", "chanceux", "softcare", "scarf"
]

def determiner_marque(nom):
    nom_n = normaliser(nom)
    for marque in marques_connues:
        if marque in nom_n:
            return marque.capitalize()
            
    mots = str(nom).strip().split()
    if len(mots) > 1:
        for mot in mots:
            mot_clean = normaliser(mot)
            if mot_clean in marques_connues:
                return mot.capitalize()
                
    return "Non spécifié"

def determiner_type_produit(nom):
    nom_n = normaliser(nom)
    if "protege" in nom_n or "slip" in nom_n:
        return "Protège-slip"
    elif "culotte" in nom_n:
        return "Culotte menstruelle"
    elif "tampon" in nom_n or "tampax" in nom_n:
        return "Tampon hygiénique"
    elif "coupe" in nom_n or "cup" in nom_n:
        return "Coupe menstruelle"
    else:
        return "Serviette hygiénique"

def determiner_categorie(nom):
    nom_n = normaliser(nom)
    if "lavable" in nom_n or "reutilisable" in nom_n or "culotte" in nom_n or "coupe" in nom_n:
        return "Lavable"
    return "Jetable"

def extraire_nombre_pieces(nom):
    nom_str = str(nom)
    match = re.search(r'(\d+)\s*(?:pcs|pièces|unités|tabs|pces|s)\b', nom_str, re.IGNORECASE)
    if match:
        return int(match.group(1))
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
    elif "large" in nom_n:
        return "Large"
    return "Standard / Non spécifié"

def nettoyer_prix(prix_str):
    if not prix_str:
        return None
    chiffres_trouves = re.findall(r'\d+', str(prix_str).replace(" ", "").replace("\xa0", "").replace(",", ""))
    if not chiffres_trouves:
        return None
    valeurs_valides = [int(b) for b in chiffres_trouves if 100 <= int(b) <= 500000]
    return min(valeurs_valides) if valeurs_valides else None

produits_recuperes = []
page = 1

print(f"\n--- Exploration de Sakanal : {url_ciblee} ---")

while page <= 3:
    url_courante = f"{url_ciblee}?page={page}" if page > 1 else url_ciblee
    print(f"Page {page} en cours...")
    
    try:
        response = session.get(url_courante, headers=headers, timeout=25)
        
        if response.status_code != 200:
            print(f"-> Fin de pagination ou code HTTP {response.status_code}.")
            break
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = soup.select('div.product, article.product-miniature, div.product-miniature')
        
        if not articles:
            print("-> Aucun article trouvé sur cette page.")
            break
            
        produits_sur_cette_page = 0
        for article in articles:
            name_elem = article.select_one('.product-title a, h3 a, h2 a, h3.h3.product-title a')
            if not name_elem:
                name_elem = article.select_one('a[href*="hygiene-et-beaute"], a[href*=".html"]')
                
            nom = name_elem.text.strip() if name_elem else ""
            
            if not nom or len(nom) < 3:
                continue
            
            nom_n = normaliser(nom)
            if any(exclu in nom_n for exclu in mots_exclus):
                continue
            
            price_elem = article.select_one('.price, span.price, div.product-price-and-shipping span')
            prix = nettoyer_prix(price_elem.text if price_elem else "")
            
            if prix is None:
                continue
            
            old_price_elem = article.select_one('.regular-price, del')
            ancien_prix = nettoyer_prix(old_price_elem.text if old_price_elem else "")
            if prix == ancien_prix:
                ancien_prix = None
            
            link_elem = name_elem if name_elem and name_elem.name == 'a' else article.select_one('a')
            lien = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
            
            produits_recuperes.append({
                "Nom_original": nom,
                "Marque": determiner_marque(nom),
                "Type_produit": determiner_type_produit(nom),
                "Categorie": determiner_categorie(nom),
                "Nombre_pieces": extraire_nombre_pieces(nom),
                "Taille_Format": extraire_taille(nom),
                "Prix_FCFA": prix,
                "Ancien_prix_FCFA": ancien_prix,
                "Plateforme": "Sakanal",
                "Lien_acces_produit": lien
            })
            produits_sur_cette_page += 1
            
        print(f"-> {produits_sur_cette_page} produits pertinents récupérés sur cette page.")
        
        if produits_sur_cette_page == 0:
            break
            
        page += 1
        time.sleep(2)
        
    except Exception as e:
        print(f"Erreur réseau ou timeout sur cette page : {e}")
        break

# Exportation des résultats
if produits_recuperes:
    df = pd.DataFrame(produits_recuperes).drop_duplicates(subset=["Nom_original"])
    nom_fichier = "produits_sakanal.xlsx"
    try:
        df.to_excel(nom_fichier, index=False)
        print(f"\n✨ Succès ! {len(df)} produits enregistrés dans '{nom_fichier}'.")
    except PermissionError:
        print(f"\n❌ ERREUR : Le fichier '{nom_fichier}' est ouvert dans Excel. Veuillez le fermer !")
else:
    print("\n❌ Aucun produit récupéré.")