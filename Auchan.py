import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import unicodedata
import time

# Vos liens Auchan complets
liens_de_base_auchan = [
    "https://www.auchan.sn/156-hygiene-soinsintime",
    "https://www.auchan.sn/recherche?controller=search&s=protection+intime",
    "https://www.auchan.sn/recherche?controller=search&s=tampon"
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

# Mots exclus stricts pour éliminer tout ce qui est ménager (Spontex, vaisselle, etc.)
mots_exclus = [
    "couche adulte", "incontinence", "masseur", "gel intime", "savon", "lingette", 
    "vaisselle", "spontex", "grattoir", "sol", "menager", "nettoyant", "nettoyage", "eponge"
]

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
    if "lavable" in nom_n or "reutilisable" in nom_n or "culotte" in nom_n or "coupe" in nom_n:
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

def nettoyer_prix(prix_str):
    if not prix_str:
        return None
    chiffres_trouves = re.findall(r'\d+', prix_str.replace(" ", "").replace("\xa0", "").replace(",", ""))
    if not chiffres_trouves:
        return None
    valeurs_valides = [int(b) for b in chiffres_trouves if 100 <= int(b) <= 100000]
    return min(valeurs_valides) if valeurs_valides else None

produits_recuperes = []

for base_url in liens_de_base_auchan:
    page = 1
    print(f"\n--- Traitement du lien : {base_url} ---")
    
    while True:
        # Construction de l'URL selon s'il s'agit d'une recherche ou d'une catégorie
        if "recherche" in base_url:
            url_courante = f"{base_url}&page={page}" if page > 1 else base_url
        else:
            url_courante = f"{base_url}?page={page}" if page > 1 else base_url
            
        print(f"Exploration page {page}...")
        try:
            response = requests.get(url_courante, headers=headers, timeout=15)
            
            # Si la page n'existe plus ou renvoie une erreur (ex: 404/500), on arrête ce lien
            if response.status_code != 200:
                print(f"-> Fin de pagination (Code HTTP {response.status_code}).")
                break
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.select('.product-miniature, .item-product, article, .js-product-miniature')
            
            # Si aucun article n'est trouvé sur la page, on stoppe la boucle de pagination
            if not articles:
                print("-> Aucun article supplémentaire sur cette page.")
                break
                
            produits_sur_cette_page = 0
            for article in articles:
                name_elem = article.select_one('.product-title, h2, h3, a.product-name')
                nom = name_elem.text.strip() if name_elem else ""
                
                if not nom:
                    continue
                
                nom_n = normaliser(nom)
                # Vérification des exclusions strictes (ménage, etc.)
                if any(exclu in nom_n for exclu in mots_exclus):
                    continue
                
                type_p = determiner_type_produit(nom)
                if type_p == "Autre":
                    continue
                
                price_elem = article.select_one('.price, .current-price, span.price')
                prix = nettoyer_prix(price_elem.text if price_elem else "")
                
                link_elem = article.select_one('a')
                lien = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                
                produits_recuperes.append({
                    "Nom_original": nom,
                    "Marque": "Auchan" if "auchan" in normaliser(nom) else "Non spécifié",
                    "Type_produit": type_p,
                    "Categorie": determiner_categorie(nom),
                    "Nombre_pieces": extraire_nombre_pieces(nom),
                    "Taille_Format": extraire_taille(nom),
                    "Prix_FCFA": prix,
                    "Ancien_prix_FCFA": None,
                    "Plateforme": "Auchan",
                    "Soumis_par": "Lien direct",
                    "Lien_acces_produit": lien
                })
                produits_sur_cette_page += 1
            
            print(f"-> {produits_sur_cette_page} produits pertinents ajoutés.")
            
            # Si la page a renvoyé 0 produits pertinents, inutile de chercher plus loin sur ce lien
            if produits_sur_cette_page == 0:
                break
                
            page += 1
            time.sleep(1) # Petite pause de courtoisie pour éviter le blocage par le serveur
            
        except Exception as e:
            print(f"Erreur rencontrée : {e}")
            break

if produits_recuperes:
    df = pd.DataFrame(produits_recuperes).drop_duplicates(subset=["Lien_acces_produit"])
    nom_fichier = "produits_auchan_protection_menstruelle.xlsx"
    df.to_excel(nom_fichier, index=False)
    print(f"\n✨ Succès total ! {len(df)} produits uniques enregistrés dans '{nom_fichier}'.")
else:
    print("\nAucun produit trouvé.")