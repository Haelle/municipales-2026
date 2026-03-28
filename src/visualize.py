"""Génération des visualisations Plotly."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DOCS_DIR, VIZ_CONFIG
from src.colors import BLOC_COULEURS, liste_blocs


# Catégories de taille de commune
SIZE_CATEGORIES = {
    "Petites (< 5k)": {"max_pop": 5000, "size": 5},
    "Moyennes (5k-50k)": {"max_pop": 50000, "size": 10},
    "Grandes (> 50k)": {"max_pop": float("inf"), "size": 20},
}


def compute_marker_size(population: pd.Series) -> np.ndarray:
    """Calcule la taille des marqueurs selon 3 catégories."""
    sizes = np.zeros(len(population))
    sizes[population < 5000] = 5
    sizes[(population >= 5000) & (population < 50000)] = 10
    sizes[population >= 50000] = 20
    return sizes


def compute_pie_data(df_filtered: pd.DataFrame, by_population: bool = False) -> tuple[list, list, list]:
    """Calcule les données du camembert."""
    if by_population:
        bloc_data = df_filtered.groupby("bloc")["population"].sum()
    else:
        bloc_data = df_filtered["bloc"].value_counts()

    blocs_ordre = [b for b in liste_blocs() if b in bloc_data.index]
    bloc_data = bloc_data[blocs_ordre]

    labels = list(bloc_data.index)
    values = [int(v) for v in bloc_data.values]
    colors = [BLOC_COULEURS[b] for b in labels]

    return labels, values, colors


def create_hover_text(row: pd.Series) -> str:
    """Crée le texte de survol pour un point."""
    return (f"<b>{row['nom']}</b><br>"
            f"{row['departement']} ({row['region']})<br>"
            f"Maire: {row['maire']}<br>"
            f"Nuance: {row['nuance']} ({row['bloc']})<br>"
            f"Population: {row['population']:,}<br>"
            f"Tour: {row['tour']}")


def create_visualization(df: pd.DataFrame) -> go.Figure:
    """Crée la visualisation complète avec carte et camemberts."""

    marker_sizes = compute_marker_size(df["population"])

    # Créer la figure avec subplots: carte + 2 camemberts
    fig = make_subplots(
        rows=2, cols=2,
        row_heights=[0.5, 0.5],
        column_widths=[0.72, 0.28],
        specs=[
            [{"type": "map", "rowspan": 2}, {"type": "pie"}],
            [None, {"type": "pie"}]
        ],
        vertical_spacing=0.08,
        horizontal_spacing=0.02,
        subplot_titles=("", "Par nombre de communes", "Par population")
    )

    # === CARTE (trace 0) ===
    fig.add_trace(
        go.Scattermap(
            lat=df["lat"],
            lon=df["lon"],
            mode="markers",
            marker=dict(
                size=marker_sizes,
                color=df["couleur"],
                opacity=VIZ_CONFIG["point_opacity"],
            ),
            text=df.apply(create_hover_text, axis=1),
            hoverinfo="text",
            name="Communes",
        ),
        row=1, col=1
    )

    # === CAMEMBERT COMMUNES (trace 1) ===
    labels_c, values_c, colors_c = compute_pie_data(df, by_population=False)
    total_communes = sum(values_c)

    fig.add_trace(
        go.Pie(
            labels=labels_c,
            values=values_c,
            marker=dict(colors=colors_c),
            textinfo="percent",
            textposition="inside",
            hovertemplate="<b>%{label}</b><br>%{value:,} communes<br>%{percent}<extra></extra>",
            name="Communes",
            title=dict(text=f"<b>{total_communes:,} communes</b>", position="top center", font=dict(size=12)),
        ),
        row=1, col=2
    )

    # === CAMEMBERT POPULATION (trace 2) ===
    labels_p, values_p, colors_p = compute_pie_data(df, by_population=True)
    total_pop = sum(values_p)

    fig.add_trace(
        go.Pie(
            labels=labels_p,
            values=values_p,
            marker=dict(colors=colors_p),
            textinfo="percent",
            textposition="inside",
            hovertemplate="<b>%{label}</b><br>%{value:,} habitants<br>%{percent}<extra></extra>",
            name="Population",
            title=dict(text=f"<b>{total_pop:,} hab.</b>", position="top center", font=dict(size=12)),
        ),
        row=2, col=2
    )

    # === FILTRES INTERACTIFS ===
    blocs_list = ["Tous"] + liste_blocs()
    tours_list = ["Tous", "1er tour", "2nd tour"]
    tailles_list = ["Toutes", "Petites (< 5k)", "Moyennes (5k-50k)", "Grandes (> 50k)"]

    # Régions et départements triés
    regions_list = ["Toutes"] + sorted(df["region"].unique().tolist())
    departements_list = ["Tous"] + sorted(df["departement"].unique().tolist())

    def create_filter_args(mask):
        """Crée les arguments pour mettre à jour les 3 traces."""
        df_filtered = df.loc[mask]
        filtered_sizes = marker_sizes[mask]

        # Camembert communes
        pie_c_labels, pie_c_values, pie_c_colors = compute_pie_data(df_filtered, by_population=False)
        pie_c_total = sum(pie_c_values)

        # Camembert population
        pie_p_labels, pie_p_values, pie_p_colors = compute_pie_data(df_filtered, by_population=True)
        pie_p_total = sum(pie_p_values)

        return [
            {
                "lat": [df_filtered["lat"].tolist(), None, None],
                "lon": [df_filtered["lon"].tolist(), None, None],
                "marker.size": [filtered_sizes.tolist(), None, None],
                "marker.color": [df_filtered["couleur"].tolist(), None, None],
                "marker.colors": [None, pie_c_colors, pie_p_colors],
                "text": [df_filtered.apply(create_hover_text, axis=1).tolist(), None, None],
                "labels": [None, pie_c_labels, pie_p_labels],
                "values": [None, pie_c_values, pie_p_values],
                "title.text": [None, f"<b>{pie_c_total:,} communes</b>", f"<b>{pie_p_total:,} hab.</b>"],
            },
            [0, 1, 2]
        ]

    # Boutons Bloc
    bloc_buttons = []
    for bloc in blocs_list:
        mask = pd.Series([True] * len(df), index=df.index) if bloc == "Tous" else df["bloc"] == bloc
        bloc_buttons.append(dict(args=create_filter_args(mask), label=bloc, method="restyle"))

    # Boutons Tour
    tour_buttons = []
    for tour in tours_list:
        if tour == "Tous":
            mask = pd.Series([True] * len(df), index=df.index)
        elif tour == "1er tour":
            mask = df["tour"] == 1
        else:
            mask = df["tour"] == 2
        tour_buttons.append(dict(args=create_filter_args(mask), label=tour, method="restyle"))

    # Boutons Taille
    taille_buttons = []
    for taille in tailles_list:
        if taille == "Toutes":
            mask = pd.Series([True] * len(df), index=df.index)
        elif taille == "Petites (< 5k)":
            mask = df["population"] < 5000
        elif taille == "Moyennes (5k-50k)":
            mask = (df["population"] >= 5000) & (df["population"] < 50000)
        else:
            mask = df["population"] >= 50000
        taille_buttons.append(dict(args=create_filter_args(mask), label=taille, method="restyle"))

    # Boutons Région
    region_buttons = []
    for region in regions_list:
        mask = pd.Series([True] * len(df), index=df.index) if region == "Toutes" else df["region"] == region
        region_buttons.append(dict(args=create_filter_args(mask), label=region, method="restyle"))

    # Boutons Département
    dept_buttons = []
    for dept in departements_list:
        mask = pd.Series([True] * len(df), index=df.index) if dept == "Tous" else df["departement"] == dept
        dept_buttons.append(dict(args=create_filter_args(mask), label=dept, method="restyle"))

    # === LAYOUT ===
    fig.update_layout(
        title=dict(
            text="<b>Élections Municipales 2026</b> - Maires élus par commune",
            x=0.5,
            y=0.98,
            font=dict(size=20),
        ),
        showlegend=False,

        map=dict(
            style=VIZ_CONFIG["map_style"],
            center=VIZ_CONFIG["map_center"],
            zoom=VIZ_CONFIG["map_zoom"],
        ),

        updatemenus=[
            dict(
                buttons=bloc_buttons, direction="down", showactive=True, active=0,
                x=0.07, xanchor="left", y=0.99, yanchor="top",
                bgcolor="white", bordercolor="#666", borderwidth=1, font=dict(size=10),
            ),
            dict(
                buttons=tour_buttons, direction="down", showactive=True, active=0,
                x=0.195, xanchor="left", y=0.99, yanchor="top",
                bgcolor="white", bordercolor="#666", borderwidth=1, font=dict(size=10),
            ),
            dict(
                buttons=taille_buttons, direction="down", showactive=True, active=0,
                x=0.30, xanchor="left", y=0.99, yanchor="top",
                bgcolor="white", bordercolor="#666", borderwidth=1, font=dict(size=10),
            ),
            dict(
                buttons=region_buttons, direction="down", showactive=True, active=0,
                x=0.44, xanchor="left", y=0.99, yanchor="top",
                bgcolor="white", bordercolor="#666", borderwidth=1, font=dict(size=10),
            ),
            dict(
                buttons=dept_buttons, direction="down", showactive=True, active=0,
                x=0.58, xanchor="left", y=0.99, yanchor="top",
                bgcolor="white", bordercolor="#666", borderwidth=1, font=dict(size=10),
            ),
        ],

        annotations=[
            dict(text="<b>Bloc</b>", x=0.0, xref="paper", y=0.985, yref="paper", showarrow=False, font=dict(size=10)),
            dict(text="<b>Tour</b>", x=0.14, xref="paper", y=0.985, yref="paper", showarrow=False, font=dict(size=10)),
            dict(text="<b>Taille</b>", x=0.255, xref="paper", y=0.985, yref="paper", showarrow=False, font=dict(size=10)),
            dict(text="<b>Région</b>", x=0.385, xref="paper", y=0.985, yref="paper", showarrow=False, font=dict(size=10)),
            dict(text="<b>Dépt.</b>", x=0.53, xref="paper", y=0.985, yref="paper", showarrow=False, font=dict(size=10)),
        ],

        margin=dict(l=10, r=10, t=50, b=10),
        height=800,
        autosize=True,
    )

    return fig


def save_html(fig: go.Figure, output_path: Path | None = None) -> Path:
    """Exporte la visualisation en HTML avec tableau des nuances."""
    if output_path is None:
        output_path = DOCS_DIR / "index.html"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    config = {
        "responsive": True,
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        "displaylogo": False,
        "scrollZoom": True,
    }

    plotly_html = fig.to_html(include_plotlyjs="cdn", full_html=False, config=config)

    full_html = f"""<!DOCTYPE html>
