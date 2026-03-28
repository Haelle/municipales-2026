#!/usr/bin/env python3
"""Script principal de build pour le projet municipales-2026."""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DOCS_DIR, OUTPUT_FILES
from src.download import check_local_files, download_all
from src.process import process_data, save_processed
from src.visualize import create_visualization, save_html


def main():
    """Exécute le pipeline complet de build."""
    print("=" * 60)
    print("  MUNICIPALES 2026 - Build Pipeline")
    print("=" * 60)
    print()

    # Étape 1: Vérifier/Télécharger les données
    print("ÉTAPE 1: Vérification des données sources")
    print("-" * 40)

    existing = check_local_files()
    missing = [name for name, exists in existing.items() if not exists]

    if missing:
        print(f"Fichiers manquants: {', '.join(missing)}")
        print("Tentative de téléchargement...")
        results = download_all()

        # Vérifier si des téléchargements ont échoué
        failed = [name for name, success in results.items() if not success]
        if failed:
            print(f"\nAttention: Certains téléchargements ont échoué: {', '.join(failed)}")
            print("Le pipeline utilisera des données de démonstration.\n")
    else:
        print("Toutes les données sources sont présentes.\n")

    # Étape 2: Traitement des données
    print("ÉTAPE 2: Traitement des données")
    print("-" * 40)
    df = process_data()
    save_processed(df)
    print()

    # Étape 3: Génération de la visualisation
    print("ÉTAPE 3: Génération de la visualisation")
    print("-" * 40)
    print(f"  Création de la carte avec {len(df)} communes...")
    fig = create_visualization(df)
    output_path = save_html(fig)
    print()

    # Résumé
    print("=" * 60)
    print("  BUILD TERMINÉ")
    print("=" * 60)
    print(f"\n  Fichier HTML généré: {output_path}")
    print(f"  Taille: {output_path.stat().st_size / 1024:.1f} KB")
    print()

    # Statistiques
    print("  Statistiques:")
    print(f"    - Communes: {len(df)}")
    print(f"    - Blocs politiques: {df['bloc'].nunique()}")
    print(f"    - Population totale: {df['population'].sum():,}")
    print()

    # Instructions
    print("  Pour visualiser:")
    print(f"    1. Ouvrir {output_path} dans un navigateur")
    print("    2. Ou déployer le dossier 'docs/' sur GitHub Pages")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
