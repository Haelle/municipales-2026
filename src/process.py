"""Traitement et fusion des données électorales."""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import OUTPUT_FILES, PROCESSED_DIR
from src.colors import get_bloc, get_couleur


def load_arrondissements_csv(path: Path, tour: int) -> pd.DataFrame | None:
    """Charge les résultats des arrondissements Paris/Lyon/Marseille."""
    if not path.exists():
        print(f"  Fichier arrondissements non trouvé: {path}")
        return None

    try:
        df = pd.read_csv(path, sep=";", dtype=str)

        # Parser CODSECT: "75056SR07" -> secteur 07
        df["secteur"] = df["CODSECT"].str.extract(r"SR(\d+)$")[0].astype(int)
        df["ville_code"] = df["CODSECT"].str.extract(r"^(\d+)SR")[0]

        # Créer code_insee pour chaque arrondissement
        # Paris: 75056SRxx -> 751xx
        # Lyon: 69123SRxx -> 6938x
        # Marseille: 13055SRxx -> 132xx (secteur*2-1 et secteur*2)
        def make_arr_code(row):
            if row["ville_code"] == "75056":
                return f"751{int(row['secteur']):02d}"
            elif row["ville_code"] == "69123":
                return f"6938{int(row['secteur'])}"
            elif row["ville_code"] == "13055":
                return f"132{int(row['secteur']):02d}"
            return None

        df["code_insee"] = df.apply(make_arr_code, axis=1)

        # Prendre le premier élu par secteur (maire d'arrondissement)
        maires = df.groupby("code_insee").first().reset_index()

        maires = maires.rename(columns={
            "NOMPSN": "nom_maire",
            "PREPSN": "prenom_maire",
            "CODE_NUANCE_DE_LISTE": "nuance",
        })

        maires["tour"] = tour
        maires["maire"] = maires["prenom_maire"].fillna("") + " " + maires["nom_maire"].fillna("")
        maires["maire"] = maires["maire"].str.strip()

        return maires[["code_insee", "maire", "nuance", "tour"]]

    except Exception as e:
        print(f"  Erreur lecture arrondissements {path}: {e}")
        return None


def load_results_csv(path: Path, tour: int) -> pd.DataFrame | None:
    """Charge un fichier de résultats électoraux et extrait les maires."""
    if not path.exists():
        print(f"  Fichier non trouvé: {path}")
        return None

    try:
        df = pd.read_csv(path, sep=";", dtype=str)

        # Créer le code INSEE: département (2 chiffres) + commune (3 derniers chiffres)
        df["code_insee"] = df["CODDPT"].str.zfill(2) + df["CODCOM"].str[-3:].str.zfill(3)

        # Prendre uniquement le premier élu par commune (le maire / tête de liste)
        maires = df.groupby("code_insee").first().reset_index()

        # Renommer les colonnes
        maires = maires.rename(columns={
            "NOMPSN": "nom_maire",
            "PREPSN": "prenom_maire",
            "CODE_NUANCE_DE_LISTE": "nuance",
        })

        # Ajouter le tour
        maires["tour"] = tour

        # Créer le nom complet du maire
        maires["maire"] = maires["prenom_maire"].fillna("") + " " + maires["nom_maire"].fillna("")
        maires["maire"] = maires["maire"].str.strip()

        return maires[["code_insee", "maire", "nuance", "tour"]]

    except Exception as e:
        print(f"  Erreur lecture {path}: {e}")
        return None


def load_communes_geo(path: Path) -> pd.DataFrame | None:
    """Charge les coordonnées des communes depuis le JSON geo.api."""
    if not path.exists():
        print(f"  Fichier non trouvé: {path}")
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        records = []
        for commune in data:
            if "centre" in commune and commune["centre"]:
                coords = commune["centre"].get("coordinates", [None, None])
                records.append({
                    "code_insee": commune.get("code", ""),
                    "nom": commune.get("nom", ""),
                    "lon": coords[0] if len(coords) > 0 else None,
                    "lat": coords[1] if len(coords) > 1 else None,
                })

        return pd.DataFrame(records)
    except Exception as e:
        print(f"  Erreur lecture {path}: {e}")
        return None


