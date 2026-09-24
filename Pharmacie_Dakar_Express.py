import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import unicodedata
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Liens de recherche et produit direct
urls_cibles = [
    "https://pharmacie.dakar.express/?s=protege+slips&post_type=product",
    "https://pharmacie.dakar.express/?s=serviette+hygienique&post_type=product",
    "https://pharmacie.dakar.express/?s=culotte+menstruelle&post_type=product",
    "https://pharmacie.dakar.express/product/organyc-tampon-super-100-cotton-bio-16-pi-ces/"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9"
}

# Configuration d'une session avec politique de réessai automatique (Retry)
session = requests.Session()
retries = Retry(total=3, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

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
    "bella", "vess", "tampax", "o.b.", "organyc", "florgynal", "longrich", "angel", "monica", "senami", "Les Petites Choses"
]

def determiner_marque(nom):
    nom_n = normaliser(nom)
    for marque in marques_connues:
        marque_n = normaliser(marque)  # <--- On normalise la marque de la liste
        if marque_n in nom_n:
            if "petites choses" in marque_n:
                return "Les Petites Choses"
            return marque.capitalize()
            
    mots = str(nom).strip().split()
    if mots:
        premier_mot = mots[0].strip(".,:;()[]")
        premier_mot_n = normaliser(premier_mot)
        
        # On interdit les articles isolés comme première marque
        mots_interdits_locaux = mots_interdits_marques + ["les", "des", "le", "la"]
        
        if premier_mot_n in mots_interdits_locaux or len(premier_mot) <= 2 or not premier_mot[0].isupper():
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

for base_url in urls_cibles:
    # 1. Cas d'un produit unique direct
    if "/product/" in base_url:
        print(f"\n--- Traitement de la fiche produit directe : {base_url} ---")
        try:
            response = session.get(base_url, headers=headers, timeout=25)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                name_elem = soup.select_one('h1.product_title, h1')
                nom = name_elem.text.strip() if name_elem else ""
                
                if nom:
                    nom_n = normaliser(nom)
                    if not any(exclu in nom_n for exclu in mots_exclus):
                        type_p = determiner_type_produit(nom)
                        if type_p != "Autre":
                            price_container = soup.select_one('.price')
                            if price_container:
                                price_container_copy = BeautifulSoup(str(price_container), 'html.parser')
                                for del_tag in price_container_copy.select('del'):
                                    del_tag.decompose()
                                prix = nettoyer_prix(price_container_copy.text)
                            else:
                                prix = None
                                
                            if prix is not None:
                                old_price_elem = soup.select_one('.price del span.amount, .price del')
                                ancien_prix = nettoyer_prix(old_price_elem.text if old_price_elem else "")
                                if prix == ancien_prix:
                                    ancien_prix = None
                                    
                                produits_recuperes.append({
                                    "Nom_original": nom,
                                    "Marque": determiner_marque(nom),
                                    "Type_produit": type_p,
                                    "Categorie": determiner_categorie(nom),
                                    "Nombre_pieces": extraire_nombre_pieces(nom),
                                    "Taille_Format": extraire_taille(nom),
                                    "Prix_FCFA": prix,
                                    "Ancien_prix_FCFA": ancien_prix,
                                    "Plateforme": "Dakar Express",
                                    "Lien_acces_produit": base_url
                                })
                                print("-> 1 produit unique ajouté avec succès.")
        except Exception as e:
            print(f"Erreur réseau sur le produit direct : {e}")
        continue

    # 2. Cas des pages de recherche avec pagination automatique
    page = 1
    print(f"\n--- Exploration du lien de recherche : {base_url} ---")
    
    while page <= 10:
        if page == 1:
            url_courante = base_url
        else:
            if "?" in base_url:
                parties = base_url.split("?")
                url_courante = f"{parties[0]}page/{page}/?{parties[1]}"
            else:
                url_courante = f"{base_url}page/{page}/"
                
        print(f"Page {page} en cours...")
        try:
            response = session.get(url_courante, headers=headers, timeout=25)
            
            if response.status_code != 200:
                print(f"-> Fin de pagination (Code HTTP {response.status_code}).")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select('div.product, li.product, .type-product')
            
            if not articles:
                print("-> Aucun article trouvé sur cette page. Fin de l'exploration pour ce lien.")
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
                
                price_container = article.select_one('.price')
                if price_container:
                    price_container_copy = BeautifulSoup(str(price_container), 'html.parser')
                    for del_tag in price_container_copy.select('del'):
                        del_tag.decompose()
                    prix = nettoyer_prix(price_container_copy.text)
                else:
                    prix = None
                
                if prix is None:
                    continue
                
                old_price_elem = article.select_one('.price del span.amount, .price del')
                ancien_prix = nettoyer_prix(old_price_elem.text if old_price_elem else "")
                
                if prix == ancien_prix:
                    ancien_prix = None
                
                # CIBLAGE PROPRE DU VRAI LIEN PRODUIT (sur le titre ou l'image, jamais sur les boutons d'action)
                link_elem = article.select_one('.woocommerce-loop-product__title a, h2 a, h3 a, .product-title a')
                if not link_elem:
                    # Fallback sécurisé : on cherche un lien qui ne contient pas "add_to_wishlist" ou "add-to-cart"
                    all_links = article.select('a[href]')
                    for a in all_links:
                        href_val = a.get('href', '')
                        if 'add_to_wishlist' not in href_val and 'add-to-cart' not in href_val and href_val != '#':
                            link_elem = a
                            break
                
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
                    "Plateforme": "Dakar Express",
                    "Lien_acces_produit": lien
                })
                produits_sur_cette_page += 1
                
            print(f"-> {produits_sur_cette_page} produits pertinents récupérés sur cette page.")
            
            if produits_sur_cette_page == 0:
                break
                
            page += 1
            time.sleep(3)  # Pause un peu plus longue pour éviter les timeouts
            
        except Exception as e:
            print(f"Erreur réseau ou timeout sur cette page : {e}")
            break

# Exportation sécurisée des résultats
if produits_recuperes:
    df = pd.DataFrame(produits_recuperes).drop_duplicates(subset=["Lien_acces_produit"])
    nom_fichier = "produits_dakar_express.xlsx"
    try:
        df.to_excel(nom_fichier, index=False)
        print(f"\n✨ Succès ! {len(df)} produits enregistrés dans '{nom_fichier}'.")
    except PermissionError:
        print(f"\n❌ ERREUR : Le fichier '{nom_fichier}' est ouvert dans Excel. Veuillez le fermer et relancer !")
else:
    print("\n❌ Aucun produit récupéré.")