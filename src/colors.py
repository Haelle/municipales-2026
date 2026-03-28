"""Mapping des nuances politiques vers les blocs et couleurs."""

# Définition des blocs politiques avec leurs nuances et couleurs
# Codes officiels des municipales 2026 (préfixe "L" = Liste)
BLOCS = {
    "Extrême Gauche": {
        "nuances": ["LEXG", "LFI"],
        "couleur": "#BB0000",
    },
    "Gauche": {
        "nuances": ["LCOM", "LSOC", "LDVG", "LUG"],
        "couleur": "#FF6B6B",
    },
    "Écologistes": {
        "nuances": ["LECO", "LVEC"],
        "couleur": "#2ECC71",
    },
    "Centre": {
        "nuances": ["LDVC", "LHOR", "LMDM", "LREN", "LUC", "LUDI"],
        "couleur": "#F39C12",
    },
    "Droite": {
        "nuances": ["LDVD", "LLR", "LUD", "LUDR"],
        "couleur": "#3498DB",
    },
    "Extrême Droite": {
        "nuances": ["LEXD", "LRN", "LREC", "LUXD"],
        "couleur": "#1A1A2E",
    },
    "Régionalistes": {
        "nuances": ["LREG"],
        "couleur": "#9B59B6",
    },
    "Divers": {
        "nuances": ["DIV", "LDIV", "LDSV"],
        "couleur": "#95A5A6",
    },
}

# Tableau récapitulatif pour documentation
NUANCES_TABLE = """
| Code  | Signification                    | Bloc           |
|-------|----------------------------------|----------------|
| LEXG  | Liste Extrême Gauche             | Extrême Gauche |
| LFI   | La France Insoumise              | Extrême Gauche |
| LCOM  | Liste Communiste                 | Gauche         |
| LSOC  | Liste Socialiste                 | Gauche         |
| LDVG  | Liste Divers Gauche              | Gauche         |
| LUG   | Liste Union de la Gauche         | Gauche         |
| LECO  | Liste Écologiste                 | Écologistes    |
| LVEC  | Liste Verts Écologistes          | Écologistes    |
| LDVC  | Liste Divers Centre              | Centre         |
| LHOR  | Liste Horizons                   | Centre         |
| LMDM  | Liste Modem                      | Centre         |
| LREN  | Liste Renaissance                | Centre         |
| LUC   | Liste Union du Centre            | Centre         |
| LUDI  | Liste UDI                        | Centre         |
| LDVD  | Liste Divers Droite              | Droite         |
| LLR   | Liste Les Républicains           | Droite         |
| LUD   | Liste Union de la Droite         | Droite         |
| LUDR  | Liste Union Droite et Centre     | Droite         |
| LEXD  | Liste Extrême Droite             | Extrême Droite |
| LRN   | Liste Rassemblement National     | Extrême Droite |
| LREC  | Liste Reconquête                 | Extrême Droite |
| LUXD  | Liste Union Extrême Droite       | Extrême Droite |
| LREG  | Liste Régionaliste               | Régionalistes  |
| DIV   | Divers (sans étiquette)          | Divers         |
| LDIV  | Liste Divers                     | Divers         |
| LDSV  | Liste Divers                     | Divers         |
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
