# TEM Viewer

Logiciels développés dans le cadre d'un stage de Master (SIA2, Université de
Toulouse) au laboratoire CEMES-CNRS, équipe PPM, pour le pilotage et le
post-traitement de caméras de microscope électronique à transmission (MET)
lors d'expériences in-situ.

Le projet est composé de deux programmes complémentaires, partageant un
même pipeline de traitement d'image, décrits en détail dans le rapport de
stage associé.

## Scripts

### `tem_main.py`
Acquisition temps réel pour la caméra **Ximea Megaview** (capteur CCD).

- Acquisition sans perte de trames via double-buffering (`RawBufferWriter`,
  `DoubleBufferedWriter`)
- Pipeline de traitement en temps réel dans un thread dédié
  (`ImageProcessingWorker`) : correction de champ plat, gamma,
  contraste/luminosité, filtres (gaussien, médian, bilatéral), CLAHE ou
  autocontraste adaptatif
- Correction de dérive de l'échantillon par corrélation de phase
  (`FrameToFrameTracker`) ou par suivi de région d'intérêt (`ROITracker`)
- Enregistrement vidéo avec audio synchronisé via FFmpeg (FFV1 sans perte,
  HEVC/NVENC GPU, ou HEVC CPU)
- Mode diffraction (exposition/gain figés, traitement désactivé)
- Interface utilisateur PyQt5 (`TEMViewerApp`)

### `dm4_converter.py`
Conversion des acquisitions individuelles **Gatan OneView** (capteur CMOS,
fichiers DM3/DM4) en vidéo.

- Lecture des fichiers DM3/DM4 via `ncempy`
- Concaténation chronologique en une vidéo continue via un pipe FFmpeg
  (format `rawvideo`), sans fichiers intermédiaires
- Conversion en arrière-plan dans un thread dédié (`ConversionWorker`)
- Fenêtre de sélection de dossier et de lancement (`DM4ConverterDialog`)

### `tem_video_processor.py`
Éditeur de post-traitement pour les vidéos issues de `dm4_converter.py`
(ou toute autre vidéo).

- Mêmes algorithmes de traitement que `tem_main.py` (dérive, autocontraste,
  gamma), avec le CLAHE intégré directement dans `TEMProcessor`
- Segmentation de la vidéo en plages à traitement indépendant
  (`ProcessingSegment`)
- Ligne de temps interactive (`TimelineWidget`)
- Fenêtre principale d'édition et d'export (`TEMVideoProcessor`)
- Importe `DM4ConverterDialog` depuis `dm4_converter.py` : les deux fichiers
  doivent rester dans le même dossier

## Dépendances

```
pip install opencv-python numpy PyQt5 matplotlib xxhash ncempy
```

Deux dépendances supplémentaires ne sont pas installables via pip :

- **SDK Ximea (`xiapi`)** : requis uniquement par `tem_main.py`, fourni par
  Ximea avec les pilotes de la caméra Megaview. Nécessite la caméra
  physique connectée.
- **FFmpeg** : requis par les trois scripts pour l'encodage/décodage vidéo.
  Doit être installé séparément et accessible dans le PATH.

`tem_main.py` nécessite en outre la caméra Ximea Megaview branchée pour
fonctionner ; `dm4_converter.py` et `tem_video_processor.py` n'ont pas cette
contrainte et peuvent tourner sur n'importe quelle machine disposant des
dépendances Python et de FFmpeg.

## Utilisation

```bash
# Acquisition temps réel (nécessite la caméra Ximea Megaview)
python tem_main.py

# Conversion DM3/DM4 -> vidéo, puis édition
python dm4_converter.py
```

## Contexte

Développé par Nail Benamarouche, stage de Master 2 SIA2 (avril–septembre
2026), sous la direction de Frédéric Mompiou, laboratoire CEMES-CNRS,
équipe Physique de la Plasticité et Métallurgie (PPM).
