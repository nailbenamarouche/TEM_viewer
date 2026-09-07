# Guide d'utilisation — TEM Video Processor

Guide pratique pour l'utilisation de `tem_video_processor.py`, l'éditeur de
post-traitement pour les vidéos produites par `dm4_converter.py` (ou tout
autre fichier vidéo). Pour les détails d'architecture/implémentation, voir
[README.md](README.md). Pour l'étape de conversion DM4→vidéo elle-même,
voir [GUIDE_UTILISATEUR_DM4_CONVERTER.md](GUIDE_UTILISATEUR_DM4_CONVERTER.md).

## 1. Démarrage

```bash
python tem_video_processor.py
```

Ceci ouvre toujours d'abord la boîte de dialogue **DM4 to Video** (voir le
guide DM4 Converter). Convertissez-y un dossier de fichiers DM3/DM4, ou
cliquez sur **Skip — open existing video instead** pour passer directement
à l'ouverture d'un fichier vidéo existant. Une fois cette boîte de dialogue
fermée, la fenêtre principale de l'éditeur s'ouvre — avec la vidéo
résultante (ou choisie) déjà chargée.

Vous pouvez ensuite charger une autre vidéo depuis l'éditeur avec **OPEN
VIDEO**.

## 2. Profondeur de bits

La profondeur de bits de la vidéo est détectée automatiquement (via
`ffprobe`) à l'ouverture, et affichée dans l'en-tête :

- **8-BIT** — décodée normalement via OpenCV.
- **16-BIT NATIVE** — lue via un pipe FFmpeg brut dédié plutôt que OpenCV
  (qui décode toujours en 8-bit et tronquerait sinon silencieusement la
  précision supplémentaire). Tout le pipeline (dérive, contraste, gamma,
  filtres) travaille ensuite à la profondeur native de la source.

Ceci a un impact direct sur l'export (voir [Export](#6-segments-et-export)) :
un export avec perte d'une source 16-bit tronque toujours en 8-bit, et
l'application vous avertira avant de le faire.

## 3. Lecture

- **PLAY/PAUSE** ou **Espace** : bascule la lecture.
- **STOP** : met en pause et revient à l'image 0.
- **Flèche gauche/droite** : avance/recule d'une image.
- La ligne de temps permet de se déplacer directement à n'importe quelle
  image.

**La correction de dérive Edge-strip ne suit le mouvement que pendant la
lecture avant**, pas en se déplaçant sur la ligne de temps — voir
[Correction de dérive](#5-correction-de-dérive).

## 4. Traitement d'image

- **GAMMA** : curseur + champ de saisie exacte (défaut 1.00, c'est-à-dire
  aucun ajustement).
- **CONTRAST** : **AUTOCONTRAST** (défaut) avec écrêtage par percentile
  LOW%/HIGH% ajustable (défaut 1.0/99.0), **CLAHE** avec limite CLIP et
  taille TILE ajustables (défaut 2.0/8) — plus paramétrable ici que dans le
  logiciel d'acquisition en direct — ou **NONE**, qui laisse passer l'image
  sans aucun traitement de contraste (utile pour conserver des intensités
  brutes significatives, par ex. des diagrammes de diffraction). Notez que
  NONE ne désactive que cette étape - GAMMA reste appliqué par-dessus,
  laissez donc aussi GAMMA à 1.00 si vous voulez une image vraiment
  inchangée.
- **FILTER** : NONE / GAUSSIAN / MEDIAN / BILATERAL / NLM, chacun avec ses
  propres paramètres (taille de noyau, sigma, etc.). NLM est une
  approximation rapide par filtre bilatéral sur CPU comme sur GPU, pas un
  véritable Non-Local Means (trop lent en pratique sur CPU).
- **FLAT FIELD CORRECTION** : cliquez sur **LOAD FLAT FIELD** pour choisir
  une image de référence noire, puis une image de gain/référence.
  Contrairement au logiciel d'acquisition en direct, il n'y a pas de chemin
  de fichier fixe — vous choisissez vous-même les images, qui sont
  automatiquement redimensionnées pour correspondre à la résolution de la
  vidéo chargée si nécessaire.

## 5. Correction de dérive

Menu déroulant **METHOD** :

- **NONE (MANUAL)** — réglez un décalage X/Y fixe en pixels à la main,
  appliqué à chaque image.
- **EDGE-STRIP (AUTO)** — suit la dérive en corrélant la texture près des
  bords de l'image, d'une image à l'autre. Nécessite une véritable
  **lecture avant**, pas un déplacement sur la ligne de temps. Les champs
  **MARGIN** et **WIDTH** contrôlent où se situe la bande échantillonnée :
  si vos acquisitions ont un vignettage noir/bord circulaire,
  échantillonner juste au bord réel tombe sur du vignettage sans rien à
  suivre — augmentez MARGIN jusqu'à sortir du vignettage (c'est la raison
  la plus fréquente pour laquelle edge-strip « semble » échouer).
- **ROI (AUTO)** — cliquez sur **SELECT ROI**, puis glissez un rectangle
  sur la vidéo sur une caractéristique distinctive ; le suivi se verrouille
  sur cette caractéristique par corrélation de motif. Fonctionne n'importe
  où dans l'image, y compris avec un bord vignetté/circulaire, puisque vous
  choisissez vous-même la région suivie.

**Important** : choisir une méthode ne fait que calculer le décalage. Il
faut aussi cocher **APPLY DRIFT CORRECTION** pour qu'il soit réellement
appliqué à l'image — c'est un interrupteur maître séparé, et il est facile
de configurer une méthode et de se demander pourquoi rien ne change parce
que cette case est encore décochée.

