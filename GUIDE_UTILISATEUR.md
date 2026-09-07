# Guide d'utilisation — TEM Live Viewer

Guide pratique pour l'utilisation de `tem_main.py`, le logiciel
d'acquisition temps réel pour la caméra Ximea Megaview. Pour les détails
d'architecture/implémentation, voir [README.md](README.md).

## 1. Démarrage

```bash
python tem_main.py
```

La fenêtre s'ouvre avec l'affichage indiquant « Camera not connected ».
Cliquez sur **Connect Camera** pour démarrer le flux vidéo — cela ne fait
que démarrer l'*affichage* ; l'enregistrement sur disque est une étape
séparée (voir [Enregistrement](#6-enregistrement)).

## 2. Mode microscope

Le menu déroulant **Microscope Mode** bascule entre deux préréglages.
Sélectionner l'un d'eux écrase l'exposition, le gain, la méthode de
contraste, la correction de champ plat, le débruitage, le binning et
l'encodeur — à considérer comme un point de départ, pas un verrouillage.

| Paramètre | Image Mode (défaut) | Diffraction Mode |
|---|---|---|
| Exposition | 40 ms | 40 ms |
| Gain | 20 dB | 20 dB |
| Méthode de contraste | Autocontraste | Aucune |
| Champ plat | Activé | Désactivé |
| Débruitage NLM/Bilatéral | Désactivé | Désactivé |
| Binning | inchangé | forcé à 1x1 |
| Encodeur | CPU (libx265) | Sans perte (FFV1) |
| Gamma | réinitialisé à 1.00 | réinitialisé à 1.00 |

Le mode Diffraction désactive le traitement d'image et bascule vers un
enregistrement sans perte, car les diagrammes de diffraction doivent rester
quantitativement intacts — ne réactivez pas CLAHE/autocontraste/champ plat
dans ce mode si les intensités brutes doivent conserver leur sens.

## 3. Exposition et gain

- Champs **Exposure (ms)** et **Manual Gain (dB)** : saisissez une valeur et
  appuyez sur **Entrée**, ou utilisez les **flèches Haut/Bas** pendant que
  le champ a le focus — les deux s'appliquent immédiatement, sans avoir à
  cliquer sur Apply à la souris. Les boutons Apply fonctionnent toujours si
  vous préférez la souris.
- **Auto Exposure/Gain (AEAG)** : active/désactive l'algorithme d'exposition
  et de gain automatique de la caméra. Quand il est activé, les champs
  exposition/gain sont désactivés (c'est la caméra qui les pilote) et
  l'exposition peut aller jusqu'à 80 ms (plafond fixé pour qu'une scène
  sombre ne fasse pas chuter la fréquence d'image à quelques FPS). Désactiver
  l'AEAG restaure le contrôle manuel au gain actuellement réglé.
- Changer l'exposition change la fréquence d'image native de la caméra
  (environ 1000/exposition en ms) — l'indicateur **FPS** dans la barre de
  statut est la fréquence réellement mesurée, qui devrait suivre cette
  valeur sauf si CLAHE/NLM/les écritures disque deviennent le goulot
  d'étranglement (voir [Dépannage](#9-dépannage)).

## 4. Traitement d'image

- Curseurs **Gamma / Brightness / Contrast** : ajustements de tonalité
  manuels, appliqués *en dernier* dans le pipeline (après CLAHE/
  autocontraste) afin d'avoir toujours un effet visible quelle que soit la
  méthode de contraste choisie.
- **Méthode de contraste** (boutons radio) :
  - **Autocontrast (Recommended)** — défaut. Étirement automatique basé sur
    les percentiles.
  - **CLAHE** — amélioration de contraste adaptative locale. Coûte
    sensiblement plus de temps CPU/GPU par image que l'autocontraste.
  - **None** — les valeurs brutes passent sans modification (utilisé par le
    mode Diffraction).
- **Filter** (boutons radio) : None / Gaussian / Median / Bilateral, chacun
  avec ses propres champs de taille de noyau/sigma.
- Case **NLM Denoising** (ou **Bilateral Denoising (GPU)** si un GPU CUDA
  est détecté) : une passe de débruitage supplémentaire avant l'amélioration
  du contraste. Il s'agit d'une approximation rapide par filtre bilatéral
  sur CPU comme sur GPU, pas d'un véritable Non-Local Means — le vrai NLM
  est trop lent pour un affichage temps réel (typiquement 150-250ms/image,
  soit 4-6 FPS).
- Case **Flat-field correction** : corrige la réponse à motif fixe du
  capteur à partir d'images de référence noir/champ plat. Si le message
  « WARNING: Could not load flat-field correction » apparaît dans le
  journal, les fichiers de référence ne se trouvent pas au chemin attendu
  sur cette machine — la correction ne fera alors silencieusement rien tant
  que ce n'est pas corrigé.

## 5. Correction de dérive

Trois modes (boutons radio dans **Drift correction**) :

- **None** — aucune correction.
- **Edge-strip** — suit la dérive de l'échantillon en corrélant quatre
  bandes échantillonnées près des bords de l'image, d'une image à l'autre.
  Deux réglages :
  - **Margin** : distance par rapport au bord réel à laquelle échantillonner,
    en pixels (rogne aussi les extrémités de chaque bande vers l'intérieur,
    pour rester à l'écart des coins). **Les acquisitions MET avec un champ
    de vue circulaire/vignetté nécessitent de monter cette valeur au-dessus
    de 0** — échantillonner juste au bord (et à travers les coins) tombe sur
    du vignettage sans aucune texture à suivre, ce qui donne l'impression
    que la correction « ne fait rien » quelle que soit la dérive réelle de
    l'échantillon. Augmentez la valeur jusqu'à ce que les rectangles de
    bande affichés se trouvent à l'intérieur du cercle éclairé.
  - **Width** : épaisseur de la bande échantillonnée, en pixels.
  - Activer ce mode crée un fichier `drift_log_<timestamp>.csv` dans le
    dossier de travail, journalisant pour chaque image le (dx, dy,
    fiabilité) mesuré. Il est fermé automatiquement en changeant de mode de
    dérive ou en quittant.
- **ROI (click+drag on preview)** — cliquez-glissez un rectangle sur l'image
  en direct sur une caractéristique distinctive ; la correction de dérive se
  verrouille sur cette caractéristique par corrélation de motif (template
  matching) plutôt que sur les bords de l'image (fonctionne même avec un
  champ de vue vignetté, puisque vous choisissez vous-même la région
  suivie). La sélection doit faire entre 32 et 512 px de côté. Le suivi se
  réacquiert automatiquement s'il est brièvement perdu (mouvement rapide,
  occlusion) plutôt que de rester bloqué.

Avec l'un ou l'autre mode actif, l'image corrigée est affichée avec une
surimpression (rectangles verts des bandes, ou rectangle de verrouillage
ROI) permettant de vérifier visuellement que le suivi tient bien.

## 6. Enregistrement

- Bouton **Record: OFF/ON** : démarre/arrête l'enregistrement du flux en
  direct sur disque, indépendamment de la connexion caméra (se connecter ne
  fait que démarrer l'affichage). Arrêter l'enregistrement écrit le segment
  en mémoire tampon sur disque en arrière-plan — l'affichage continue
  pendant ce temps.
- **Pause/Resume** : met en pause l'enregistrement et écrit le segment en
  cours sans se déconnecter ni arrêter l'affichage ; reprendre démarre un
  nouveau segment.
- Les segments sont automatiquement écrits sur disque toutes les 1200
  images, ou si la mémoire tampon dépasse 8 Go, selon la première condition
  atteinte.
- **Encoder** : GPU (hevc_nvenc) - Fast / **CPU (libx265) - Smallest**
  (défaut) / Lossless (FFV1) - Scientific.
- **Encoding Mode** : **High Quality (CQ)** — un seul paramètre de qualité
  (CQ pour GPU, CRF pour CPU libx265), plus la valeur est basse plus la
  qualité est élevée (et le fichier gros), plus elle est haute plus c'est
  compressé (et le fichier petit), plage valide 0-51. Ou **Long Duration** —
  un débit binaire cible en Mbps à la place, pour une taille de fichier
  prévisible sur des enregistrements longs.
- Case **Concatenate videos on quit** : à la fermeture, réunit tous les
  segments de la session en un seul `session_<timestamp>_concat.mkv`, dans
  l'ordre où ils ont réellement été enregistrés (suivi dans un manifeste
  `<timestamp>_segments.json` à côté des fichiers vidéo — c'est ce qui
  garantit un ordre de concaténation correct même si les segments finissent
  leur encodage dans le désordre en arrière-plan).

## 7. Histogramme, captures d'écran, journal

- **H** ou **Open Histogram** : ouvre une petite fenêtre avec un histogramme
  d'intensité en direct (moyenne/écart-type dans le titre), rafraîchi
  plusieurs fois par seconde.
- **C** ou **Screenshot** : enregistre l'image suivante en PNG horodaté dans
  le dossier de sortie.
- La fenêtre de journal reflète tout ce qui est affiché dans la console
  (statut de connexion, changements d'exposition/gain, progression de
  l'encodage, erreurs).

## 8. Raccourcis clavier

| Touche | Action |
|---|---|
| `P` | Pause / Reprise de l'enregistrement |
| `C` | Capture d'écran |
| `H` | Ouvrir la fenêtre d'histogramme |
| `R` | Réinitialiser les réglages de traitement/affichage par défaut |
| `F11` | Basculer le plein écran |
| `Échap` | Quitter le plein écran |
| `Q` | Quitter |
| `Haut` / `Bas` (dans un champ Exposure/Gain) | Ajuster la valeur et l'appliquer immédiatement |
| `Entrée` (dans un champ Exposure/Gain) | Appliquer la valeur saisie |

**Reset (R)** restaure le gamma, la luminosité/contraste, la méthode de
contraste, les filtres, le champ plat, le débruitage et la correction de
dérive à leurs valeurs par défaut. Cela ne touche **pas** aux réglages
matériels de la caméra (exposition/gain), au mode microscope, à l'encodeur
ni à l'audio — ce sont des réglages de session, pas des ajustements
d'affichage.

## 9. Dépannage

- **FPS plus bas qu'attendu / ne suit pas les changements d'exposition** :
  CLAHE et le débruitage coûtent tous deux un temps réel par image. Si le
  FPS ne bouge pas quand vous changez l'exposition, vérifiez si CLAHE ou le
  débruitage sont activés — sans GPU disponible, les deux basculent sur CPU,
  plus lent. Le FPS devrait suivre l'exposition de près avec les deux
  désactivés (méthode de contraste : None, débruitage désactivé).
- **La correction de dérive Edge-strip semble ne rien faire** : augmentez
  **Margin** (voir [Correction de dérive](#5-correction-de-dérive)) —
  c'est presque toujours un problème de vignettage sur des acquisitions à
  champ de vue circulaire, pas un suivi défaillant.
- **Le suivi ROI perd la caractéristique lors d'un mouvement rapide** : il
  se rétablit de lui-même en quelques images en élargissant sa recherche ;
  s'il perd le verrouillage de façon persistante, choisissez une
  caractéristique plus contrastée/distinctive pour le ROI.
- **L'AEAG ne semble rien changer** : il est plafonné à 80 ms d'exposition
  (pour protéger la fréquence d'image) — dans une scène vraiment sombre,
  cela peut ne pas suffire ; augmentez alors le gain manuellement avec
  l'AEAG désactivé.
- **Un segment enregistré a mis longtemps à s'encoder** : vérifiez la valeur
  CQ/CRF dans Encoding Mode — une valeur basse (ex. 12) est proche du sans
  perte et est légitimement lente sur CPU même avec un preset rapide.
  Augmentez-la (ex. 20-28) pour des encodages bien plus rapides avec une
  perte de qualité modérée.
- **Les segments vidéo concaténés sont dans le mauvais ordre** : ne devrait
  plus arriver depuis la correction par manifeste de segments — si c'est le
  cas, vérifiez que le fichier `<timestamp>_segments.json` à côté des
  segments vidéo correspond à l'ordre d'enregistrement ; signalez-le sinon.
