# 🛡️ Security Agent IA — Détection d'intrusion en temps réel pour application bancaire

> Un agent de cybersécurité autonome qui combine **Machine Learning** (Isolation Forest) et un **LLM (Google Gemini)** pour analyser, juger et bloquer en temps réel les requêtes malveillantes adressées à une application web — illustré ici sur une simulation de plateforme bancaire (**SecureBank**).

---

## 📌 Sommaire

- [Contexte et objectif](#-contexte-et-objectif)
- [Démonstration](#-démonstration)
- [Architecture du projet](#-architecture-du-projet)
- [Comment ça marche](#-comment-ça-marche)
- [Tools & Technologies](#-tools--technologies)
- [Key Concepts Covered](#-key-concepts-covered)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Lancement](#-lancement)
- [Tester une attaque](#-tester-une-attaque)
- [Dashboard de l'agent IA](#-dashboard-de-lagent-ia)
- [Limites connues](#-limites-connues)
- [Pistes d'amélioration](#-pistes-damélioration)
- [Avertissement](#-avertissement)
- [Author](#-author)
- [Licence](#-licence)

---

## 🎯 Contexte et objectif

Ce projet est un **prototype pédagogique de SOC (Security Operations Center) assisté par IA**. L'idée est de répondre à une question simple : *peut-on déléguer la détection d'intrusion à une IA générative, en complément d'un modèle de Machine Learning classique ?*

Le scénario simulé est celui d'une banque en ligne (**SecureBank**) qui expose un formulaire de virement et un chatbot client. Chaque requête entrante traverse un **middleware de sécurité** avant d'atteindre l'application :

1. Un modèle ML léger (**Isolation Forest**) fait un premier tri rapide basé sur des caractéristiques de la requête (longueur, présence de caractères suspects).
2. Si la requête est jugée anormale, elle est transmise à un **agent Gemini** qui l'analyse en langage naturel et rend un verdict motivé : `BLOCK` ou `ALLOW`.
3. En cas de blocage, l'IP est bannie, l'événement est journalisé, et une **alerte email** est envoyée automatiquement à l'administrateur.
4. Un **dashboard temps réel** permet de visualiser les flux, les IPs bloquées, l'historique des alertes, et de dialoguer avec un chatbot qui analyse les logs sur demande.

---

## 🖥️ Démonstration

### Scénario complet : de l'attaque au blocage automatique

**1. L'application bancaire en fonctionnement**

L'interface client (`bank_index.html`) simule un compte courant avec formulaire de virement. Chaque soumission passe par le middleware de sécurité, de façon transparente pour l'utilisateur.

![Interface SecureBank](Screenshots/Capture%20d%E2%80%99%C3%A9cran%20%28101%29.png)

**2. Lancement du serveur Flask**

L'agent est démarré en local (mode debug) et écoute sur le réseau pour pouvoir être ciblé par une machine d'attaque (ici une VM Kali Linux sur le même réseau).

![Lancement du serveur Flask](Screenshots/Capture%20d%E2%80%99%C3%A9cran%20%28100%29.png)

**3. Simulation d'une attaque depuis Kali Linux**

Une requête `curl` injecte une charge malveillante combinant **injection SQL** et **XSS** dans le endpoint `/chat` :

```bash
curl -X POST http://192.168.56.1:5000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "SELECT * FROM users; DROP TABLE accounts; <script>alert(1)</script>"}'
```

![Attaque depuis Kali Linux](Screenshots/Capture%20d%E2%80%99%C3%A9cran%20%28104%29.png)

**4. Blocage immédiat — page d'erreur 403**

Le middleware intercepte la requête, le modèle ML détecte l'anomalie, l'agent Gemini confirme le verdict `BLOCK`, et l'IP est immédiatement bannie. Toute requête suivante de cette IP reçoit une page d'erreur 403, y compris pour les ressources statiques (ici une erreur de template attendue en environnement de démo).

![Page d'erreur après blocage](Screenshots/Capture%20d%E2%80%99%C3%A9cran%20%28105%29.png)

**5. Dashboard — visualisation de l'attaque en temps réel**

Le dashboard administrateur affiche le graphique des flux : le trafic normal apparaît en vert, le pic critique de l'attaque détectée apparaît en rouge. L'IP `192.168.56.102` est listée dans les IPs bloquées, et un rapport a été automatiquement envoyé par email.

![Dashboard temps réel](Screenshots/Capture%20d%E2%80%99%C3%A9cran%20%28106%29.png)

**6. Chatbot d'analyse des logs**

L'administrateur peut interroger l'agent IA en langage naturel pour obtenir une synthèse des événements de sécurité de la journée, avec horodatage, IP source et raison du blocage pour chaque alerte.

![Chatbot d'analyse de sécurité](Screenshots/Capture%20d%E2%80%99%C3%A9cran%20%28107%29.png)

**7. Alerte email reçue**

Chaque blocage déclenche l'envoi automatique d'un email d'alerte SOC contenant la date, l'IP bloquée, le type d'attaque et le modèle IA ayant rendu le verdict.

![Email d'alerte SOC](Screenshots/Capture%20d%E2%80%99%C3%A9cran%20%28108%29.png)

---

## 🏗️ Architecture du projet

```
security_agent/
│   .env
│   requirements.txt
│   test_api.py           # Script de diagnostic : liste les modèles Gemini disponibles pour la clé API
│
├───app/
│   │   main.py           # Point d'entrée Flask : middleware de sécurité, routes, dashboard
│   │   config.py         # Chargement centralisé de la configuration (.env)
│   │   __init__.py
│   │
│   ├───services/
│   │       ai_handler.py     # Agent Gemini : chatbot de logs + verdict BLOCK/ALLOW motivé
│   │       ml_engine.py      # Modèle Isolation Forest pour la détection d'anomalies
│   │       mail_sender.py    # Envoi des alertes email (SMTP SSL Gmail)
│   │       __init__.py
│   │
│   ├───static/           # CSS / JS du site bancaire et du dashboard
│   │       bank_style.css
│   │       dashboard_logic.js
│   │       dashboard_style.css
│   │       script.js
│   │       style.css
│   │
│   └───templates/
│           bank_index.html   # Interface client SecureBank
│           dashboard.html    # Dashboard administrateur / SOC
│
├───logs/
│       access.log        # Journal des requêtes : horodatage, IP, statut, action, raison, score
│
└───Screenshots/          # Captures d'écran de démonstration (voir section ci-dessus)
```

---

## ⚙️ Comment ça marche

### 1. Le middleware de sécurité (`app/main.py`)

Chaque requête HTTP entrante (hors fichiers statiques et routes d'administration) passe par `security_middleware()` avant d'atteindre la logique applicative :

- Vérifie si l'IP émettrice est déjà dans la liste noire (`blocked_ips`) → renvoie directement une erreur 403.
- Extrait des **features** simples de la requête : longueur totale, nombre de quotes (`'`), nombre de chevrons (`<`).
- Calcule un **score de menace préliminaire** (10 = normal, 50 = suspect).

### 2. Premier filtre : le modèle ML (`app/services/ml_engine.py`)

Un `IsolationForest` (scikit-learn) entraîné sur un jeu de données "normal" sert de premier détecteur d'anomalies. Toute présence de caractères spéciaux (`'` ou `<`) force immédiatement le statut anomalie, en complément du jugement du modèle.

### 3. Second filtre : le verdict de l'agent Gemini (`app/services/ai_handler.py`)

Si une anomalie est détectée, la requête brute est transmise au modèle **Gemini** (`gemini-flash-latest`) avec un prompt lui demandant de rendre un verdict binaire **BLOCK / ALLOW** et une justification.

> 🔁 **Mode de secours** : si l'API Gemini est indisponible (quota, erreur réseau...), une détection par liste de patterns (`'`, `<`, `>`, `SELECT`, `SCRIPT`) prend automatiquement le relais pour ne jamais laisser une requête suspecte sans réponse.

### 4. Action et notification

- Si le verdict est `BLOCK` : l'IP est ajoutée à la liste noire, l'événement est journalisé avec un score critique (95), et une **alerte email** est envoyée via `smtplib` (SMTP SSL, Gmail).
- Si `ALLOW` : la requête est journalisée avec un score modéré (60) et autorisée à continuer.
- Tout trafic normal (sans anomalie) est journalisé avec un score faible (10).

### 5. Journalisation (`logs/access.log`)

Chaque ligne de log suit le format :

```
timestamp|ip_source|chemin|statut|action|raison|score
```

Ce journal alimente à la fois l'API `/api/stats` (graphique du dashboard) et le chatbot d'analyse (`/chat`).

### 6. Dashboard administrateur (`/admin`)

Une interface temps réel (rafraîchie périodiquement) affiche :
- Un **graphique des flux** (trafic normal en vert, attaques critiques en rouge).
- La liste des **IPs bloquées**, avec un bouton de déblocage manuel.
- L'historique des **emails d'alerte envoyés**.
- Un **chatbot** permettant d'interroger l'agent IA en langage naturel sur l'état de la sécurité (ex. *"est-ce que vous avez détecté une attaque aujourd'hui ?"*).

---

## 🛠️ Tools & Technologies

| Catégorie | Outil / Technologie | Rôle dans le projet |
|---|---|---|
| Langage | **Python 3** | Langage principal du backend |
| Framework web | **Flask** | Serveur applicatif, routes, middleware de sécurité |
| Machine Learning | **scikit-learn** (`IsolationForest`) | Détection d'anomalies sur les requêtes entrantes |
| Calcul numérique | **NumPy / Pandas** | Manipulation des features et des données de logs |
| IA générative | **Google Gemini** (`google-genai`) | Verdict BLOCK/ALLOW motivé + chatbot d'analyse des logs |
| Visualisation | **Plotly** | Graphique temps réel des flux dans le dashboard |
| Frontend | **HTML / CSS / JavaScript** (vanilla) | Interface bancaire (SecureBank) et dashboard SOC |
| Email | **smtplib** (SMTP SSL) | Envoi automatique des alertes d'intrusion via Gmail |
| Configuration | **python-dotenv** | Chargement sécurisé des variables d'environnement (`.env`) |
| Tests / Diagnostic | `test_api.py` | Vérification de la clé API et des modèles Gemini disponibles |
| Environnement d'attaque | **Kali Linux** (VirtualBox) | Machine utilisée pour simuler les requêtes malveillantes (`curl`) |
| Versioning | **Git / GitHub** | Gestion de version et hébergement du dépôt |

---

## 📌 Key Concepts Covered

Ce projet met en pratique plusieurs concepts clés à l'intersection de la **cybersécurité**, du **Machine Learning** et de l'**IA générative** :

- **Sécurité applicative web** — middleware d'interception, gestion des requêtes entrantes, bannissement d'IP, réponses HTTP 403.
- **Détection d'intrusion (IDS)** — identification de motifs d'attaque courants : injection SQL, Cross-Site Scripting (XSS).
- **Détection d'anomalies par Machine Learning** — utilisation d'un modèle non supervisé (`IsolationForest`) pour repérer des comportements déviants sans étiquetage préalable.
- **IA générative comme moteur de décision (LLM-as-a-judge)** — un modèle de langage rend un verdict de sécurité motivé à partir d'une donnée brute, illustrant un pattern *"LLM-as-a-judge"*.
- **Stratégie de repli (fallback)** — bascule automatique vers une détection par patterns lorsque l'API IA est indisponible, pour garantir la continuité de la protection.
- **Journalisation et observabilité** — structuration des logs pour permettre l'analyse a posteriori et l'alimentation d'un dashboard temps réel.
- **Automatisation des alertes** — notification email déclenchée automatiquement par un événement de sécurité.
- **Visualisation de données de sécurité** — représentation graphique du niveau de menace dans le temps.
- **Gestion sécurisée des secrets** — séparation configuration / code via variables d'environnement (`.env`), exclusion via `.gitignore`.
- **Simulation d'attaque en environnement contrôlé** — usage d'une machine virtuelle Kali Linux pour reproduire un scénario d'intrusion réaliste sans risque.

---

## 📥 Installation

```bash
git clone https://github.com/Yasser-02G/security_agent.git
cd security_agent

python -m venv venv
source venv/bin/activate      # Windows : venv\Scripts\activate

pip install -r requirements.txt
```

---

## 🔑 Configuration

Copie le fichier d'exemple et renseigne tes propres identifiants :

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Clé API Google Gemini ([obtenir une clé sur AI Studio](https://aistudio.google.com/apikey)) |
| `GMAIL_USER` | Adresse Gmail utilisée comme expéditeur des alertes |
| `GMAIL_APP_PASSWORD` | [Mot de passe d'application](https://support.google.com/accounts/answer/185833) Gmail (16 caractères, **pas** ton mot de passe principal) |
| `RECIPIENT_EMAIL` | Adresse email destinataire des alertes de sécurité |

⚠️ **Le fichier `.env` réel ne doit jamais être commité** — il est déjà exclu via `.gitignore`.

Pour vérifier que ta clé Gemini est valide et lister les modèles disponibles :

```bash
python test_api.py
```

---

## 🚀 Lancement

```bash
python -m app.main
```

| Interface | URL |
|---|---|
| Site bancaire (client) | http://localhost:5000/ |
| Dashboard administrateur | http://localhost:5000/admin |

---

## 🧪 Tester une attaque

```bash
curl -X POST http://<IP_DU_SERVEUR>:5000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "SELECT * FROM users; DROP TABLE accounts; <script>alert(1)</script>"}'
```

Déroulement attendu :
1. Le middleware détecte l'anomalie (présence de `'` et `<`).
2. L'agent Gemini (ou le mode de secours) rend un verdict `BLOCK`.
3. L'IP source est bannie immédiatement.
4. L'événement est journalisé dans `logs/access.log`.
5. Une alerte email est envoyée au destinataire configuré.
6. Le dashboard affiche le pic d'attaque en temps réel.

---

## 📊 Dashboard de l'agent IA

Accessible sur `/admin`, il expose trois zones principales :

- **Analyse des flux (logs)** — graphique temps réel basé sur `/api/stats`.
- **IPs bloquées** — liste avec action de déblocage manuel (`/api/unblock`).
- **Rapports envoyés** — historique des alertes email.
- **Chat de l'agent** — interface conversationnelle (`/chat`) pour interroger les logs récents en langage naturel.

---

## ⚠️ Limites connues

- Le serveur Flask est lancé en **mode debug** — à ne jamais exposer ainsi en production.
- Les **features ML** sont volontairement simples (longueur, occurrences de caractères) à des fins pédagogiques ; un détecteur réel utiliserait des features bien plus riches (entropie, n-grams, géolocalisation IP, fréquence des requêtes...).
- Le **verdict Gemini** peut produire des faux positifs/négatifs et dépend de la disponibilité de l'API.
- Le **stockage est en mémoire** (`blocked_ips`, `sent_emails_log`) : tout est perdu au redémarrage du serveur.
- Pas d'authentification sur la route `/admin` dans cette version de démonstration.

## 🔭 Pistes d'amélioration

- Authentification et autorisation sur le dashboard.
- Persistance des IPs bloquées et des logs (base de données plutôt que fichier plat).
- Limitation de débit (rate limiting) en complément de la détection comportementale.
- Tableau de bord avec filtres par période, export des rapports, et alerting multi-canal (Slack, Telegram...).
- Tests automatisés (unitaires sur `ml_engine.py`, `ai_handler.py`, et tests d'intégration sur le middleware).

---

## ⚠️ Avertissement

Ce projet est un **prototype de démonstration / pédagogique**, réalisé dans un cadre d'apprentissage en cybersécurité et IA appliquée. Il n'est **pas conçu pour un usage en production** :

- Le serveur de développement Flask (`debug=True`) ne doit jamais être exposé publiquement.
- La détection par IA ne remplace pas un WAF (Web Application Firewall) ou un SOC professionnel.
- Toute clé API ou identifiant ayant pu être exposé pendant les phases de test doit être révoqué avant toute mise en ligne du dépôt.

---

## 👤 Author

**Yasser**

- GitHub : [@Yasser-02G](https://github.com/Yasser-02G)

N'hésite pas à ouvrir une *issue* ou une *pull request* si tu as des suggestions d'amélioration sur ce projet.

---

## 📄 Licence

Distribué sous licence MIT — libre à toi d'ajuster selon tes besoins.
