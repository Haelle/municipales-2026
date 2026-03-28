# Municipales 2026

Visualisation interactive des résultats des élections municipales françaises de 2026.

## Intention du projet

Ce projet a pour objectif de rendre accessibles et lisibles les résultats des élections municipales 2026 à travers une **carte interactive** permettant d'explorer la répartition politique des maires élus sur l'ensemble du territoire français.

L'outil permet de :

- **Visualiser géographiquement** la couleur politique de chaque commune
- **Comprendre les rapports de force** via des camemberts dynamiques (par communes et par population)
- **Explorer les données** grâce à des filtres multiples (bloc politique, tour d'élection, taille de commune, région, département)
- **Comparer** les résultats selon différents critères démographiques et géographiques

## Fonctionnalités

### Carte interactive

- **34 700+ communes** représentées avec leurs coordonnées géographiques
- Points colorés selon le bloc politique du maire élu
- Taille des points proportionnelle à la population (3 catégories)
- Survol pour afficher les détails (nom, maire, nuance, population, tour)
- Zoom et navigation libre sur la carte

### Camemberts dynamiques

- **Par nombre de communes** : répartition des maires par bloc politique
- **Par population** : poids démographique de chaque bloc
- Mise à jour en temps réel selon les filtres appliqués

### Filtres

- **Bloc politique** : Extrême Gauche, Gauche, Centre, Droite, Extrême Droite, Divers (selon [référentiel MI](https://www.resultats-elections.interieur.gouv.fr/municipales2026/referentiel.html))
- **Tour d'élection** : 1er tour / 2nd tour
- **Taille de commune** : Petites (<5k), Moyennes (5k-50k), Grandes (>50k)
- **Région** : 18 régions françaises (métropole + DOM-TOM)
- **Département** : 101 départements

### Design

- Interface moderne avec Tailwind CSS
- Mode sombre / mode clair
- Responsive (desktop, tablette, mobile)
- Légende interactive des nuances politiques

## Architecture technique

```
municipales-2026/
├── pyproject.toml           # Dépendances Python (UV)
├── config.py                # URLs sources, chemins, constantes
├── data/
│   ├── raw/                 # Données brutes téléchargées
│   └── processed/           # Données fusionnées
├── src/
│   ├── download.py          # Téléchargement des sources
│   ├── process.py           # Nettoyage et fusion des données
│   ├── colors.py            # Mapping nuances → blocs/couleurs
│   └── visualize.py         # Génération Plotly + HTML
├── scripts/
│   └── build.py             # Pipeline complet
└── docs/
    └── index.html           # Sortie HTML pour GitHub Pages
```

## Sources de données

| Donnée                 | Source | Format |
| ---------------------- | ------ | ------ |
| Résultats T1           | [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/r/bc9bca84-beb4-4525-b79a-23ecca48d86e) | CSV |
| Résultats T2           | [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/r/ddd5a822-0cb1-4ebd-9da3-193411ab4d30) | CSV |
| Arrondissements T1 PLM | [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/r/e9b07817-433c-4c26-afb3-5bf1304622e2) | CSV |
| Arrondissements T2 PLM | [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/r/879a6c8e-2a59-419a-8e86-587e635f02d7) | CSV |
| Population INSEE       | [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/r/be303501-5c46-48a1-87b4-3d198423ff49) | XLS |
| Coordonnées communes   | [geo.api.gouv.fr](https://geo.api.gouv.fr/communes?fields=code,nom,centre,codeDepartement,codeRegion&format=json) | JSON |
| Départements           | [geo.api.gouv.fr](https://geo.api.gouv.fr/departements?fields=code,nom,codeRegion) | JSON |
| Régions                | [geo.api.gouv.fr](https://geo.api.gouv.fr/regions?fields=code,nom) | JSON |

## Stack technique

- **Python 3.11+** avec gestionnaire de paquets [UV](https://github.com/astral-sh/uv)
- **Pandas** pour le traitement des données
- **Plotly** pour la visualisation interactive (Scattermap + Pie)
- **Tailwind CSS** pour le styling (via CDN)
- **GitHub Pages** pour l'hébergement

## Installation et utilisation

### Prérequis

- Python 3.11+
- [UV](https://github.com/astral-sh/uv) (gestionnaire de paquets)

### Installation

```bash
# Cloner le projet
git clone https://github.com/your-username/municipales-2026.git
cd municipales-2026

# Installer les dépendances
uv sync
```

### Génération de la visualisation

```bash
# Télécharger les données et générer le HTML
uv run python scripts/build.py
```

Le fichier `docs/index.html` est généré et peut être ouvert directement dans un navigateur.

### Étapes individuelles

```bash
# Télécharger uniquement les données sources
uv run python src/download.py

# Traiter et fusionner les données
uv run python src/process.py

# Générer la visualisation
uv run python src/visualize.py
```

## Déploiement

Le dossier `docs/` est configuré pour être servi par GitHub Pages :

1. Pousser le code sur GitHub
2. Activer GitHub Pages dans les paramètres du dépôt
3. Sélectionner la branche `main` et le dossier `/docs`

## Mapping des nuances politiques

Source : [Circulaire MI du 2 février 2026 - Annexe 3](https://www.legifrance.gouv.fr/circulaire/id/45645)

| Bloc           | Nuances                         | Couleur |
| -------------- | ------------------------------- | ------- |
| Extrême Gauche | LEXG, LFI                       | #BB0000 |
| Gauche         | LCOM, LSOC, LVEC, LUG, LDVG     | #FF6B6B |
| Divers         | LECO, LREG, LDIV                | #95A5A6 |
| Centre         | LREN, LMDM, LHOR, LUDI, LUC, LDVC | #F39C12 |
| Droite         | LLR, LUD, LDVD, LDSV, LUDR      | #3498DB |
| Extrême Droite | LRN, LREC, LUXD, LEXD           | #1A1A2E |

## Licence

MIT
