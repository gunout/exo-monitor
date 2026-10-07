# 🎧 Exo FM Monitor

> **Moniteur de programmation musicale en temps réel pour Exo FM (La Réunion)**
> Identification automatique des morceaux diffusés via Shazam + enrichissement iTunes.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-ff7a00?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-00a86b?style=for-the-badge)]()
[![Made in Réunion](https://img.shields.io/badge/Made%20in-La%20Réunion-ff7a00?style=for-the-badge&logo=icloud&logoColor=white)](https://www.exofm.re)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-ff7a00?style=for-the-badge&logo=git&logoColor=white)](https://github.com/gunout/exo-monitor/pulls)
[![GitHub stars](https://img.shields.io/github/stars/gunout/exo-monitor?style=for-the-badge&logo=github&color=ff7a00)](https://github.com/gunout/exo-monitor/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/gunout/exo-monitor?style=for-the-badge&logo=github&color=ff7a00)](https://github.com/gunout/exo-monitor/network)
[![GitHub issues](https://img.shields.io/github/issues/gunout/exo-monitor?style=for-the-badge&logo=github&color=ff7a00)](https://github.com/gunout/exo-monitor/issues)

---

## 📖 À propos

**Exo FM** est une radio réunionnaise spécialisée dans la *musique soleil*. Comme de nombreuses radios indépendantes, elle ne publie **aucune métadonnée de playlist** : ni sur son flux Icecast (pas de `icy-metaint`), ni sur son site Wix, ni via une API publique.

**Exo FM Monitor** contourne ce problème en :

1. **Capturant** 12 secondes du flux audio en direct
2. **Convertissant** l'AAC en WAV mono 16 kHz via `ffmpeg`
3. **Identifiant** le morceau avec Shazam (via `shazamio`, non-officiel)
4. **Enrichissant** avec l'API iTunes (pochette HD, extrait 30s, album, année, genre, explicit)
5. **Agrégeant** les statistiques dans un dashboard web

**100 % gratuit**, aucune clé API, aucun abonnement, aucune activation côté radio.

---

## ✨ Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| 🎵 **Identification temps réel** | Détecte le morceau en cours via Shazam toutes les 60 s |
| 🖼️ **Enrichissement iTunes** | Pochette 500×500, extrait 30 s, album, année, genre |
| 🔞 **Détection Explicit** | Badge sur les titres explicites (via iTunes) |
| 📊 **Dashboard web** | Moniteur HTML orange Exo FM avec Plotly |
| 📈 **Statistiques** | Top artistes, top titres, répartition horaire/journalière, évolution |
| 🔁 **Détection doublon** | Évite de ré-identifier le même morceau (seuil 3 min) |
| 📻 **Lecteur intégré** | Écoute du flux Exo FM depuis le navigateur |
| 📺 **Grille des émissions** | Semaine + week-end affichées dynamiquement |
| 💾 **Historique JSON** | Archive complète des diffusions (5000 dernières) |
| 📥 **Export CSV** | Génération de fichiers CSV compatibles avec les autres moniteurs |

---

## 🚀 Installation

### Prérequis

- **Python 3.10+**
- **FFmpeg** (décodage audio)

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y ffmpeg python3-pip python3-venv
```

### Clone + setup

```bash
git clone https://github.com/gunout/exo-monitor.git
cd exo-monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🎬 Utilisation

### 1. Lancer le moniteur (terminal 1)

```bash
cd Bases
python3 shazam_monitor.py
```

Sortie attendue :

```
🎧 Exo FM Monitor démarré
📡 Flux : https://exofmreunion.ice.infomaniak.ch/exofmreunion-128.aac
⏱️  Intervalle : 60s

🔞 [15:24:26] Secteur 410 & Sanjiva — La vie chère
✅ [15:25:33] Goldn.B & Keros-N — Ou Pé
```

### 2. Servir le dashboard (terminal 2)

```bash
cd ~/Desktop/APPS/exo
python3 -m http.server 5050
```

### 3. Ouvrir le moniteur

```
http://localhost:5050/Bases/index.html
```

### 4. (Optionnel) Générer les CSV agrégés

```bash
cd Bases
python3 generer_stats.py
```

Les CSV apparaissent dans `Bases/resultats/`.

---

## 🏗️ Architecture

```
exo-monitor/
├── Bases/
│   ├── shazam_monitor.py      # Script principal (boucle)
│   ├── generer_stats.py       # Export CSV agrégés
│   ├── data.json              # Données temps réel (généré)
│   ├── historique.json        # Archive complète (généré)
│   └── resultats/             # CSV agrégés (généré)
├── index.html                 # Dashboard web orange
├── requirements.txt
└── README.md
```

### Flux de données

```
┌─────────────────┐
│ Flux Icecast    │  https://exofmreunion.ice.infomaniak.ch/exofmreunion-128.aac
│  (AAC 128 kbps) │
└────────┬────────┘
         │ ffmpeg (12s capture → WAV 16kHz mono)
         ▼
┌─────────────────┐
│  Shazam API     │  shazamio (reverse-engineered)
│  (fingerprint)  │
└────────┬────────┘
         │ titre + artiste
         ▼
┌─────────────────┐
│  iTunes API     │  pochette + preview + album + année + genre + explicit
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  data.json      │  consommé par index.html
│  historique.json│
└─────────────────┘
```

---

## 🛠️ Stack technique

| Composant | Technologie | Rôle |
|---|---|---|
| Capture audio | `ffmpeg` | Conversion AAC → WAV |
| Identification | `shazamio` | Reconnaissance musicale (non-officiel) |
| Enrichissement | iTunes Search API | Pochette HD + métadonnées |
| Backend | Python 3.10+ | Boucle de surveillance |
| Frontend | HTML/CSS/JS | Dashboard statique |
| Graphiques | Plotly.js | Visualisations interactives |
| Stockage | JSON | Pas de BDD requise |

---

## ⚠️ Limitations

- **Précision ~90 %** — Shazam peut rater les jingles, transitions, morceaux locaux peu connus.
- **Fragilité** — L'API Shazam non-officielle peut cesser de fonctionner à tout moment.
- **Rate limiting** — Ne pas descendre sous 30 s d'intervalle (risque de blocage IP).
- **Pas d'explicit Shazam** — L'info vient d'iTunes ; certains titres peuvent manquer.
- **Bande passante** — ~1 Mo/minute capturé (négligeable).

---

## 🤝 Contribuer

Les contributions sont les bienvenues !

```bash
# Fork + clone
git clone https://github.com/<ton-user>/exo-monitor.git
cd exo-monitor

# Branche
git checkout -b feature/ma-feature

# Commit
git commit -m "feat: ajout de ma feature"

# Push
git push origin feature/ma-feature

# Ouvrir une Pull Request
```

### Idées d'amélioration

- [ ] Support d'autres radios réunionnaises (NRJ Réunion, Kréol FM…)
- [ ] Alertes Telegram / Discord quand un artiste passe
- [ ] Export Excel (`.xlsx`) en plus du CSV
- [ ] Filtres par plage horaire (matin / après-midi / soir)
- [ ] Dockerisation
- [ ] Service `systemd` pour démarrage automatique
- [ ] Détection auto du changement de morceau (au lieu du polling fixe)

---

## 📜 Licence

Distribué sous licence **MIT**. Voir [`LICENSE`](LICENSE) pour plus d'informations.

---

## ⚖️ Avertissement légal

Ce projet est un **outil de veille à usage personnel et éducatif**.

- Il n'héberge, ne redistribue ni ne stocke aucun contenu audio protégé.
- L'identification Shazam utilise des endpoints non-officiels, à vos propres risques.
- Les métadonnées affichées proviennent d'iTunes Search API (publique).
- Exo FM et ses marques appartiennent à leurs propriétaires respectifs.

---

## 🙏 Remerciements

- [**shazamio**](https://github.com/dotX12/shazamio) — Client Shazam non-officiel
- [**Plotly.js**](https://plotly.com/javascript/) — Graphiques interactifs
- [**iTunes Search API**](https://performance-partners.apple.com/search-api) — Métadonnées musicales
- [**Exo FM**](https://www.exofm.re) — Pour la musique soleil 🌞

---

<div align="center">

**Fait avec ❤️ à La Réunion**

[⬆ Retour en haut](#-exo-fm-monitor)

</div>
