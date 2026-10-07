#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exo FM Monitor - Script de surveillance
Capture le flux, identifie via Shazam, enrichit avec iTunes.
"""

import asyncio
import subprocess
import os
import json
import time
import requests
from datetime import datetime, timezone, timedelta
from shazamio import Shazam

# ============================================================
# CONFIG
# ============================================================
FLUX_URL = "https://exofmreunion.ice.infomaniak.ch/exofmreunion-128.aac"
FICHIER_WAV = "/tmp/exofm_extrait.wav"
FICHIER_JSON = os.path.join(os.path.dirname(__file__), "data.json")
FICHIER_HISTORIQUE = os.path.join(os.path.dirname(__file__), "historique.json")

DUREE_CAPTURE = 12
INTERVALLE = 60
SEUIL_DOUBLON = 180

TZ_REUNION = timezone(timedelta(hours=4))

DERNIER_MORCEAU = None
DERNIER_TS = 0


# ============================================================
# CAPTURE
# ============================================================
def capturer_audio(duree=DUREE_CAPTURE):
    cmd = [
        "ffmpeg", "-y",
        "-i", FLUX_URL,
        "-t", str(duree),
        "-ar", "16000",
        "-ac", "1",
        "-f", "wav",
        FICHIER_WAV
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=40)
    except subprocess.TimeoutExpired:
        print("⚠️  Timeout ffmpeg")
        return None
    if not os.path.exists(FICHIER_WAV) or os.path.getsize(FICHIER_WAV) < 10000:
        return None
    return FICHIER_WAV


# ============================================================
# SHAZAM
# ============================================================
async def identifier_shazam(fichier):
    shazam = Shazam()
    try:
        resultat = await shazam.recognize(fichier)
    except Exception as e:
        print(f"💥 Erreur Shazam : {e}")
        return None
    track = resultat.get('track') if resultat else None
    if not track:
        return None
    titre = track.get('title', '').strip()
    artiste = track.get('subtitle', '').strip()
    if not titre or not artiste:
        return None
    cover = None
    images = track.get('images', {})
    if images:
        cover = images.get('coverart') or images.get('background')
    return {'titre': titre, 'artistes': artiste, 'cover_shazam': cover}


# ============================================================
# ITUNES (avec explicit)
# ============================================================
def enrichir_itunes(titre, artiste):
    try:
        r = requests.get("https://itunes.apple.com/search", params={
            'term': f"{artiste} {titre}",
            'media': 'music',
            'entity': 'song',
            'limit': 1
        }, timeout=10)
        data = r.json()
        if data.get('resultCount', 0) > 0:
            item = data['results'][0]
            return {
                'album': item.get('collectionName', ''),
                'annee': int(item.get('releaseDate', '0000')[:4]) if item.get('releaseDate') else None,
                'cover_deezer': item.get('artworkUrl100', '').replace('100x100', '500x500'),
                'preview_mp3': item.get('previewUrl', ''),
                'genre': item.get('primaryGenreName', ''),
                'duree_sec': int(item.get('trackTimeMillis', 0) / 1000) if item.get('trackTimeMillis') else None,
                'explicit': item.get('trackExplicitness', 'notExplicit'),
            }
    except Exception as e:
        print(f"⚠️  Erreur iTunes : {e}")
    return {}


# ============================================================
# FUSION
# ============================================================
def fusionner(shazam_data):
    maintenant = datetime.now(TZ_REUNION)
    ts = int(maintenant.timestamp())
    itunes = enrichir_itunes(shazam_data['titre'], shazam_data['artistes'])
    explicit = itunes.get('explicit', 'notExplicit')
    est_explicit = explicit == 'explicit'
    return {
        'titre': shazam_data['titre'],
        'artistes': shazam_data['artistes'],
        'cover_deezer': itunes.get('cover_deezer') or shazam_data.get('cover_shazam') or '',
        'preview_mp3': itunes.get('preview_mp3', ''),
        'album': itunes.get('album', ''),
        'annee': itunes.get('annee'),
        'genre': itunes.get('genre', ''),
        'explicit': est_explicit,
        'start_ts': ts,
        'end_ts': ts + (itunes.get('duree_sec') or 0),
        'heure': maintenant.hour,
        'date': maintenant.strftime('%Y-%m-%d'),
        'jour_semaine': maintenant.weekday(),
    }


# ============================================================
# HISTORIQUE
# ============================================================
def charger_historique():
    if os.path.exists(FICHIER_HISTORIQUE):
        try:
            with open(FICHIER_HISTORIQUE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return []


def sauver_historique(hist):
    with open(FICHIER_HISTORIQUE, 'w', encoding='utf-8') as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)


# ============================================================
# STATS
# ============================================================
def calculer_volume(hist):
    return {
        'nb_diffusions': len(hist),
        'nb_artistes': len(set(m['artistes'] for m in hist)),
        'nb_titres': len(set((m['artistes'], m['titre']) for m in hist)),
        'heures': round(len(hist) * 3.5 / 60, 2),
        'duree_moy': 210,
    }


def top_artistes(hist, n=20):
    from collections import Counter
    c = Counter(m['artistes'] for m in hist)
    return [{'artistes': k, 'nb_diffusions': v} for k, v in c.most_common(n)]


def top_titres(hist, n=20):
    from collections import Counter
    c = Counter((m['artistes'], m['titre']) for m in hist)
    return [{'artistes': k[0], 'titre': k[1], 'nb_diffusions': v} for k, v in c.most_common(n)]


def repartition_heures(hist):
    from collections import Counter
    c = Counter(m['heure'] for m in hist if 'heure' in m)
    return [{'heure': h, 'nb': c.get(h, 0)} for h in range(24)]


def repartition_jours(hist):
    from collections import Counter
    c = Counter(m['date'] for m in hist if 'date' in m)
    return [{'date': d, 'nb': c[d]} for d in sorted(c.keys())]


def repartition_semaine(hist):
    from collections import Counter
    jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    c = Counter(m['jour_semaine'] for m in hist if 'jour_semaine' in m)
    return [{'jour': jours[i], 'nb_diffusions': c.get(i, 0)} for i in range(7)]


def repartition_annees(hist):
    from collections import Counter
    c = Counter(m.get('annee') for m in hist if m.get('annee'))
    return [{'annee': a, 'nb_diffusions': c[a]} for a in sorted(c.keys())]


def repartition_explicit(hist):
    nb_exp = sum(1 for m in hist if m.get('explicit'))
    nb_clean = len(hist) - nb_exp
    total = len(hist) or 1
    return [
        {'type_contenu': 'Clean', 'nb': nb_clean, 'pct': round(nb_clean * 100 / total, 1)},
        {'type_contenu': 'Explicit', 'nb': nb_exp, 'pct': round(nb_exp * 100 / total, 1)},
    ]


def artistes_recurrents(hist):
    from collections import defaultdict
    jours = defaultdict(set)
    for m in hist:
        if m.get('date'):
            jours[m['artistes']].add(m['date'])
    res = [{'artistes': a, 'nb_jours': len(j), 'nb_diffusions': sum(1 for m in hist if m['artistes'] == a)}
           for a, j in jours.items() if len(j) >= 2]
    return sorted(res, key=lambda x: x['nb_jours'], reverse=True)[:15]


def titres_recurrents(hist):
    from collections import defaultdict
    jours = defaultdict(set)
    for m in hist:
        if m.get('date'):
            jours[(m['artistes'], m['titre'])].add(m['date'])
    res = [{'artistes': k[0], 'titre': k[1], 'nb_jours': len(j)}
           for k, j in jours.items() if len(j) >= 2]
    return sorted(res, key=lambda x: x['nb_jours'], reverse=True)[:15]


def artistes_diversifies(hist):
    from collections import defaultdict
    titres = defaultdict(set)
    for m in hist:
        titres[m['artistes']].add(m['titre'])
    res = [{'artistes': a, 'nb_titres': len(t), 'nb_diffusions': sum(1 for m in hist if m['artistes'] == a)}
           for a, t in titres.items()]
    return sorted(res, key=lambda x: x['nb_titres'], reverse=True)[:15]


def top_albums(hist, n=15):
    from collections import Counter
    c = Counter(m.get('album', '') for m in hist if m.get('album'))
    return [{'album': k, 'artistes': '', 'nb': v} for k, v in c.most_common(n)]


# ============================================================
# ÉCRITURE data.json
# ============================================================
def ecrire_data_json(morceau, historique):
    maintenant = datetime.now(TZ_REUNION)
    data = {
        'genere_ts': int(maintenant.timestamp()),
        'dernier_morceau': morceau,
        'derniers_morceaux': historique[-50:][::-1],
        'volume': calculer_volume(historique),
        'top_artistes': top_artistes(historique, 20),
        'top_titres': top_titres(historique, 20),
        'heures': repartition_heures(historique),
        'jours': repartition_jours(historique),
        'semaine': repartition_semaine(historique),
        'annees': repartition_annees(historique),
        'explicit': repartition_explicit(historique),
        'recurrents': artistes_recurrents(historique),
        'titres_recurrents': titres_recurrents(historique),
        'diversifies': artistes_diversifies(historique),
        'albums': top_albums(historique, 15),
    }
    with open(FICHIER_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# BOUCLE
# ============================================================
async def boucle():
    global DERNIER_MORCEAU, DERNIER_TS
    print("🎧 Exo FM Monitor démarré")
    print(f"📡 Flux : {FLUX_URL}")
    print(f"⏱️  Intervalle : {INTERVALLE}s\n")
    historique = charger_historique()

    while True:
        try:
            fichier = capturer_audio()
            if not fichier:
                await asyncio.sleep(INTERVALLE); continue

            shazam_data = await identifier_shazam(fichier)
            if not shazam_data:
                print(f"❌ [{datetime.now(TZ_REUNION).strftime('%H:%M:%S')}] Aucun morceau reconnu")
                await asyncio.sleep(INTERVALLE); continue

            maintenant = time.time()
            if (DERNIER_MORCEAU and
                DERNIER_MORCEAU['titre'] == shazam_data['titre'] and
                DERNIER_MORCEAU['artistes'] == shazam_data['artistes'] and
                maintenant - DERNIER_TS < SEUIL_DOUBLON):
                print(f"⏭️  [{datetime.now(TZ_REUNION).strftime('%H:%M:%S')}] Doublon ignoré : {shazam_data['titre']}")
                await asyncio.sleep(INTERVALLE); continue

            morceau = fusionner(shazam_data)
            DERNIER_MORCEAU = morceau
            DERNIER_TS = maintenant

            historique.append(morceau)
            if len(historique) > 5000:
                historique = historique[-5000:]
            sauver_historique(historique)
            ecrire_data_json(morceau, historique)

            tag = "🔞" if morceau['explicit'] else "✅"
            print(f"{tag} [{datetime.now(TZ_REUNION).strftime('%H:%M:%S')}] "
                  f"{morceau['artistes']} — {morceau['titre']}")

        except Exception as e:
            print(f"💥 Erreur boucle : {e}")
        await asyncio.sleep(INTERVALLE)


if __name__ == "__main__":
    asyncio.run(boucle())