## 6. Segments et export

- **IN** / **OUT** (ou `I` / `O`) : marque l'image actuelle comme début/fin
  d'une plage de sélection sur la ligne de temps. **CLEAR** (ou `X`)
  l'efface.
- **ADD SEGMENT** (ou `A`) : enregistre la plage IN/OUT actuelle **avec les
  réglages de traitement actuels** (gamma, méthode de contraste et ses
  paramètres, filtre et ses paramètres, décalage de dérive/indicateur
  d'application) comme un segment nommé (`SEG 1`, `SEG 2`, ...). C'est ainsi
  que différentes parties d'une même vidéo peuvent recevoir un traitement
  différent — par exemple un segment en autocontraste, un autre en CLAHE
  avec un débruitage plus poussé.
  - Remarque : les valeurs MARGIN/WIDTH d'edge-strip ne sont *pas*
    enregistrées par segment (ce sont des réglages globaux uniques), seuls
    les éléments listés ci-dessus le sont.
  - Cliquer sur un segment dans la liste recharge ses réglages et déplace
    la ligne de temps/la sélection en conséquence — utile pour le relire ou
    l'ajuster avant de le réexporter. **DELETE** supprime le segment
    sélectionné, **CLEAR ALL** les supprime tous.
- **EXPORT** : si aucun segment n'est défini, demande s'il faut exporter
  toute la vidéo avec les réglages actuels. Si des segments existent,
  exporte chacun dans son propre fichier. Choisissez d'abord le mode
  d'export :
  - **LOSSY H.265** — fichiers petits, toujours en sortie 8-bit. Exporter
    une source 16-bit avec ce mode la tronque — une boîte de dialogue de
    confirmation apparaît avant de continuer.
  - **LOSSLESS FFV1** — encode à la profondeur de bits réelle de la source
    (8- ou 16-bit), aucune perte de compression, fichiers bien plus gros,
    écrits en `.mkv` (pas `.mp4` — le conteneur MP4 ne supporte pas de
    façon fiable le 16-bit/FFV1).

## 7. Surimpression des métadonnées DM4

**SHOW METADATA OVERLAY** n'est sélectionnable que si la vidéo actuellement
chargée possède un fichier `<vidéo>.metadata.json` à côté d'elle — que
`dm4_converter.py` écrit automatiquement lors de la conversion de fichiers
DM3/DM4 (taille de pixel, champ de vue, tension, grossissement, opérateur,
etc., extraits des tags DM4 de la première image). Un fichier vidéo ouvert
directement n'en dispose pas, et la case reste désactivée.

## 8. Autres outils

- **HISTOGRAM** (bouton) : ouvre une petite fenêtre avec un histogramme
  d'intensité en direct de l'image actuelle (moyenne/écart-type dans le
  titre).
- **SCREENSHOT** (bouton ou `C`) : enregistre l'image actuelle en PNG.
- **RESET SETTINGS** : restaure le gamma, la méthode de contraste et ses
  paramètres, le filtre et ses paramètres, le champ plat et la correction de
  dérive (y compris redésactiver APPLY DRIFT CORRECTION) à leurs valeurs par
  défaut. Ne touche pas à la vidéo chargée, aux segments, ni au thème.
- **THEME** : DARK / LIGHT.
- **FULLSCREEN** (case à cocher ou `F11`, `Échap` pour quitter).

## 9. Raccourcis clavier

| Touche | Action |
|---|---|
| `Espace` | Lecture / Pause |
| `Gauche` / `Droite` | Reculer / avancer d'une image |
| `I` | Définir le point IN |
| `O` | Définir le point OUT |
| `X` | Effacer la sélection IN/OUT |
| `A` | Ajouter un segment depuis la sélection actuelle |
| `C` | Capture d'écran |
| `F11` | Basculer le plein écran |
| `Échap` | Quitter le plein écran |
| `Q` | Quitter |

## 10. Dépannage

- **La correction de dérive Edge-strip ne semble rien suivre** : vérifiez
  que vous appuyez bien sur **PLAY** et non simplement en train de vous
  déplacer sur la ligne de temps — elle a besoin d'une lecture séquentielle
  avant pour accumuler le mouvement d'une image à l'autre. Si elle ne suit
  toujours rien, augmentez **MARGIN** (les acquisitions à champ de vue
  circulaire/vignetté en ont presque toujours besoin au-dessus de 0).
- **La méthode de dérive est réglée mais l'image ne bouge pas** : vérifiez
  **APPLY DRIFT CORRECTION** — le menu de méthode ne fait que calculer le
  décalage, c'est cette case qui l'applique réellement.
- **Une vidéo 16-bit exportée semble délavée / de moins bonne qualité que
  prévu** : vous avez probablement exporté en LOSSY H.265, qui tronque
  toujours en 8-bit. Utilisez LOSSLESS FFV1 pour conserver la pleine
  précision (fichier plus gros, `.mkv`).
- **La correction de champ plat semble incorrecte après le chargement des
  images de référence** : vérifiez la ligne de statut sous LOAD FLAT FIELD
  — si les images noire et de gain n'avaient pas la même résolution entre
  elles, ou avec la vidéo chargée, elles sont redimensionnées
  automatiquement, ce qui est indiqué à cet endroit.
- **SHOW METADATA OVERLAY est grisé** : la vidéo chargée n'a pas de fichier
  `<vidéo>.metadata.json` associé — cela n'existe que pour les vidéos
  produites par le convertisseur DM4, pas pour les vidéos ouvertes
  directement.
