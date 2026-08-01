# 🛡️ Security Agent IA — Real-time Intrusion Detection for a Banking Application

> An autonomous cybersecurity agent that combines **Machine Learning** (Isolation Forest) with an **LLM (Google Gemini)** to analyze, judge, and block malicious requests to a web application in real time — illustrated here on a simulated banking platform (**SecureBank**).

---

## 📌 Table of Contents

- [Context and Goal](#-context-and-goal)
- [Demo](#-demo)
- [Project Architecture](#-project-architecture)
- [How It Works](#-how-it-works)
- [Tools & Technologies](#-tools--technologies)
- [Key Concepts Covered](#-key-concepts-covered)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the App](#-running-the-app)
- [Testing an Attack](#-testing-an-attack)
- [AI Agent Dashboard](#-ai-agent-dashboard)
- [Known Limitations](#-known-limitations)
- [Roadmap](#-roadmap)
- [Disclaimer](#-disclaimer)
- [Author](#-author)
- [License](#-license)

---

## 🎯 Context and Goal

This project is an **educational prototype of an AI-assisted SOC (Security Operations Center)**. The idea is to answer a simple question: *can intrusion detection be delegated to a generative AI, as a complement to a classic Machine Learning model?*

The simulated scenario is that of an online bank (**SecureBank**) exposing a wire-transfer form and a customer chatbot. Every incoming request goes through a **security middleware** before reaching the application:

1. A lightweight ML model (**Isolation Forest**) does a first quick pass based on request features (length, presence of suspicious characters).
2. If the request is flagged as abnormal, it is forwarded to a **Gemini agent** which analyzes it in natural language and returns a reasoned verdict: `BLOCK` or `ALLOW`.
3. If blocked, the IP is banned, the event is logged, and an **email alert** is automatically sent to the administrator.
4. A **real-time dashboard** lets you visualize traffic, blocked IPs, the alert history, and chat with a bot that analyzes logs on demand.

---

## 🖥️ Demo

**Architecture overview**

Before diving into the scenario details, here is a global view of the pipeline: from log collection to automated actions (blocking, alerting, dashboard), through the AI analysis engine and the storage/observability layer.

![Project Architecture](Screenshots/architecture.png)

### Full scenario: from attack to automatic blocking

**1. The banking application running**

The client interface (`bank_index.html`) simulates a checking account with a wire-transfer form. Every submission passes through the security middleware, transparently for the user.

![SecureBank Interface](Screenshots/Capture%20d%E2%80%99%C3%A9cran%20%28101%29.png)

**2. Starting the Flask server**

The agent is started locally (debug mode) and listens on the network so it can be targeted by an attacking machine (here, a Kali Linux VM on the same network).

![Starting the Flask server](Screenshots/Capture%20d%E2%80%99%C3%A9cran%20%28100%29.png)

**3. Simulating an attack from Kali Linux**

A `curl` request injects a malicious payload combining **SQL injection** and **XSS** into the `/chat` endpoint:

```bash
curl -X POST http://192.168.56.1:5000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "SELECT * FROM users; DROP TABLE accounts; <script>alert(1)</script>"}'
```

![Attack from Kali Linux](Screenshots/Capture%20d%E2%80%99%C3%A9cran%20%28104%29.png)

**4. Immediate blocking — 403 error page**

The middleware intercepts the request, the ML model detects the anomaly, the Gemini agent confirms the `BLOCK` verdict, and the IP is immediately banned. Any subsequent request from that IP receives a 403 error page, including for static resources (a template error expected in this demo environment).

![Error page after blocking](Screenshots/Capture%20d%E2%80%99%C3%A9cran%20%28106%29.png)

**5. Dashboard — real-time attack visualization**

The admin dashboard shows the traffic chart: normal traffic appears in green, the critical spike from the detected attack appears in red. IP `192.168.56.102` is listed among the blocked IPs, and a report was automatically sent by email.

![Real-time dashboard](Screenshots/Capture%20d%E2%80%99%C3%A9cran%20%28105%29.png)

**6. Log-analysis chatbot**

The administrator can query the AI agent in natural language to get a summary of the day's security events, with timestamp, source IP, and blocking reason for each alert.

![Security analysis chatbot](Screenshots/Capture%20d%E2%80%99%C3%A9cran%20%28107%29.png)

**7. Email alert received**

Every blocking event automatically triggers a SOC alert email containing the date, the blocked IP, the attack type, and the AI model that issued the verdict.

![SOC alert email](Screenshots/Capture%20d%E2%80%99%C3%A9cran%20%28108%29.png)

---

## 🏗️ Project Architecture

```
security_agent/
│   .env.example          # Configuration template (copy to .env)
│   .gitignore
│   requirements.txt
│   test_api.py           # Diagnostic script: lists Gemini models available for the API key
│
├───app/
│   │   main.py           # Flask entry point: security middleware, routes, dashboard
│   │   config.py         # Centralized configuration loading (.env)
│   │   __init__.py
│   │
│   ├───services/
│   │       ai_handler.py     # Gemini agent: log chatbot + reasoned BLOCK/ALLOW verdict
│   │       ml_engine.py      # Isolation Forest model for anomaly detection
│   │       mail_sender.py    # Sends email alerts (Gmail SMTP SSL)
│   │       __init__.py
│   │
│   ├───static/           # CSS / JS for the banking site and dashboard
│   │       bank_style.css
│   │       dashboard_logic.js
│   │       dashboard_style.css
│   │       script.js
│   │       style.css
│   │
│   └───templates/
│           bank_index.html   # SecureBank client interface
│           dashboard.html    # Admin / SOC dashboard
│
├───logs/
│       access.log        # Request log: timestamp, IP, status, action, reason, score
│
└───Screenshots/          # Demo screenshots (see section above)
```

---

## ⚙️ How It Works

### 1. The security middleware (`app/main.py`)

Every incoming HTTP request (excluding static files and admin routes) passes through `security_middleware()` before reaching the application logic:

- Checks whether the source IP is already blacklisted (`blocked_ips`) → returns a 403 error directly.
- Extracts simple **features** from the request: total length, number of quotes (`'`), number of angle brackets (`<`).
- Computes a **preliminary threat score** (10 = normal, 50 = suspicious).

### 2. First filter: the ML model (`app/services/ml_engine.py`)

An `IsolationForest` (scikit-learn) trained on a "normal" dataset acts as the first anomaly detector. The presence of special characters (`'` or `<`) immediately forces the anomaly status, in addition to the model's judgment.

### 3. Second filter: the Gemini agent's verdict (`app/services/ai_handler.py`)

If an anomaly is detected, the raw request is forwarded to the **Gemini** model (`gemini-flash-latest`) with a prompt asking it to return a binary **BLOCK / ALLOW** verdict along with a justification.

> 🔁 **Fallback mode**: if the Gemini API is unavailable (quota, network error, etc.), a pattern-based detector (`'`, `<`, `>`, `SELECT`, `SCRIPT`) automatically takes over so that a suspicious request is never left unanswered.

### 4. Action and notification

- If the verdict is `BLOCK`: the IP is added to the blacklist, the event is logged with a critical score (95), and an **email alert** is sent via `smtplib` (Gmail SMTP SSL).
- If `ALLOW`: the request is logged with a moderate score (60) and allowed to continue.
- Any normal traffic (no anomaly) is logged with a low score (10).

### 5. Logging (`logs/access.log`)

Each log line follows this format:

```
timestamp|source_ip|path|status|action|reason|score
```

This log feeds both the `/api/stats` API (dashboard chart) and the analysis chatbot (`/chat`).

### 6. Admin dashboard (`/admin`)

A real-time interface (periodically refreshed) displays:
- A **traffic chart** (normal traffic in green, critical attacks in red).
- The list of **blocked IPs**, with a manual unblock button.
- The history of **email alerts sent**.
- A **chatbot** to query the AI agent in natural language about the current security status (e.g. *"did you detect an attack today?"*).

---

## 🛠️ Tools & Technologies

| Category | Tool / Technology | Role in the project |
|---|---|---|
| Language | **Python 3** | Main backend language |
| Web framework | **Flask** | Application server, routes, security middleware |
| Machine Learning | **scikit-learn** (`IsolationForest`) | Anomaly detection on incoming requests |
| Numerical computing | **NumPy / Pandas** | Handling features and log data |
| Generative AI | **Google Gemini** (`google-genai`) | Reasoned BLOCK/ALLOW verdict + log-analysis chatbot |
| Visualization | **Plotly** | Real-time traffic chart in the dashboard |
| Frontend | **HTML / CSS / JavaScript** (vanilla) | Banking interface (SecureBank) and SOC dashboard |
| Email | **smtplib** (SMTP SSL) | Automatic sending of intrusion alerts via Gmail |
| Configuration | **python-dotenv** | Secure loading of environment variables (`.env`) |
| Testing / Diagnostics | `test_api.py` | Verifies the API key and lists available Gemini models |
| Attack environment | **Kali Linux** (VirtualBox) | Machine used to simulate malicious requests (`curl`) |
| Versioning | **Git / GitHub** | Version control and repository hosting |

---

## 📌 Key Concepts Covered

This project puts into practice several key concepts at the intersection of **cybersecurity**, **Machine Learning**, and **generative AI**:

- **Web application security** — interception middleware, handling of incoming requests, IP banning, HTTP 403 responses.
- **Intrusion Detection (IDS)** — identifying common attack patterns: SQL injection, Cross-Site Scripting (XSS).
- **ML-based anomaly detection** — using an unsupervised model (`IsolationForest`) to spot deviant behavior without prior labeling.
- **Generative AI as a decision engine (LLM-as-a-judge)** — a language model returns a reasoned security verdict from raw data, illustrating the *"LLM-as-a-judge"* pattern.
- **Fallback strategy** — automatic switch to pattern-based detection when the AI API is unavailable, ensuring continuous protection.
- **Logging and observability** — structuring logs to enable after-the-fact analysis and feed a real-time dashboard.
- **Alert automation** — email notification automatically triggered by a security event.
- **Security data visualization** — graphical representation of the threat level over time.
- **Secure secrets management** — separating configuration from code via environment variables (`.env`), excluded via `.gitignore`.
- **Attack simulation in a controlled environment** — using a Kali Linux virtual machine to reproduce a realistic intrusion scenario without risk.

---

## 📥 Installation

```bash
git clone https://github.com/<your-username>/security_agent.git
cd security_agent

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

---

## 🔑 Configuration

Copy the example file and fill in your own credentials:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key ([get one on AI Studio](https://aistudio.google.com/apikey)) |
| `GMAIL_USER` | Gmail address used as the alert sender |
| `GMAIL_APP_PASSWORD` | Gmail [app password](https://support.google.com/accounts/answer/185833) (16 characters, **not** your main password) |
| `RECIPIENT_EMAIL` | Email address that receives security alerts |

⚠️ **The actual `.env` file must never be committed** — it is already excluded via `.gitignore`.

To verify your Gemini key is valid and list the available models:

```bash
python test_api.py
```

---

## 🚀 Running the App

```bash
python -m app.main
```

| Interface | URL |
|---|---|
| Banking site (client) | http://localhost:5000/ |
| Admin dashboard | http://localhost:5000/admin |

---

## 🧪 Testing an Attack

```bash
curl -X POST http://<SERVER_IP>:5000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "SELECT * FROM users; DROP TABLE accounts; <script>alert(1)</script>"}'
```

Expected flow:
1. The middleware detects the anomaly (presence of `'` and `<`).
2. The Gemini agent (or the fallback mode) returns a `BLOCK` verdict.
3. The source IP is banned immediately.
4. The event is logged in `logs/access.log`.
5. An email alert is sent to the configured recipient.
6. The dashboard shows the attack spike in real time.

---

## 📊 AI Agent Dashboard

Accessible at `/admin`, it exposes three main areas:

- **Traffic analysis (logs)** — real-time chart based on `/api/stats`.
- **Blocked IPs** — list with a manual unblock action (`/api/unblock`).
- **Sent reports** — email alert history.
- **Agent chat** — conversational interface (`/chat`) to query recent logs in natural language.

---

## ⚠️ Known Limitations

- The Flask server runs in **debug mode** — never expose it this way in production.
- The **ML features** are intentionally simple (length, character counts) for educational purposes; a real detector would use much richer features (entropy, n-grams, IP geolocation, request frequency, etc.).
- The **Gemini verdict** can produce false positives/negatives and depends on API availability.
- **Storage is in-memory** (`blocked_ips`, `sent_emails_log`): everything is lost on server restart.
- No authentication on the `/admin` route in this demo version.

## 🔭 Roadmap

- Authentication and authorization on the dashboard.
- Persistence of blocked IPs and logs (database instead of a flat file).
- Rate limiting as a complement to behavioral detection.
- Dashboard with time-period filters, report export, and multi-channel alerting (Slack, Telegram, etc.).
- Automated tests (unit tests for `ml_engine.py`, `ai_handler.py`, and integration tests for the middleware).

---

## ⚠️ Disclaimer

This project is a **demo / educational prototype**, built as part of a learning exercise in cybersecurity and applied AI. It is **not designed for production use**:

- The Flask development server (`debug=True`) must never be exposed publicly.
- AI-based detection does not replace a WAF (Web Application Firewall) or a professional SOC.
- Any API key or credential that may have been exposed during testing must be revoked before the repository goes live.

---

## 👤 Author

**Yasser**

- GitHub: [@Yasser-02G](https://github.com/Yasser-02G)

Feel free to open an *issue* or a *pull request* if you have suggestions for improving this project.

---

## 📄 License

Distributed under the MIT license — feel free to adjust it to your needs.
