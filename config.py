"""Configuration centralisée pour le projet municipales-2026."""

from pathlib import Path

# Chemins du projet
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DOCS_DIR = PROJECT_ROOT / "docs"

# URLs des sources de données (data.gouv.fr)
URLS = {
    # Municipales 2026 - Candidats Elus - Tour 1
    "resultats_t1": "https://www.data.gouv.fr/api/1/datasets/r/bc9bca84-beb4-4525-b79a-23ecca48d86e",
    # Municipales 2026 - Candidats Elus - Tour 2
    "resultats_t2": "https://www.data.gouv.fr/api/1/datasets/r/ddd5a822-0cb1-4ebd-9da3-193411ab4d30",
    # Arrondissements Paris Lyon Marseille - Tour 1
    "arrondissements_t1": "https://www.data.gouv.fr/api/1/datasets/r/e9b07817-433c-4c26-afb3-5bf1304622e2",
    # Arrondissements Paris Lyon Marseille - Tour 2
    "arrondissements_t2": "https://www.data.gouv.fr/api/1/datasets/r/879a6c8e-2a59-419a-8e86-587e635f02d7",
    # Population municipale (INSEE via data.gouv.fr)
    "population": "https://www.data.gouv.fr/api/1/datasets/r/be303501-5c46-48a1-87b4-3d198423ff49",
    # Coordonnées des communes avec département et région (geo.api.gouv.fr)
    "communes_geo": "https://geo.api.gouv.fr/communes?fields=code,nom,centre,codeDepartement,codeRegion&format=json",
    # Liste des départements
    "departements": "https://geo.api.gouv.fr/departements?fields=code,nom,codeRegion",
    # Liste des régions
    "regions": "https://geo.api.gouv.fr/regions?fields=code,nom",
}

# Fichiers de sortie
OUTPUT_FILES = {
    "resultats_t1": RAW_DIR / "resultats_t1.csv",
    "resultats_t2": RAW_DIR / "resultats_t2.csv",
    "arrondissements_t1": RAW_DIR / "arrondissements_t1.csv",
    "arrondissements_t2": RAW_DIR / "arrondissements_t2.csv",
    "population": RAW_DIR / "population.xls",
    "communes_geo": RAW_DIR / "communes_geo.json",
    "departements": RAW_DIR / "departements.json",
    "regions": RAW_DIR / "regions.json",
    "processed": PROCESSED_DIR / "resultats_complets.csv",
    "html": DOCS_DIR / "index.html",
}

# Colonnes attendues dans les fichiers de résultats
RESULT_COLUMNS = {
    "code_insee": "Code de la commune",
    "nom_commune": "Libellé de la commune",
    "nom_candidat": "Nom du candidat",
    "prenom_candidat": "Prénom du candidat",
    "nuance": "Nuance",
    "parti": "Libellé abrégé de liste",
    "voix": "Voix",
    "pourcentage": "% Voix/Exp",
    "elu": "Elu",
}

# Configuration de la visualisation
VIZ_CONFIG = {
    "map_style": "carto-positron",
    "map_center": {"lat": 46.603354, "lon": 1.888334},  # Centre de la France
    "map_zoom": 5,
    "point_size_min": 3,
    "point_size_max": 30,
    "point_opacity": 0.7,
}
