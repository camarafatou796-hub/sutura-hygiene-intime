import pandas as pd

# Données brutes extraites de Kitambaa Woman
donnees_produits = [
    {
        "Nom_original": "Kit Standard Safepad",
        "Marque": "Kitambaa Woman",
        "Type_produit": "Kit de protection",
        "Categorie": "Lavable / Réutilisable",
        "Prix_FCFA": 6000,
        "Ancien_prix_FCFA": None,
        "Plateforme": "Kitambaa Woman",
        "Lien_acces_produit": "https://kitambaa-woman.com/shop-2/"
    },
    {
        "Nom_original": "Culotte Menstruelle Kitambaa",
        "Marque": "Kitambaa Woman",
        "Type_produit": "Culotte menstruelle",
        "Categorie": "Lavable / Réutilisable",
        "Prix_FCFA": 5500,
        "Ancien_prix_FCFA": None,
        "Plateforme": "Kitambaa Woman",
        "Lien_acces_produit": "https://kitambaa-woman.com/shop-2/"
    },
    {
        "Nom_original": "Serviettes Hygiéniques Réutilisables (Pack)",
        "Marque": "Kitambaa Woman",
        "Type_produit": "Serviette hygiénique",
        "Categorie": "Lavable / Réutilisable",
        "Prix_FCFA": 4500,
        "Ancien_prix_FCFA": None,
        "Plateforme": "Kitambaa Woman",
        "Lien_acces_produit": "https://kitambaa-woman.com/shop-2/"
    },
    {
        "Nom_original": "Kit Premium Safepad",
        "Marque": "Kitambaa Woman",
        "Type_produit": "Kit de protection",
        "Categorie": "Lavable / Réutilisable",
        "Prix_FCFA": 10000,
        "Ancien_prix_FCFA": 12000,
        "Plateforme": "Kitambaa Woman",
        "Lien_acces_produit": "https://kitambaa-woman.com/shop-2/"
    },
    {
        "Nom_original": "Protège-slips Lavables",
        "Marque": "Kitambaa Woman",
        "Type_produit": "Serviette hygiénique",
        "Categorie": "Lavable / Réutilisable",
        "Prix_FCFA": 3000,
        "Ancien_prix_FCFA": None,
        "Plateforme": "Kitambaa Woman",
        "Lien_acces_produit": "https://kitambaa-woman.com/shop-2/"
    },
    {
        "Nom_original": "Safepad Nuit (Grande taille)",
        "Marque": "Kitambaa Woman",
        "Type_produit": "Serviette hygiénique",
        "Categorie": "Lavable / Réutilisable",
        "Prix_FCFA": 3500,
        "Ancien_prix_FCFA": None,
        "Plateforme": "Kitambaa Woman",
        "Lien_acces_produit": "https://kitambaa-woman.com/shop-2/"
    },
    {
        "Nom_original": "Culotte Menstruelle Teen",
        "Marque": "Kitambaa Woman",
        "Type_produit": "Culotte menstruelle",
        "Categorie": "Lavable / Réutilisable",
        "Prix_FCFA": 5000,
        "Ancien_prix_FCFA": None,
        "Plateforme": "Kitambaa Woman",
        "Lien_acces_produit": "https://kitambaa-woman.com/shop-2/"
    },
    {
        "Nom_original": "Protection Incontinence Légère",
        "Marque": "Kitambaa Woman",
        "Type_produit": "Protection incontinence",
        "Categorie": "Lavable / Réutilisable",
        "Prix_FCFA": 4000,
        "Ancien_prix_FCFA": None,
        "Plateforme": "Kitambaa Woman",
        "Lien_acces_produit": "https://kitambaa-woman.com/shop-2/"
    }
]

def determiner_type_produit_kitambaa(nom):
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
        # Par défaut (kits complets, protections diverses), on classe en serviette hygiénique
        return "Serviette hygiénique"

# Création du DataFrame
df_kitambaa = pd.DataFrame(donnees_produits)

# Application stricte de la fonction sur le nom original
df_kitambaa['Type_produit'] = df_kitambaa['Nom_original'].apply(determiner_type_produit_kitambaa)

# Sauvegarde propre
df_kitambaa.to_excel("produits_kitambaa.xlsx", index=False)
print("Fichier 'produits_kitambaa.xlsx' généré avec succès sans catégories non conformes !")