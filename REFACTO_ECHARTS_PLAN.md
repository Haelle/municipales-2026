# Plan : Migration Plotly → ECharts

## Contexte

Les graphiques Plotly sont fonctionnels mais impossibles à styler avec Tailwind/shadcn (iframe canvas isolé). Le HTML fait ~89MB à cause de la pré-computation des filtres côté Python. ECharts permet un rendu Canvas/SVG natif, themable, et le filtrage côté JS réduit drastiquement la taille du fichier (~5MB).

## Approche

Remplacer Plotly par ECharts (CDN) + GeoJSON France en fond de carte. Le filtrage passe de Python (pré-calculé) à JavaScript (runtime). Trois instances ECharts séparées (carte + 2 pies) positionnées via Tailwind.

## Fichiers à modifier

### 1. `config.py` — Ajouter l'URL du GeoJSON France
- Ajouter dans `URLS` : `"france_geo"` → GeoJSON départements simplifiés
- Ajouter dans `OUTPUT_FILES` : `"france_geo"` → `RAW_DIR / "france_departements.geojson"`
- Supprimer les clés de `VIZ_CONFIG` spécifiques à Plotly (`map_style`)

### 2. `src/download.py` — Télécharger le GeoJSON
- Ajouter le téléchargement du GeoJSON France dans `download_all()`

### 3. `src/visualize.py` — Réécriture complète
**Supprimer :**
- Imports Plotly (`plotly.graph_objects`, `plotly.subplots`)
- `create_visualization()` (toute la logique Plotly)
- `compute_pie_data()` (sera en JS)
- `create_hover_text()` (sera en JS via tooltip formatter)

**Garder :**
- `compute_marker_size()` (pré-calcul des tailles)
- `SIZE_CATEGORIES` (constantes)

**Ajouter :**
- `prepare_data_json(df)` — Convertit le DataFrame en JSON (arrays parallèles : lon[], lat[], nom[], etc.)
- `generate_filter_html(df)` — Génère les `<select>` HTML avec options triées
- `save_html(df)` — Signature change : prend `df` au lieu de `go.Figure`. Génère le HTML complet avec :
  - ECharts CDN (`<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js">`)
  - GeoJSON France embarqué inline
  - Data JSON embarqué inline
  - JS vanilla (~150 lignes) : init 3 charts, filtrage combiné, mise à jour

**Structure JS embarquée :**
```
const DATA = { communes: { lon[], lat[], nom[], ... }, filters: {...}, blocCouleurs: {...} }
const FRANCE_GEO = { ... }

initCharts()          → 3 instances ECharts (carte geo + 2 pies)
getFilteredIndices()  → boucle sur les communes, applique les 5 filtres combinés
updateCharts()        → reconstruit scatter data + pie data, setOption() sur les 3 charts
```

**Filtres :** 5 `<select>` HTML natifs (Tailwind) au lieu des dropdowns Plotly. Avantage : les filtres se combinent (actuellement avec Plotly le dernier filtre cliqué écrase les autres).

**Carte ECharts :**
- `echarts.registerMap('france', geoJson)`
- Composant `geo` avec `roam: true` (zoom/pan)
- Série `scatter` avec `coordinateSystem: 'geo'`
- `large: true` pour les 34k+ points

**Dark mode :** La fonction `toggleDark()` existante est étendue pour mettre à jour les couleurs ECharts (`geo.itemStyle.areaColor`, fond des pies).

### 4. `scripts/build.py` — Adapter l'appel
```python
# Avant
fig = create_visualization(df)
save_html(fig)

# Après
save_html(df)
```
- Supprimer l'import de `create_visualization`

### 5. `pyproject.toml` — Supprimer Plotly
- Retirer `"plotly>=5.24"` des dependencies

## Ce qui ne change PAS
- La structure HTML (header, footer, légende des blocs, dark mode toggle)
- Le pipeline de données (download → process → CSV)
- `src/colors.py`, `src/process.py`, `src/download.py` (sauf ajout GeoJSON)
- Le déploiement GitHub Pages

## Vérification
1. `uv sync` — vérifier que plotly est bien supprimé
2. `uv run python scripts/build.py` — doit générer `docs/index.html`
3. Ouvrir dans un navigateur : carte visible, points colorés, 5 filtres fonctionnels, 2 pies, dark mode
4. Vérifier la taille du fichier (~5MB vs ~89MB)
5. Tester le zoom/pan sur la carte
6. Tester la combinaison de filtres (ex: Bloc=Gauche + Région=Île-de-France)
