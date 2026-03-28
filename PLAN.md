# Plan : Carte interactive des élections municipales 2026

## Objectif
Créer une visualisation interactive (carte + camembert) des résultats des municipales 2026, exportée en HTML statique pour GitHub Pages.

## Architecture du projet

```
municipales-2026/
├── pyproject.toml               # Config projet + dépendances (UV)
├── config.py                    # URLs sources, constantes, chemins
├── data/
│   ├── raw/                     # Données brutes téléchargées
│   └── processed/               # Données fusionnées
├── src/
│   ├── download.py              # Téléchargement des données
│   ├── process.py               # Nettoyage et fusion
│   ├── colors.py                # Mapping nuances -> couleurs
│   └── visualize.py             # Génération Plotly
├── scripts/
│   └── build.py                 # Script principal
└── docs/
    └── index.html               # Sortie pour GitHub Pages
```

## Sources de données

| Donnée | Source | Format |
|--------|--------|--------|
| Résultats T1 | data.gouv.fr | CSV |
| Résultats T2 | data.gouv.fr | CSV |
| Population | data.gouv.fr | XLSX |
| Coordonnées communes | geo.api.gouv.fr | JSON |

## Pipeline de données

1. **download.py** : Télécharger les 4 sources
2. **process.py** :
   - Fusionner résultats T1 + T2
   - Joindre avec coordonnées via code INSEE
   - Enrichir avec population
   - Calculer bloc politique et couleur
3. **Schéma final** : code_insee, nom, lat, lon, population, maire, nuance, parti, tour, bloc, couleur

## Visualisation (Plotly)

### Carte
- `Scattermap` avec points sur chaque commune
- **Taille des points** : échelle logarithmique de la population
- **Couleur des points** : selon bloc/nuance politique

### Camembert
- Répartition des maires élus par bloc politique

### Filtres interactifs (via `updatemenus` Plotly)
- **Bloc politique** : Tous / Gauche / Centre / Droite / Extrême droite / Divers
- **Parti** : Dropdown avec nuances détaillées (LFI, SOC, LR, RN, etc.)
- **Tour d'élection** : Tous / 1er tour / 2nd tour

## Mapping des couleurs

| Bloc | Nuances | Couleur |
|------|---------|---------|
| Extrême Gauche | EXG, LFI, NPA | #BB0000 |
| Gauche | COM, SOC, DVG, VEC | #FF6B6B |
| Écologistes | ECO, VEC | #2ECC71 |
| Centre | REM, MDM, HOR, UDI | #F39C12 |
| Droite | LR, DVD | #3498DB |
| Extrême Droite | RN, REC | #1A1A2E |
| Divers | DIV, DSV | #95A5A6 |

## Étapes d'implémentation

1. **config.py** - Configuration centralisée
2. **src/colors.py** - Mapping nuances/couleurs
3. **src/download.py** - Téléchargement des sources
4. **src/process.py** - Fusion et nettoyage
5. **src/visualize.py** - Carte + camembert + filtres
6. **scripts/build.py** - Orchestration
7. **Déploiement** - GitHub Pages depuis `/docs`

## Dépendances Python (via UV)

```toml
# pyproject.toml
[project]
name = "municipales-2026"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pandas>=2.0",
    "plotly>=5.24",
    "requests>=2.31",
    "openpyxl>=3.1",
    "numpy>=1.24",
]

[tool.uv]
dev-dependencies = []
```

Installation : `uv sync`

## Vérification

1. Installer les dépendances : `uv sync`
2. Exécuter `uv run python scripts/build.py`
3. Ouvrir `docs/index.html` dans un navigateur
4. Tester les filtres (bloc, parti, tour)
5. Vérifier la taille des points (grandes villes = gros points)
6. Vérifier le camembert mis à jour avec les filtres
7. Tester sur mobile (responsive)

## Points d'attention

- ~35000 communes : utiliser WebGL (natif Scattermap) + réduire précision coordonnées
- Gestion des communes sans correspondance INSEE
- Couleur grise par défaut pour nuances inconnues
- DOM-TOM : coordonnées hors métropole à gérer
