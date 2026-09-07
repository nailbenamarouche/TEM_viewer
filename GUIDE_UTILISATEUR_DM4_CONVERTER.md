# Guide d'utilisation — DM4 Converter

Guide pratique pour la boîte de dialogue de conversion DM3/DM4 → vidéo
définie dans `dm4_converter.py`. Pour les détails d'architecture/
implémentation, voir [README.md](README.md). Pour l'éditeur vers lequel
elle bascule ensuite, voir
[GUIDE_UTILISATEUR_VIDEO_PROCESSOR.md](GUIDE_UTILISATEUR_VIDEO_PROCESSOR.md).

**Remarque** : `dm4_converter.py` est un module utilitaire, pas un
programme autonome — il n'a pas de fenêtre à lancer directement. Il est
importé par `tem_video_processor.py`, qui affiche sa boîte de dialogue
automatiquement au démarrage. Les deux fichiers doivent rester dans le même
dossier.

## 1. Ouvrir la boîte de dialogue

```bash
python tem_video_processor.py
```

La boîte de dialogue **TEM Video Processor — DM4 to Video** s'ouvre en
premier, avant la fenêtre principale de l'éditeur. Depuis là, vous
convertissez soit un dossier de fichiers DM3/DM4 en vidéo, soit vous passez
directement à l'ouverture d'un fichier vidéo existant.

## 2. Sélection du dossier source

Cliquez sur **Browse…** à côté de **DM4/DM3 folder** et choisissez soit :

- un **dossier plat** de fichiers DM3/DM4 individuels, soit
- un **dossier « heure »** contenant des sous-dossiers `minute_XX`,
  chacun contenant des sous-dossiers `second_XX` de frames (l'organisation
  souvent utilisée par les sessions d'acquisition Ximea/OneView).

L'organisation hiérarchique est détectée automatiquement. Quand c'est le
cas, la ligne de statut indique le nombre de minutes/secondes/frames
trouvées, et le **Source FPS est calculé automatiquement** à partir du
rythme de capture réel (nombre total de frames ÷ nombre total de
sous-dossiers secondes — chaque dossier `second_XX` représente exactement
une seconde enregistrée). Vous pouvez toujours le corriger manuellement
ensuite.

Le champ **File pattern** (défaut `*.dm4`) contrôle quels fichiers sont pris
en compte dans chaque dossier — le changer (par ex. en `*.dm3`) relance
automatiquement l'analyse du dossier.

## 3. Sortie et qualité

- **Output video** : le chemin est pré-rempli à côté du dossier source dès
  que vous le choisissez, mais peut être changé avec son propre
  **Browse…**.
- **Quality** :
  - **Lossy H.264 (8-bit, smaller files)** — encode toujours en 8-bit
    `yuv420p`. Si les frames source sont en 16-bit, cela les tronque ; un
    message d'avertissement apparaît une fois l'analyse des fichiers
    terminée si c'est le cas.
  - **Lossless FFV1 (native bit depth)** — encode à la profondeur réelle
    de la source (8-bit gray ou 16-bit `gray16le`), rien n'est perdu. Les
    fichiers sont bien plus gros, et écrits en `.mkv` (le conteneur MP4 ne
    supporte pas de façon fiable le 16-bit/FFV1) — passer à ce mode change
    automatiquement un chemin de sortie `.mp4` en `.mkv`, et inversement si
    vous revenez en arrière.

## 4. Paramètres d'encodage

- **Source FPS** : le rythme de capture réel des frames (auto-rempli pour
  les dossiers hiérarchiques, voir ci-dessus).
- **Target FPS** : la fréquence d'image de la vidéo de sortie. Si elle
  diffère de Source FPS, les images sont interpolées pour l'atteindre (voir
  Interpolation ci-dessous) plutôt que simplement supprimées/dupliquées.
- **Scale width (px)** : redimensionne la sortie à cette largeur (la
  hauteur conserve le ratio d'aspect, mise à l'échelle Lanczos). `0` =
  **Native (slow)** — résolution source complète, pas de redimensionnement.
- **x264 preset** / **CRF** : s'appliquent uniquement au Lossy H.264. Un
  CRF plus bas = qualité plus élevée/fichier plus gros, un CRF plus haut =
  plus compressé/fichier plus petit (0-51). Le preset échange la vitesse
  d'encodage contre l'efficacité de compression (`ultrafast` le plus
  rapide, `medium` le plus lent parmi les choix proposés).
- **Interpolation** : **blend (fast)** — simple fondu entre images pour
  atteindre le FPS cible — ou **mci (slow, smoother)** — interpolation
  compensée en mouvement, bien plus fluide mais nettement plus lente à
  encoder.

## 5. Conversion

Cliquez sur **Convert**. La progression et la vitesse d'encodage estimée
(images/s) s'affichent dans la ligne de statut et la barre de progression.
**Cancel** arrête proprement la conversion (la sortie partielle n'est pas
traitée comme une vidéo terminée).

Si la source nécessite une mise à l'échelle globale du contraste (données
source ni 8- ni 16-bit), la première passe de la barre de progression
parcourt une fois toute la pile pour trouver un min/max unique et cohérent
— ce qui évite un scintillement de luminosité d'une image à l'autre, que
provoquerait un réajustement naïf de chaque image à son propre min/max.

En cas de succès, la vidéo s'ouvre automatiquement dans la fenêtre
principale de l'éditeur et la boîte de dialogue se ferme. En cas d'échec,
consultez `ffmpeg.log` écrit à côté du fichier de sortie pour le détail de
l'erreur FFmpeg.

## 6. Passer la conversion

Cliquez sur **Skip — open existing video instead** pour ignorer tout ce qui
précède et ouvrir directement un fichier vidéo existant (`.mp4`, `.mkv`,
`.avi`, `.mov`, `.wmv`) dans l'éditeur.

## 7. Métadonnées

Lors d'une conversion depuis DM4, un fichier `<sortie>.metadata.json` est
écrit à côté de la vidéo, contenant la calibration de pixel (taille de
pixel, champ de vue) et les champs instrument/acquisition pouvant être lus
dans les tags DM4 de la première image (tension, grossissement, opérateur,
échantillon, date/heure d'acquisition, binning). C'est du best-effort — une
conversion n'échoue jamais simplement parce qu'un champ de métadonnées
manque — et c'est ce qui alimente l'option **SHOW METADATA OVERLAY** dans
le video processor.

## 8. Dépannage

- **« ffmpeg not found »** : installez FFmpeg et assurez-vous qu'il est
  accessible dans le PATH.
- **Une image est silencieusement ignorée pendant la conversion** : un
  fichier DM3/DM4 qui ne peut pas être lu, ou dont les dimensions ne
  correspondent pas à la première image, est ignoré plutôt que d'interrompre
  toute la conversion (cela désynchroniserait sinon toutes les images
  suivantes dans la sortie).
- **Les couleurs/la luminosité semblent tronquées sur une source 16-bit** :
  vous avez probablement choisi Lossy H.264 — utilisez Lossless FFV1 pour
  conserver la pleine profondeur de bits.
- **Le Source FPS semble incorrect** : n'est auto-détecté que pour
  l'organisation hiérarchique heure/minute/seconde ; pour un dossier plat
  de frames, réglez-le manuellement pour correspondre à votre rythme de
  capture réel.
