"""Téléchargement des données sources."""

import json
import sys
from pathlib import Path

import requests

# Ajouter le répertoire parent au path pour importer config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import OUTPUT_FILES, RAW_DIR, URLS


def download_file(url: str, output_path: Path, description: str = "") -> bool:
    """Télécharge un fichier depuis une URL."""
    print(f"Téléchargement {description or output_path.name}...")

    try:
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"  -> Sauvegardé: {output_path}")
        return True

    except requests.RequestException as e:
        print(f"  -> Erreur: {e}")
        return False


def download_json(url: str, output_path: Path, description: str = "") -> bool:
    """Télécharge et sauvegarde des données JSON."""
    print(f"Téléchargement {description or output_path.name}...")

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        data = response.json()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  -> Sauvegardé: {output_path} ({len(data)} entrées)")
        return True

    except requests.RequestException as e:
        print(f"  -> Erreur: {e}")
        return False


def download_all() -> dict[str, bool]:
    """Télécharge toutes les sources de données."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    results = {}

    # Résultats électoraux T1
    results["resultats_t1"] = download_file(
        URLS["resultats_t1"],
        OUTPUT_FILES["resultats_t1"],
        "résultats 1er tour"
    )

    # Résultats électoraux T2
    results["resultats_t2"] = download_file(
        URLS["resultats_t2"],
        OUTPUT_FILES["resultats_t2"],
        "résultats 2nd tour"
    )

    # Arrondissements Paris Lyon Marseille - T1
    results["arrondissements_t1"] = download_file(
        URLS["arrondissements_t1"],
        OUTPUT_FILES["arrondissements_t1"],
        "arrondissements T1 (Paris/Lyon/Marseille)"
    )

    # Arrondissements Paris Lyon Marseille - T2
    results["arrondissements_t2"] = download_file(
        URLS["arrondissements_t2"],
        OUTPUT_FILES["arrondissements_t2"],
        "arrondissements T2 (Paris/Lyon/Marseille)"
    )

    # Population INSEE
    results["population"] = download_file(
        URLS["population"],
        OUTPUT_FILES["population"],
        "population INSEE"
    )

    # Coordonnées des communes (API geo.gouv.fr)
    results["communes_geo"] = download_json(
        URLS["communes_geo"],
        OUTPUT_FILES["communes_geo"],
        "coordonnées communes"
    )

    # Départements
    results["departements"] = download_json(
        URLS["departements"],
        OUTPUT_FILES["departements"],
        "départements"
    )

    # Régions
    results["regions"] = download_json(
        URLS["regions"],
        OUTPUT_FILES["regions"],
        "régions"
    )

    # GeoJSON France (départements)
    results["france_geo"] = download_file(
        URLS["france_geo"],
        OUTPUT_FILES["france_geo"],
        "GeoJSON départements France"
    )

    # Ajouter les arrondissements au fichier geo
    if results["communes_geo"]:
        add_arrondissements_to_geo(OUTPUT_FILES["communes_geo"])

    return results


def add_arrondissements_to_geo(geo_path: Path) -> None:
    """Ajoute les arrondissements Paris/Lyon/Marseille au fichier geo."""
    print("Ajout des arrondissements (Paris/Lyon/Marseille)...")

    try:
        # Charger le fichier existant
        with open(geo_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        existing_codes = {c.get("code") for c in data}

        # Récupérer les arrondissements via API
        arrondissements = []
        for parent_code in ["75056", "69123", "13055"]:
            url = f"https://geo.api.gouv.fr/communes?codeParent={parent_code}&type=arrondissement-municipal&fields=code,nom,centre"
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                arr_data = response.json()
                for arr in arr_data:
                    if arr.get("code") not in existing_codes:
                        arrondissements.append(arr)
            except Exception as e:
                print(f"  Erreur récupération arrondissements {parent_code}: {e}")

        # Ajouter au fichier
        if arrondissements:
            data.extend(arrondissements)
            with open(geo_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  -> {len(arrondissements)} arrondissements ajoutés")

    except Exception as e:
        print(f"  Erreur ajout arrondissements: {e}")


def check_local_files() -> dict[str, bool]:
    """Vérifie si les fichiers locaux existent déjà."""
    return {
        name: path.exists()
        for name, path in OUTPUT_FILES.items()
        if name in ["resultats_t1", "resultats_t2", "population", "communes_geo", "france_geo"]
    }


if __name__ == "__main__":
    print("=== Téléchargement des données ===\n")

    # Vérifier les fichiers existants
    existing = check_local_files()
    if any(existing.values()):
        print("Fichiers existants:")
        for name, exists in existing.items():
            status = "OK" if exists else "MANQUANT"
            print(f"  - {name}: {status}")
        print()

    # Télécharger
    results = download_all()

    print("\n=== Résumé ===")
    success = sum(results.values())
    total = len(results)
    print(f"Téléchargements réussis: {success}/{total}")

    if success < total:
        print("\nFichiers manquants - le traitement utilisera des données de démonstration.")
