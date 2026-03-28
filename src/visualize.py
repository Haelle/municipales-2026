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
                "marker.color": [df_filtered["couleur"].tolist(), pie_c_colors, pie_p_colors],
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
                x=0.10, xanchor="left", y=0.99, yanchor="top",
                bgcolor="white", bordercolor="#666", borderwidth=1, font=dict(size=11),
            ),
            dict(
                buttons=tour_buttons, direction="down", showactive=True, active=0,
                x=0.27, xanchor="left", y=0.99, yanchor="top",
                bgcolor="white", bordercolor="#666", borderwidth=1, font=dict(size=11),
            ),
            dict(
                buttons=taille_buttons, direction="down", showactive=True, active=0,
                x=0.42, xanchor="left", y=0.99, yanchor="top",
                bgcolor="white", bordercolor="#666", borderwidth=1, font=dict(size=11),
            ),
        ],

        annotations=[
            dict(text="<b>Bloc:</b>", x=0.01, xref="paper", y=0.985, yref="paper", showarrow=False, font=dict(size=12)),
            dict(text="<b>Tour:</b>", x=0.20, xref="paper", y=0.985, yref="paper", showarrow=False, font=dict(size=12)),
            dict(text="<b>Taille:</b>", x=0.36, xref="paper", y=0.985, yref="paper", showarrow=False, font=dict(size=12)),
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
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{
                        border: "hsl(var(--border))",
                        background: "hsl(var(--background))",
                        foreground: "hsl(var(--foreground))",
                        card: "hsl(var(--card))",
                        muted: "hsl(var(--muted))",
                    }}
                }}
            }}
        }}
    </script>
    <style>
        :root {{
            --background: 0 0% 100%;
            --foreground: 222.2 84% 4.9%;
            --card: 0 0% 100%;
            --border: 214.3 31.8% 91.4%;
            --muted: 210 40% 96%;
        }}
        .dark {{
            --background: 222.2 84% 4.9%;
            --foreground: 210 40% 98%;
            --card: 222.2 84% 4.9%;
            --border: 217.2 32.6% 17.5%;
            --muted: 217.2 32.6% 17.5%;
        }}
        .bw .js-plotly-plot .scattermapbox .point {{
            filter: grayscale(100%) !important;
        }}
        .bw table tr:first-child {{
            filter: grayscale(100%) !important;
        }}
        .bw .slice {{
            filter: grayscale(100%) !important;
        }}
    </style>
</head>
<body class="bg-background text-foreground min-h-screen">
    <!-- Header -->
    <header class="border-b border-border bg-card">
        <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <h1 class="text-xl font-semibold tracking-tight">Élections Municipales 2026</h1>
            <div class="flex items-center gap-3">
                <button id="bwToggle" onclick="toggleBW()" class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 border border-border bg-background hover:bg-muted h-9 px-3">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mr-2"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 0 0 20z"/></svg>
                    Noir & Blanc
                </button>
                <button onclick="toggleDark()" class="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 border border-border bg-background hover:bg-muted h-9 w-9">
                    <svg id="sunIcon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>
                    <svg id="moonIcon" class="hidden" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>
                </button>
            </div>
        </div>
    </header>

    <!-- Main content -->
    <main class="max-w-7xl mx-auto">
        <div id="plotly-container" class="w-full">
            {plotly_html}
        </div>

        <!-- Legend -->
        <div class="px-4 py-6 border-t border-border">
            <h2 class="text-lg font-semibold text-center mb-4">Correspondance Nuances → Blocs politiques</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3 text-xs">
                <div class="rounded-lg border border-border overflow-hidden">
                    <div class="px-3 py-2 font-medium text-white" style="background:#BB0000">Extrême Gauche</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LEXG - Extrême Gauche</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LFI - France Insoumise</div>
                </div>
                <div class="rounded-lg border border-border overflow-hidden">
                    <div class="px-3 py-2 font-medium text-white" style="background:#FF6B6B">Gauche</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LCOM - Communiste</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LSOC - Socialiste</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LDVG - Divers Gauche</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LUG - Union Gauche</div>
                </div>
                <div class="rounded-lg border border-border overflow-hidden">
                    <div class="px-3 py-2 font-medium text-white" style="background:#2ECC71">Écologistes</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LECO - Écologiste</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LVEC - Verts</div>
                </div>
                <div class="rounded-lg border border-border overflow-hidden">
                    <div class="px-3 py-2 font-medium text-white" style="background:#F39C12">Centre</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LDVC - Divers Centre</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LHOR - Horizons</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LMDM - MoDem</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LREN - Renaissance</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LUC - Union Centre</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LUDI - UDI</div>
                </div>
                <div class="rounded-lg border border-border overflow-hidden">
                    <div class="px-3 py-2 font-medium text-white" style="background:#3498DB">Droite</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LDVD - Divers Droite</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LLR - Les Républicains</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LUD - Union Droite</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LUDR - Union DR/Centre</div>
                </div>
                <div class="rounded-lg border border-border overflow-hidden">
                    <div class="px-3 py-2 font-medium text-white" style="background:#1A1A2E">Extrême Droite</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LEXD - Extrême Droite</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LRN - Rass. National</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LREC - Reconquête</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LUXD - Union Ext. DR</div>
                </div>
                <div class="rounded-lg border border-border overflow-hidden">
                    <div class="px-3 py-2 font-medium text-white" style="background:#9B59B6">Régionalistes</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LREG - Régionaliste</div>
                </div>
                <div class="rounded-lg border border-border overflow-hidden">
                    <div class="px-3 py-2 font-medium text-white" style="background:#95A5A6">Divers</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">DIV - Sans étiquette</div>
                    <div class="px-3 py-1.5 bg-card border-t border-border">LDIV - Liste Divers</div>
                </div>
            </div>

            <div class="mt-4 flex items-center justify-center gap-6 text-sm text-muted-foreground">
                <span class="flex items-center gap-2">
                    <span class="inline-block w-2 h-2 rounded-full bg-gray-400"></span>
                    &lt;5k hab.
                </span>
                <span class="flex items-center gap-2">
                    <span class="inline-block w-3 h-3 rounded-full bg-gray-400"></span>
                    5k-50k hab.
                </span>
                <span class="flex items-center gap-2">
                    <span class="inline-block w-4 h-4 rounded-full bg-gray-400"></span>
                    &gt;50k hab.
                </span>
            </div>
        </div>
    </main>

    <!-- Footer -->
    <footer class="border-t border-border py-4">
        <div class="max-w-7xl mx-auto px-4 text-center text-sm text-muted-foreground">
            Source: <a href="https://www.data.gouv.fr/datasets/elections-municipales-2026-resultats-du-premier-tour" class="underline hover:text-foreground">data.gouv.fr</a>
            · Données du 28 mars 2026
        </div>
    </footer>

    <script>
        function toggleDark() {{
            document.documentElement.classList.toggle('dark');
            document.getElementById('sunIcon').classList.toggle('hidden');
            document.getElementById('moonIcon').classList.toggle('hidden');
        }}
        function toggleBW() {{
            document.body.classList.toggle('bw');
            const btn = document.getElementById('bwToggle');
            if (document.body.classList.contains('bw')) {{
                btn.classList.add('bg-foreground', 'text-background');
                btn.classList.remove('bg-background');
            }} else {{
                btn.classList.remove('bg-foreground', 'text-background');
                btn.classList.add('bg-background');
            }}
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