def load_population(path: Path) -> pd.DataFrame | None:
    """Charge les données de population INSEE."""
    if not path.exists():
        print(f"  Fichier non trouvé: {path}")
        return None

    try:
        df = pd.read_excel(path, dtype={"codgeo": str})
        # Utiliser la population 2023 (colonne p23_pop)
        df = df.rename(columns={"codgeo": "code_insee", "p23_pop": "population"})
        pop = df[["code_insee", "population"]].copy()

        # Calculer les totaux pour Paris, Lyon et Marseille (arrondissements)
        # Paris: 75101-75120 -> 75056
        paris_arr = pop[pop["code_insee"].str.match(r"^751\d{2}$", na=False)]
        if not paris_arr.empty:
            paris_pop = paris_arr["population"].sum()
            pop = pd.concat([pop, pd.DataFrame([{"code_insee": "75056", "population": paris_pop}])], ignore_index=True)

        # Lyon: 69381-69389 -> 69123
        lyon_arr = pop[pop["code_insee"].str.match(r"^6938[1-9]$", na=False)]
        if not lyon_arr.empty:
            lyon_pop = lyon_arr["population"].sum()
            pop = pd.concat([pop, pd.DataFrame([{"code_insee": "69123", "population": lyon_pop}])], ignore_index=True)

        # Marseille: 13201-13216 -> 13055
        marseille_arr = pop[pop["code_insee"].str.match(r"^132\d{2}$", na=False)]
        if not marseille_arr.empty:
            marseille_pop = marseille_arr["population"].sum()
            pop = pd.concat([pop, pd.DataFrame([{"code_insee": "13055", "population": marseille_pop}])], ignore_index=True)

        return pop
    except Exception as e:
        print(f"  Erreur lecture {path}: {e}")
        return None


def process_data() -> pd.DataFrame:
    """Traite et fusionne toutes les sources de données."""
    print("=== Traitement des données ===\n")

    # Charger les résultats T1 et T2
    print("Chargement des résultats électoraux...")
    t1 = load_results_csv(OUTPUT_FILES["resultats_t1"], tour=1)
    t2 = load_results_csv(OUTPUT_FILES["resultats_t2"], tour=2)

    if t1 is None and t2 is None:
        raise ValueError("Aucun fichier de résultats trouvé")

    # Charger les arrondissements Paris/Lyon/Marseille
    print("Chargement des arrondissements (PaLyMa)...")
    arr1 = load_arrondissements_csv(OUTPUT_FILES["arrondissements_t1"], tour=1)
    arr2 = load_arrondissements_csv(OUTPUT_FILES["arrondissements_t2"], tour=2)

    # Fusionner T1 et T2 (T1 prioritaire si une commune apparaît dans les deux)
    all_results = []
    if t1 is not None:
        all_results.append(t1)
    if t2 is not None:
        all_results.append(t2)
    if arr1 is not None:
        all_results.append(arr1)
        print(f"  Arrondissements T1: {len(arr1)}")
    if arr2 is not None:
        all_results.append(arr2)
        print(f"  Arrondissements T2: {len(arr2)}")

    if not all_results:
        raise ValueError("Aucun fichier de résultats trouvé")

    results = pd.concat(all_results, ignore_index=True)
    # Garder la première occurrence (T1 si présent)
    results = results.drop_duplicates(subset=["code_insee"], keep="first")
    print(f"  Maires T1: {len(t1) if t1 is not None else 0}, Maires T2: {len(t2) if t2 is not None else 0}")

    # Charger les coordonnées
    print("Chargement des coordonnées...")
    geo = load_communes_geo(OUTPUT_FILES["communes_geo"])
    if geo is None:
        raise ValueError("Fichier de coordonnées non trouvé")

    # Charger la population
    print("Chargement de la population...")
    pop = load_population(OUTPUT_FILES["population"])

    # Joindre avec les coordonnées
    df = results.merge(geo, on="code_insee", how="inner")
    print(f"  Communes avec coordonnées: {len(df)}")

    # Joindre avec la population
    if pop is not None:
        df = df.merge(pop, on="code_insee", how="left")
        # Remplir les populations manquantes avec une valeur par défaut
        df["population"] = df["population"].fillna(500).astype(int)
        print(f"  Communes avec population: {df['population'].notna().sum()}")
    else:
        df["population"] = 500  # Valeur par défaut

    # Ajouter bloc et couleur
    df["nuance"] = df["nuance"].fillna("DIV")
    df["bloc"] = df["nuance"].apply(get_bloc)
    df["couleur"] = df["nuance"].apply(get_couleur)

    # Réduire la précision des coordonnées pour optimiser
    df["lat"] = df["lat"].round(4)
    df["lon"] = df["lon"].round(4)

    # Filtrer les lignes sans coordonnées
    df = df.dropna(subset=["lat", "lon"])

    print(f"\n  Communes traitées: {len(df)}")
    print(f"  Blocs politiques: {df['bloc'].nunique()}")
    print(f"  Maires élus T1: {(df['tour'] == 1).sum()}")
    print(f"  Maires élus T2: {(df['tour'] == 2).sum()}")

    return df


def save_processed(df: pd.DataFrame) -> Path:
    """Sauvegarde les données traitées."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_FILES["processed"]
    df.to_csv(output_path, index=False)
    print(f"  Sauvegardé: {output_path}")
    return output_path


if __name__ == "__main__":
    df = process_data()
    save_processed(df)
    print("\n=== Traitement terminé ===")
