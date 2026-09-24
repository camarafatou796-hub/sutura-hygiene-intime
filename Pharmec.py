import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import unicodedata
import time

# Liste complète des liens Pharmec à explorer (incluant les soins intimes)
urls_pharmec = [
    "https://pharmec.sn/categorie-produit/maman-bebe/hygiene-feminine/",
    "https://pharmec.sn/categorie-produit/soins-intimes/",
    "https://pharmec.sn/?s=serviette+hygienique&post_type=product",
    "https://pharmec.sn/?s=tampon&post_type=product"
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

mots_exclus = [
    "couche", "incontinence", "bebe", "culotte d'apprentissage", "change",
    "lingette", "savon", "gel intime", "toilette intime", "bain", "lait", 
    "huile", "creme", "baume", "suplement", "tétine", "biberon", "shampoing"
]

mots_interdits_marques = ["kit", "lot", "culotte", "serviette", "serviettes", "protege", "coupe", "tampon", "proteges"]

marques_connues = [
    "always", "nana", "kotex", "libresse", "discreet", "saforelle", 
    "masmi", "dadoo", "apiafrique", "dim", "naturella", "carefree", 
    "bella", "vess", "tampax", "o.b.", "organyc", "florgynal", "longrich", "angel", "monica", "senami"
]

def determiner_marque(nom):
    nom_n = normaliser(nom)
    for marque in marques_connues:
        if marque in nom_n:
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

def determiner_type_produit(nom):
    nom_n = normaliser(nom)
    if "protege" in nom_n or "slip" in nom_n:
        return "Protège-slip"
    elif "culotte" in nom_n:
        return "Culotte menstruelle"
    elif "tampon" in nom_n:
        return "Tampon hygiénique"
    elif "coupe" in nom_n or "cup" in nom_n:
        return "Coupe menstruelle"
    elif "serviette" in nom_n:
        return "Serviette hygiénique"
    return "Autre"

def determiner_categorie(nom):
    nom_n = normaliser(nom)
    if "lavable" in nom_n or "reutilisable" in nom_n or "culotte" in nom_n or "coupe" in nom_n or "cup" in nom_n or "kit" in nom_n:
        return "Lavable"
    return "Jetable"

def extraire_nombre_pieces(nom):
    nom_str = str(nom)
    match = re.search(r'(?:boite de|paquet de|lot de|pcs|pièces|unités|tabs)?\s*(\d+)\s*(?:pieces|pces|units|unités|tampons|serviettes|s)?\b', nom_str, re.IGNORECASE)
    if match:
        nombre = int(match.group(1))
        if 2 <= nombre <= 500:
            return nombre
            
    match_x = re.search(r'(?:^|\s)[xX](\d+)\b', nom_str)
    if match_x:
        nombre = int(match_x.group(1))
        if 2 <= nombre <= 500:
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

def nettoyer_prix(prix_str):
    if not prix_str:
        return None
    chiffres_trouves = re.findall(r'\d+', str(prix_str).replace(" ", "").replace("\xa0", "").replace(",", ""))
    if not chiffres_trouves:
        return None
    valeurs_valides = [int(b) for b in chiffres_trouves if 500 <= int(b) <= 500000]
    return min(valeurs_valides) if valeurs_valides else None

produits_recuperes = []

for base_url in urls_pharmec:
    page = 1
    print(f"\n--- Exploration du lien Pharmec : {base_url} ---")
    
    while page <= 10:  # Limite de sécurité par lien
        if "?" in base_url:
            url_courante = f"{base_url}&paged={page}" if page > 1 else base_url
        else:
            url_courante = f"{base_url}page/{page}/" if page > 1 else base_url
            
        print(f"Page {page} en cours...")
        try:
            response = requests.get(url_courante, headers=headers, timeout=20)
            
            if response.status_code != 200:
                print(f"-> Fin de pagination (Code HTTP {response.status_code}).")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select('div.product, li.product, .type-product')
            
            if not articles:
                print("-> Aucun article trouvé sur cette page.")
                break
                
            produits_sur_cette_page = 0
            for article in articles:
                name_elem = article.select_one('.woocommerce-loop-product__title, h2, h3, .product-title')
                if not name_elem:
                    name_elem = article.select_one('h2, h3, a')
                nom = name_elem.text.strip() if name_elem else ""
                
                if not nom:
                    continue
                
                nom_n = normaliser(nom)
                if any(exclu in nom_n for exclu in mots_exclus):
                    continue
                
                type_p = determiner_type_produit(nom)
                if type_p == "Autre":
                    continue
                
                # --- EXTRACTION ET FILTRAGE DES PRIX ---
                price_container = article.select_one('.price')
                if price_container:
                    price_container_copy = BeautifulSoup(str(price_container), 'html.parser')
                    for del_tag in price_container_copy.select('del'):
                        del_tag.decompose()
                    prix = nettoyer_prix(price_container_copy.text)
                else:
                    prix = None
                
                # On ignore immédiatement le produit si le prix est absent ou invalide
                if prix is None:
                    continue
                
                old_price_elem = article.select_one('.price del span.amount, .price del')
                ancien_prix = nettoyer_prix(old_price_elem.text if old_price_elem else "")
                
                if prix == ancien_prix:
                    ancien_prix = None
                # ----------------------------------------
                
                link_elem = article.select_one('a.woocommerce-LoopProduct-link, a')
                lien = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                
                produits_recuperes.append({
                    "Nom_original": nom,
                    "Marque": determiner_marque(nom),
                    "Type_produit": type_p,
                    "Categorie": determiner_categorie(nom),
                    "Nombre_pieces": extraire_nombre_pieces(nom),
                    "Taille_Format": extraire_taille(nom),
                    "Prix_FCFA": prix,
                    "Ancien_prix_FCFA": ancien_prix,
                    "Plateforme": "Pharmec",
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

if produits_recuperes:
    df = pd.DataFrame(produits_recuperes).drop_duplicates(subset=["Lien_acces_produit"])
    nom_fichier = "produits_pharmec_protection_menstruelle.xlsx"
    try:
        df.to_excel(nom_fichier, index=False)
        print(f"\n✨ Succès total ! {len(df)} produits avec un prix valide enregistrés dans '{nom_fichier}'.")
    except PermissionError:
        print(f"\n❌ ERREUR : Le fichier '{nom_fichier}' est ouvert dans Excel. Veuillez le fermer !")
else:
    print("\n❌ Aucun produit récupéré.")