"""Génération de la visualisation ECharts."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DOCS_DIR, OUTPUT_FILES, VIZ_CONFIG
from src.colors import BLOC_COULEURS, BLOCS, liste_blocs

# Catégories de taille de commune
SIZE_CATEGORIES = {
    "Petites (< 5k)": {"max_pop": 5000, "size": 5},
    "Moyennes (5k-50k)": {"max_pop": 50000, "size": 10},
    "Grandes (> 50k)": {"max_pop": float("inf"), "size": 20},
}


def compute_marker_size(population: pd.Series) -> np.ndarray:
    """Calcule la taille des marqueurs selon 3 catégories."""
    sizes = np.zeros(len(population))
    sizes[population < 5000] = 3
    sizes[(population >= 5000) & (population < 50000)] = 8
    sizes[population >= 50000] = 16
    return sizes


def prepare_data_json(df: pd.DataFrame) -> str:
    """Convertit le DataFrame en JSON pour ECharts (arrays parallèles)."""
    sizes = compute_marker_size(df["population"])

    data = {
        "communes": {
            "lon": df["lon"].round(4).tolist(),
            "lat": df["lat"].round(4).tolist(),
            "nom": df["nom"].tolist(),
            "maire": df["maire"].tolist(),
            "nuance": df["nuance"].tolist(),
            "bloc": df["bloc"].tolist(),
            "couleur": df["couleur"].tolist(),
            "tour": df["tour"].astype(int).tolist(),
            "population": df["population"].astype(int).tolist(),
            "departement": df["departement"].tolist(),
            "region": df["region"].tolist(),
            "size": sizes.astype(int).tolist(),
        },
        "filters": {
            "blocs": liste_blocs(),
            "regions": sorted(df["region"].unique().tolist()),
            "departements": sorted(df["departement"].unique().tolist()),
        },
        "blocCouleurs": BLOC_COULEURS,
    }

    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def generate_filter_html(df: pd.DataFrame) -> str:
    """Génère les <select> HTML pour les filtres."""
    blocs = liste_blocs()
    regions = sorted(df["region"].unique().tolist())
    departements = sorted(df["departement"].unique().tolist())

    def options(items, all_label="Tous"):
        opts = f'<option value="">{all_label}</option>\n'
        for item in items:
            opts += f'                        <option value="{item}">{item}</option>\n'
        return opts

    select_class = (
        "block w-full rounded-lg border border-border/50 bg-card px-3 py-2 text-sm "
        "shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50 "
        "dark:bg-gray-800 dark:border-gray-700"
    )

    return f"""
        <div class="flex flex-wrap gap-4 mb-4">
            <label class="flex flex-col gap-1 text-sm font-medium text-muted-foreground">
                <span>Bloc</span>
                <select id="filter-bloc" class="{select_class}" onchange="updateCharts()">
                    {options(blocs)}
                </select>
            </label>
            <label class="flex flex-col gap-1 text-sm font-medium text-muted-foreground">
                <span>Tour</span>
                <select id="filter-tour" class="{select_class}" onchange="updateCharts()">
                    <option value="">Tous</option>
                    <option value="1">1er tour</option>
                    <option value="2">2nd tour</option>
                </select>
            </label>
            <label class="flex flex-col gap-1 text-sm font-medium text-muted-foreground">
                <span>Taille</span>
                <select id="filter-taille" class="{select_class}" onchange="updateCharts()">
                    <option value="">Toutes</option>
                    <option value="small">&lt; 5 000 hab.</option>
                    <option value="medium">5k - 50k hab.</option>
                    <option value="large">&gt; 50 000 hab.</option>
                </select>
            </label>
            <label class="flex flex-col gap-1 text-sm font-medium text-muted-foreground">
                <span>Région</span>
                <select id="filter-region" class="{select_class}" onchange="updateCharts()">
                    {options(regions, "Toutes")}
                </select>
            </label>
            <label class="flex flex-col gap-1 text-sm font-medium text-muted-foreground">
                <span>Département</span>
                <select id="filter-dept" class="{select_class}" onchange="updateCharts()">
                    {options(departements)}
                </select>
            </label>
        </div>"""


ECHART_JS = """
    echarts.registerMap('france', FRANCE_GEO);

    const mapChart = echarts.init(document.getElementById('map-chart'));
    const pieCommunes = echarts.init(document.getElementById('pie-communes'));
    const piePopulation = echarts.init(document.getElementById('pie-population'));

    function getFilteredIndices() {
        const bloc = document.getElementById('filter-bloc').value;
        const tour = document.getElementById('filter-tour').value;
        const taille = document.getElementById('filter-taille').value;
        const region = document.getElementById('filter-region').value;
        const dept = document.getElementById('filter-dept').value;

        const indices = [];
        const c = DATA.communes;
        const n = c.lon.length;

        for (let i = 0; i < n; i++) {
            if (bloc && c.bloc[i] !== bloc) continue;
            if (tour && c.tour[i] !== parseInt(tour)) continue;
            if (region && c.region[i] !== region) continue;
            if (dept && c.departement[i] !== dept) continue;
            if (taille) {
                const pop = c.population[i];
                if (taille === 'small' && pop >= 5000) continue;
                if (taille === 'medium' && (pop < 5000 || pop >= 50000)) continue;
                if (taille === 'large' && pop < 50000) continue;
            }
            indices.push(i);
        }
        return indices;
    }

    function buildPieData(indices, byPopulation) {
        const counts = {};
        const c = DATA.communes;
        for (const i of indices) {
            const b = c.bloc[i];
            counts[b] = (counts[b] || 0) + (byPopulation ? c.population[i] : 1);
        }
        return DATA.filters.blocs
            .filter(b => counts[b])
            .map(b => ({ name: b, value: counts[b], itemStyle: { color: DATA.blocCouleurs[b] } }));
    }

    function updateCharts() {
        const indices = getFilteredIndices();
        const c = DATA.communes;

        // Scatter data
        const scatterData = indices.map(i => ({
            value: [c.lon[i], c.lat[i]],
            symbolSize: c.size[i],
            itemStyle: { color: c.couleur[i] },
            _idx: i,
        }));

        mapChart.setOption({
            series: [{ data: scatterData }]
        });

        // Pies
        const pieDataCommunes = buildPieData(indices, false);
        const totalCommunes = pieDataCommunes.reduce((s, d) => s + d.value, 0);
        pieCommunes.setOption({
            title: { text: totalCommunes.toLocaleString('fr-FR') + ' communes' },
            series: [{ data: pieDataCommunes }]
        });

        const pieDataPop = buildPieData(indices, true);
        const totalPop = pieDataPop.reduce((s, d) => s + d.value, 0);
        piePopulation.setOption({
            title: { text: totalPop.toLocaleString('fr-FR') + ' hab.' },
            series: [{ data: pieDataPop }]
        });
    }

    // Dark mode colors
    const geoLight = { areaColor: '#f3f4f6', borderColor: '#d1d5db', emphasis: { areaColor: '#e5e7eb' } };
    const geoDark = { areaColor: '#1f2937', borderColor: '#374151', emphasis: { areaColor: '#374151' } };

    function isDark() { return document.documentElement.classList.contains('dark'); }

    function getGeoStyle() { return isDark() ? geoDark : geoLight; }
    function getTextColor() { return isDark() ? '#e5e7eb' : '#374151'; }

    // Map options
    mapChart.setOption({
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'item',
            formatter: function(p) {
                if (!p.data || p.data._idx === undefined) return '';
                const i = p.data._idx;
                const c = DATA.communes;
                return '<b>' + c.nom[i] + '</b><br>'
                    + c.departement[i] + ' (' + c.region[i] + ')<br>'
                    + 'Maire: ' + c.maire[i] + '<br>'
                    + 'Nuance: ' + c.nuance[i] + ' (' + c.bloc[i] + ')<br>'
                    + 'Population: ' + c.population[i].toLocaleString('fr-FR') + '<br>'
                    + 'Tour: ' + c.tour[i];
            }
        },
        geo: {
            map: 'france',
            roam: true,
            zoom: VIZCONFIG.zoom,
            center: [VIZCONFIG.center.lon, VIZCONFIG.center.lat],
            itemStyle: getGeoStyle(),
            emphasis: { itemStyle: { areaColor: getGeoStyle().emphasis.areaColor } },
            label: { show: false },
        },
        series: [{
            type: 'scatter',
            coordinateSystem: 'geo',
            data: [],
        }]
    });

    // Pie options (shared)
    function pieOption(title) {
        return {
            backgroundColor: 'transparent',
            title: {
                text: title,
                left: 'center', top: 10,
                textStyle: { fontSize: 13, fontWeight: 600, color: getTextColor() }
            },
            tooltip: {
                trigger: 'item',
                formatter: '{b}: {c} ({d}%)'
            },
            series: [{
                type: 'pie',
                radius: ['30%', '70%'],
                center: ['50%', '55%'],
                label: { show: false },
                emphasis: {
                    label: { show: true, fontWeight: 'bold' }
                },
                data: [],
            }]
        };
    }

    pieCommunes.setOption(pieOption(''));
    piePopulation.setOption(pieOption(''));

    // Initial render
    updateCharts();

    // Resize
    window.addEventListener('resize', () => {
        mapChart.resize();
        pieCommunes.resize();
        piePopulation.resize();
    });

    // Dark mode update for charts
    const origToggle = window.toggleDark;
    window.toggleDark = function() {
        origToggle();
        const style = getGeoStyle();
        mapChart.setOption({
            geo: { itemStyle: style, emphasis: { itemStyle: { areaColor: style.emphasis.areaColor } } }
        });
        pieCommunes.setOption({ title: { textStyle: { color: getTextColor() } } });
        piePopulation.setOption({ title: { textStyle: { color: getTextColor() } } });
    };
