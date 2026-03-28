"""Mapping des nuances politiques vers les blocs et couleurs."""

# Définition des blocs politiques avec leurs nuances et couleurs
# Source: Circulaire MI - Légifrance https://www.legifrance.gouv.fr/circulaire/id/45645
# Référentiel: https://www.resultats-elections.interieur.gouv.fr/municipales2026/referentiel.html
BLOCS = {
    "Extrême Gauche": {
        "nuances": ["LEXG", "LFI"],
        "couleur": "#BB0000",
    },
    "Gauche": {
        "nuances": ["LCOM", "LSOC", "LVEC", "LUG", "LDVG", "LECO", "LREG"],
        "couleur": "#FF6B6B",
    },
    "Centre": {
        "nuances": ["LREN", "LMDM", "LHOR", "LUDI", "LUC", "LDVC"],
        "couleur": "#F39C12",
    },
    "Droite": {
        "nuances": ["LLR", "LUD", "LDVD", "LDSV", "LUDR"],
        "couleur": "#3498DB",
    },
    "Extrême Droite": {
        "nuances": ["LRN", "LREC", "LUXD", "LEXD"],
        "couleur": "#1A1A2E",
    },
    "Divers": {
        "nuances": ["LDIV", "DIV"],
        "couleur": "#95A5A6",
    },
}

# Tableau récapitulatif pour documentation
# Source: Référentiel MI https://www.resultats-elections.interieur.gouv.fr/municipales2026/referentiel.html
NUANCES_TABLE = """
| Code  | Signification                         | Bloc           |
|-------|---------------------------------------|----------------|
| LEXG  | Liste d'extrême-gauche                | Extrême Gauche |
| LFI   | Liste La France Insoumise             | Extrême Gauche |
| LCOM  | Liste Parti communiste français       | Gauche         |
| LSOC  | Liste Parti socialiste                | Gauche         |
| LVEC  | Liste Les Écologistes                 | Gauche         |
| LUG   | Liste d'union à gauche                | Gauche         |
| LDVG  | Liste divers gauche                   | Gauche         |
| LECO  | Liste écologiste                      | Gauche         |
| LREG  | Liste régionaliste                    | Gauche         |
| LREN  | Liste Renaissance                     | Centre         |
| LMDM  | Liste Mouvement démocrate (MoDem)     | Centre         |
| LHOR  | Liste Horizons                        | Centre         |
| LUDI  | Liste Union des Démocrates et Indép.  | Centre         |
| LUC   | Liste d'union au centre               | Centre         |
| LDVC  | Liste divers centre                   | Centre         |
| LLR   | Liste Les Républicains                | Droite         |
| LUD   | Liste d'union à droite                | Droite         |
| LDVD  | Liste divers droite                   | Droite         |
| LDSV  | Liste droite souverainiste            | Droite         |
| LUDR  | Liste union des droites pour la Rép.  | Droite         |
| LRN   | Liste Rassemblement National          | Extrême Droite |
| LREC  | Liste Reconquête !                    | Extrême Droite |
| LUXD  | Liste d'union à l'extrême-droite      | Extrême Droite |
| LEXD  | Liste d'extrême droite                | Extrême Droite |
| LDIV  | Liste Divers                          | Divers         |
"""

# Couleur par défaut pour les nuances inconnues
COULEUR_DEFAUT = "#95A5A6"

# Construction des mappings inversés
NUANCE_TO_BLOC = {}
NUANCE_TO_COULEUR = {}

for bloc, config in BLOCS.items():
    for nuance in config["nuances"]:
        NUANCE_TO_BLOC[nuance] = bloc
        NUANCE_TO_COULEUR[nuance] = config["couleur"]

# Couleurs des blocs (pour le camembert)
BLOC_COULEURS = {bloc: config["couleur"] for bloc, config in BLOCS.items()}


def get_bloc(nuance: str | None) -> str:
    """Retourne le bloc politique correspondant à une nuance."""
    if nuance is None or (isinstance(nuance, float) and nuance != nuance):
        return "Divers"
    return NUANCE_TO_BLOC.get(str(nuance), "Divers")


def get_couleur(nuance: str | None) -> str:
    """Retourne la couleur correspondant à une nuance."""
    if nuance is None or (isinstance(nuance, float) and nuance != nuance):
        return COULEUR_DEFAUT
    return NUANCE_TO_COULEUR.get(str(nuance), COULEUR_DEFAUT)


def get_bloc_couleur(bloc: str) -> str:
    """Retourne la couleur d'un bloc politique."""
    return BLOC_COULEURS.get(bloc, COULEUR_DEFAUT)


def liste_blocs() -> list[str]:
    """Retourne la liste des blocs politiques."""
    return list(BLOCS.keys())


def liste_nuances() -> list[str]:
    """Retourne la liste de toutes les nuances connues."""
    return list(NUANCE_TO_BLOC.keys())


def print_table():
    """Affiche le tableau des correspondances."""
    print(NUANCES_TABLE)
