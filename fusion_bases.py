import pandas as pd
import os

# Liste de tous tes fichiers Excel générés
fichiers = [
    "produits_auchan_protection_menstruelle.xlsx",
    "produits_dakar_express.xlsx",
    "produits_jumia_protection_menstruelle.xlsx",
    "produits_kitambaa.xlsx",
    "produits_pharmec_protection_menstruelle.xlsx",
    "produits_sakanal.xlsx"
]

dataframes = []

print("\n--- Début de la fusion des bases de données ---")

for f in fichiers:
    if os.path.exists(f):
        try:
            df = pd.read_excel(f)
            # S'assurer que les colonnes clés existent, sinon les uniformiser
            dataframes.append(df)
            print(f"✔ Chargé : {f} ({len(df)} produits)")
        except Exception as e:
            print(f"❌ Erreur de lecture sur {f} : {e}")
    else:
        print(f"⚠️ Attention : Le fichier '{f}' est introuvable dans le dossier.")

if dataframes:
    # Concaténation de tous les DataFrames en un seul
    catalogue_global = pd.concat(dataframes, ignore_index=True)
    
    # Nettoyage des doublons stricts (basé sur le nom du produit et la plateforme)
    if "Nom_original" in catalogue_global.columns and "Plateforme" in catalogue_global.columns:
        catalogue_global = catalogue_global.drop_duplicates(subset=["Nom_original", "Plateforme"], keep="first")
    else:
        catalogue_global = catalogue_global.drop_duplicates()
    
    # Exportation du résultat final
    nom_sortie = "catalogue_global_menstruel.xlsx"
    catalogue_global.to_excel(nom_sortie, index=False)
    print(f"\n✨ Succès total ! Un total de {len(catalogue_global)} produits uniques a été regroupé dans '{nom_sortie}'.")
else:
    print("\n❌ Aucun fichier n'a pu être fusionné.")