"""


def save_html(df: pd.DataFrame, output_path: Path | None = None) -> Path:
    """Exporte la visualisation ECharts en HTML."""
    if output_path is None:
        output_path = DOCS_DIR / "index.html"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    data_json = prepare_data_json(df)

    # Charger le GeoJSON France
    geo_path = OUTPUT_FILES["france_geo"]
    with open(geo_path, "r", encoding="utf-8") as f:
        france_geo_json = f.read()

    viz_config_json = json.dumps({
        "center": VIZ_CONFIG["map_center"],
        "zoom": VIZ_CONFIG["map_zoom"],
        "opacity": VIZ_CONFIG["point_opacity"],
    })

    filter_html = generate_filter_html(df)

    # Légende des blocs
    legend_cards = ""
    for bloc, config in BLOCS.items():
        couleur = config["couleur"]
        nuances_html = ""
        for nuance in config["nuances"]:
            nuances_html += f'<div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">{nuance}</div>\n'
        legend_cards += f"""
                <div class="rounded-xl border border-border/50 overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-card">
                    <div class="px-3 py-2.5 font-semibold text-white" style="background: linear-gradient(135deg, {couleur} 0%, {couleur}cc 100%)">{bloc}</div>
                    {nuances_html}
                </div>"""

    full_html = f"""<!DOCTYPE html>
