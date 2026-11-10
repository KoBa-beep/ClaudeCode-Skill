# Icônes IDBS Polar — dossiers de l'arborescence

21 icônes SVG 40×40 px (fond transparent, sans police externe sauf le « 31 » de MONTH en Arial) pour les types de dossiers de l'arborescence Polar.

![Aperçu](preview.png)

| Type Polar | Fichier | Idée |
|---|---|---|
| ROOT | `svg/root.svg` | Globe — racine du système |
| GROUP | `svg/group.svg` | Dossier rouge, équipe |
| CATEGORY | `svg/category.svg` | Dossier rouge clair, étiquette |
| COLLABORATION_IDBS | `svg/collaboration_idbs.svg` | Dossier vert canard, cercles entrelacés |
| PROJECT | `svg/project.svg` | Dossier ardoise, mallette |
| USER | `svg/user.svg` | Dossier orange, personne |
| SHARED_GROUP | `svg/shared_group.svg` | Dossier vert, personnes + partage |
| WEB_SEARCH | `svg/web_search.svg` | Dossier bleu, loupe/web |
| TEMPLATES_FOLDER | `svg/templates_folder.svg` | Dossier violet, pile de modèles |
| TEMPLATES_SUB-FOLDER | `svg/templates_sub_folder.svg` | Dossier violet clair, modèle |
| LANDING_PAGE | `svg/landing_page.svg` | Fenêtre navigateur + accueil |
| TRASH | `svg/trash.svg` | Corbeille |
| FOLDER | `svg/folder.svg` | Dossier jaune simple |
| SUBFOLDER | `svg/subfolder.svg` | Dossier jaune, 1 niveau ↳ |
| SUBSUBFOLDER | `svg/subsubfolder.svg` | Dossier jaune, 2 niveaux ↳↳ |
| YEAR | `svg/year.svg` | Dossier turquoise, calendrier 12 mois |
| MONTH | `svg/month.svg` | Dossier turquoise clair, calendrier « 31 » |
| GAMME | `svg/gamme.svg` | Dossier orange brûlé, couches empilées |
| AXIS_DOMAIN | `svg/axis_domain.svg` | Dossier indigo foncé, organigramme |
| DOMAIN | `svg/domain.svg` | Dossier indigo, cible |
| AXIS | `svg/axis.svg` | Dossier indigo clair, axes + courbe |

## Logique couleur
- Rouge : organisation (GROUP, CATEGORY) — reprend les icônes rouges actuelles.
- Jaune : rangement générique (FOLDER, SUBFOLDER, SUBSUBFOLDER).
- Turquoise : rangement chronologique (YEAR, MONTH).
- Indigo dégradé foncé → clair : hiérarchie AXIS_DOMAIN → DOMAIN → AXIS.
- Violet : modèles.

## Modifier / régénérer
Couleurs et pictogrammes sont définis dans `generate.py` : `python3 generate.py` réécrit `svg/` et `preview.html`.
