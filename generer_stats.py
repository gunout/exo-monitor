#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère les CSV agrégés depuis historique.json."""

import json
import csv
import os
from collections import Counter

BASE = os.path.dirname(__file__)
HIST = os.path.join(BASE, "historique.json")
OUT = os.path.join(BASE, "resultats")
os.makedirs(OUT, exist_ok=True)

with open(HIST, 'r', encoding='utf-8') as f:
    hist = json.load(f)

def ecrire(nom, entetes, lignes):
    with open(os.path.join(OUT, nom + ".csv"), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(entetes)
        w.writerows(lignes)

ecrire("00_volume_global",
       ["nb_diffusions", "nb_artistes", "nb_titres", "heures_antenne", "duree_moy_s"],
       [[len(hist),
         len(set(m['artistes'] for m in hist)),
         len(set((m['artistes'], m['titre']) for m in hist)),
         round(len(hist) * 3.5 / 60, 2), 210]])

c = Counter(m['artistes'] for m in hist)
ecrire("01_top_artistes", ["artistes", "nb_diffusions"], [[k, v] for k, v in c.most_common(50)])

c = Counter((m['artistes'], m['titre']) for m in hist)
ecrire("02_top_titres", ["artistes", "titre", "nb_diffusions"],
       [[k[0], k[1], v] for k, v in c.most_common(50)])

c = Counter(m['heure'] for m in hist if 'heure' in m)
ecrire("03_repartition_horaire", ["heure", "nb_diffusions"], [[h, c.get(h, 0)] for h in range(24)])

c = Counter(m['date'] for m in hist if 'date' in m)
ecrire("04_repartition_journaliere", ["date", "nb_diffusions"], [[d, c[d]] for d in sorted(c.keys())])

jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
c = Counter(m['jour_semaine'] for m in hist if 'jour_semaine' in m)
ecrire("09_jour_semaine", ["jour", "nb_diffusions"], [[jours[i], c.get(i, 0)] for i in range(7)])

c = Counter(m.get('annee') for m in hist if m.get('annee'))
ecrire("15_par_annee", ["annee", "nb_diffusions"], [[a, c[a]] for a in sorted(c.keys())])

c = Counter(m.get('album', '') for m in hist if m.get('album'))
ecrire("17_top_albums", ["album", "artistes", "nb_diffusions"], [[k, "", v] for k, v in c.most_common(50)])

# Explicit
nb_exp = sum(1 for m in hist if m.get('explicit'))
nb_clean = len(hist) - nb_exp
total = len(hist) or 1
ecrire("16_explicit", ["type_contenu", "nb", "pct"], [
    ['Clean', nb_clean, round(nb_clean * 100 / total, 1)],
    ['Explicit', nb_exp, round(nb_exp * 100 / total, 1)],
])

if hist:
    m = hist[-1]
    ecrire("18_dernier_morceau",
           ["titre", "artistes", "start_ts", "end_ts", "cover_deezer", "preview_mp3"],
           [[m['titre'], m['artistes'], m['start_ts'], m['end_ts'],
             m.get('cover_deezer', ''), m.get('preview_mp3', '')]])

print("✅ CSV générés dans", OUT)