<html lang="fr" class="light">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Élections Municipales 2026 - Carte interactive</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    fontFamily: {{
                        sans: ['Inter', 'system-ui', 'sans-serif'],
                    }},
                    colors: {{
                        border: "hsl(var(--border))",
                        background: "hsl(var(--background))",
                        foreground: "hsl(var(--foreground))",
                        card: "hsl(var(--card))",
                        muted: "hsl(var(--muted))",
                        accent: "hsl(var(--accent))",
                    }}
                }}
            }}
        }}
    </script>
    <style>
        :root {{
            --background: 0 0% 98%;
            --foreground: 240 10% 3.9%;
            --card: 0 0% 100%;
            --border: 240 5.9% 90%;
            --muted: 240 4.8% 95.9%;
            --accent: 240 4.8% 95.9%;
        }}
        .dark {{
            --background: 240 10% 3.9%;
            --foreground: 0 0% 98%;
            --card: 240 10% 5.9%;
            --border: 240 3.7% 15.9%;
            --muted: 240 3.7% 15.9%;
            --accent: 240 3.7% 20%;
        }}
        body {{ font-family: 'Inter', system-ui, sans-serif; }}
        .glass {{
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
        }}
        .dark .glass {{
            background: rgba(15, 15, 20, 0.8);
        }}
        .gradient-border {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1px;
        }}
        .gradient-text {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
    </style>
</head>
<body class="bg-background text-foreground min-h-screen">
    <!-- Header -->
    <header class="glass sticky top-0 z-50 border-b border-border/50">
        <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl gradient-border flex items-center justify-center">
                    <div class="w-full h-full rounded-xl bg-card flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="url(#grad)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <defs><linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#667eea"/><stop offset="100%" style="stop-color:#764ba2"/></linearGradient></defs>
                            <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>
                        </svg>
                    </div>
                </div>
                <div>
                    <h1 class="text-xl font-bold tracking-tight">Municipales <span class="gradient-text">2026</span></h1>
                    <p class="text-xs text-muted-foreground">Carte interactive des maires élus</p>
                </div>
            </div>
            <button onclick="toggleDark()" class="group relative inline-flex items-center justify-center rounded-xl text-sm font-medium transition-all duration-200 border border-border/50 bg-card hover:bg-accent h-10 w-10 shadow-sm hover:shadow-md">
                <svg id="sunIcon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="transition-transform group-hover:rotate-45"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>
                <svg id="moonIcon" class="hidden transition-transform group-hover:-rotate-12" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
            </button>
        </div>
    </header>

    <!-- Main content -->
    <main class="max-w-7xl mx-auto px-4 py-6">
        <!-- Filters -->
        {filter_html}

        <!-- Charts container -->
        <div class="rounded-2xl overflow-hidden shadow-xl border border-border/50 bg-card">
            <div class="flex flex-col lg:flex-row">
                <div id="map-chart" class="w-full lg:w-[72%]" style="height:700px"></div>
                <div class="w-full lg:w-[28%] flex flex-col border-l border-border/50">
                    <div id="pie-communes" class="flex-1" style="min-height:300px"></div>
                    <div id="pie-population" class="flex-1 border-t border-border/50" style="min-height:300px"></div>
                </div>
            </div>
        </div>

        <!-- Legend -->
        <div class="mt-8 mb-6">
            <div class="flex items-center gap-3 mb-5">
                <div class="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent"></div>
                <h2 class="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Légende des nuances</h2>
                <div class="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent"></div>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3 text-xs">
                {legend_cards}
            </div>

            <!-- Size legend -->
            <div class="mt-6 flex items-center justify-center gap-8 text-sm">
                <div class="flex items-center gap-6 px-6 py-3 rounded-full bg-muted/50 border border-border/50">
                    <span class="flex items-center gap-2 text-muted-foreground">
                        <span class="inline-block w-2 h-2 rounded-full bg-gradient-to-br from-gray-400 to-gray-500 shadow-sm"></span>
                        &lt;5k hab.
                    </span>
                    <span class="flex items-center gap-2 text-muted-foreground">
                        <span class="inline-block w-3 h-3 rounded-full bg-gradient-to-br from-gray-400 to-gray-500 shadow-sm"></span>
                        5k-50k hab.
                    </span>
                    <span class="flex items-center gap-2 text-muted-foreground">
                        <span class="inline-block w-4 h-4 rounded-full bg-gradient-to-br from-gray-400 to-gray-500 shadow-sm"></span>
                        &gt;50k hab.
                    </span>
                </div>
            </div>
        </div>
    </main>

    <!-- Footer -->
    <footer class="border-t border-border/50 py-6 mt-8">
        <div class="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
            <div class="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/><path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M10 6h8v4h-8V6Z"/></svg>
                Source: <a href="https://www.data.gouv.fr/datasets/elections-municipales-2026-resultats-du-premier-tour" class="underline hover:text-foreground transition-colors">data.gouv.fr</a>
            </div>
            <div class="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>
                Données du 28 mars 2026
            </div>
        </div>
    </footer>

    <script>
        function toggleDark() {{
            document.documentElement.classList.toggle('dark');
            document.getElementById('sunIcon').classList.toggle('hidden');
            document.getElementById('moonIcon').classList.toggle('hidden');
        }}
    </script>

    <script>
        const DATA = {data_json};
        const FRANCE_GEO = {france_geo_json};
        const VIZCONFIG = {viz_config_json};

        {ECHART_JS}
    </script>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"  Visualisation exportée: {output_path}")
    return output_path


if __name__ == "__main__":
    from src.process import process_data

    print("=== Génération de la visualisation ===\n")
    df = process_data()
    print(f"  Données: {len(df)} communes\n")

    save_html(df)

    print("\n=== Terminé ===")