<html lang="fr" class="light">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Élections Municipales 2026 - Carte interactive</title>
    <script src="https://cdn.tailwindcss.com"></script>
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
        <!-- Map container with shadow -->
        <div class="rounded-2xl overflow-hidden shadow-xl border border-border/50 bg-card">
            <div id="plotly-container" class="w-full">
                {plotly_html}
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
                <div class="rounded-xl border border-border/50 overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-card">
                    <div class="px-3 py-2.5 font-semibold text-white" style="background: linear-gradient(135deg, #BB0000 0%, #8B0000 100%)">Extrême Gauche</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LEXG · Extrême Gauche</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LFI · France Insoumise</div>
                </div>
                <div class="rounded-xl border border-border/50 overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-card">
                    <div class="px-3 py-2.5 font-semibold text-white" style="background: linear-gradient(135deg, #FF6B6B 0%, #ee5a5a 100%)">Gauche</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LCOM · Communiste</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LSOC · Socialiste</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LDVG · Divers Gauche</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LUG · Union Gauche</div>
                </div>
                <div class="rounded-xl border border-border/50 overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-card">
                    <div class="px-3 py-2.5 font-semibold text-white" style="background: linear-gradient(135deg, #2ECC71 0%, #27ae60 100%)">Écologistes</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LECO · Écologiste</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LVEC · Verts</div>
                </div>
                <div class="rounded-xl border border-border/50 overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-card">
                    <div class="px-3 py-2.5 font-semibold text-white" style="background: linear-gradient(135deg, #F39C12 0%, #d68910 100%)">Centre</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LDVC · Divers Centre</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LHOR · Horizons</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LMDM · MoDem</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LREN · Renaissance</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LUC · Union Centre</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LUDI · UDI</div>
                </div>
                <div class="rounded-xl border border-border/50 overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-card">
                    <div class="px-3 py-2.5 font-semibold text-white" style="background: linear-gradient(135deg, #3498DB 0%, #2980b9 100%)">Droite</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LDVD · Divers Droite</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LLR · Les Républicains</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LUD · Union Droite</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LUDR · Union DR/Centre</div>
                </div>
                <div class="rounded-xl border border-border/50 overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-card">
                    <div class="px-3 py-2.5 font-semibold text-white" style="background: linear-gradient(135deg, #1A1A2E 0%, #0f0f1a 100%)">Extrême Droite</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LEXD · Extrême Droite</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LRN · Rass. National</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LREC · Reconquête</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LUXD · Union Ext. DR</div>
                </div>
                <div class="rounded-xl border border-border/50 overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-card">
                    <div class="px-3 py-2.5 font-semibold text-white" style="background: linear-gradient(135deg, #9B59B6 0%, #8e44ad 100%)">Régionalistes</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LREG · Régionaliste</div>
                </div>
                <div class="rounded-xl border border-border/50 overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-card">
                    <div class="px-3 py-2.5 font-semibold text-white" style="background: linear-gradient(135deg, #95A5A6 0%, #7f8c8d 100%)">Divers</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">DIV · Sans étiquette</div>
                    <div class="px-3 py-1.5 border-t border-border/50 text-muted-foreground">LDIV · Liste Divers</div>
                </div>
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

    fig = create_visualization(df)
    save_html(fig)

    print("\n=== Terminé ===")
