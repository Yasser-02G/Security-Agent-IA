import os
import datetime
import smtplib
import time
from email.mime.text import MIMEText
from flask import Flask, render_template, request, jsonify
from app.services.ml_engine import SecurityML
from app.services.ai_handler import GeminiAgent

app = Flask(__name__, static_folder="static", template_folder="templates")

# --- CONFIGURATION ---
LOG_FILE = "logs/access.log"
# REMPLACEZ PAR VOS IDENTIFIANTS ET MOT DE PASSE D'APPLICATION 16 CARACTERES
SENDER_EMAIL = "votre_mail@gmail.com"
SENDER_PASSWORD = "votre_mot_de_passe_d_application"
RECEIVER_EMAIL = "votre_mail@gmail.com"

# Initialisation
ml = SecurityML()
ai = GeminiAgent()

# Stockage en mémoire
blocked_ips = set()
last_analysis_time = {}
# NOUVEAU : Liste pour stocker l'historique des emails envoyés
sent_emails_log = []


def send_alert_email(ip, attack_type, reason):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"🛡️ Blocage Intrusion - {ip}"
    content = f"🚨 ALERTE SOC\n\nDate: {timestamp}\nIP Bloquée: {ip}\nType: {attack_type}\nAnalyse: {reason}"
    msg = MIMEText(content)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    try:
        print(f"📧 Tentative d'envoi d'email à {RECEIVER_EMAIL}...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print("✅ Email envoyé avec succès !")
        # NOUVEAU : On enregistre l'envoi réussi
        sent_emails_log.append(
            {"date": timestamp, "to": RECEIVER_EMAIL, "subject": subject}
        )
    except Exception as e:
        print(f"❌ Erreur Mail critique : {e}")


def log_event(source, event, status, action, reason, score=0):
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # NOUVEAU : On ajoute le "score" dans les logs pour le graphique
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp}|{source}|{event}|{status}|{action}|{reason}|{score}\n")


# --- MIDDLEWARE DE SÉCURITÉ ---
@app.before_request
def security_middleware():
    if (
        request.path.startswith("/static")
        or request.path.startswith("/api")
        or request.path == "/admin"
    ):
        return

    client_ip = request.remote_addr
    if client_ip in blocked_ips:
        return render_template("error.html", error_message="Votre IP est bannie."), 403

    raw_data = request.path + str(request.get_data(as_text=True))
    features = [len(raw_data), raw_data.count("'"), raw_data.count("<")]

    # On calcule un score de base pour le graphique
    threat_score = 10  # Score de base faible
    if features[1] > 0 or features[2] > 0:
        threat_score = 50  # Suspect

    if ml.analyze_request(features):
        current_time = time.time()
        if client_ip in last_analysis_time and (
            current_time - last_analysis_time[client_ip] < 5
        ):
            return

        print(f"🔍 [SCAN] Anomalie détectée pour {client_ip}. Analyse Gemini...")
        last_analysis_time[client_ip] = current_time

        analysis = ai.analyze_and_judge(raw_data)
        print(f"⚖️ [VERDICT] {analysis['decision']}")

        if analysis["decision"] == "BLOCK":
            threat_score = 95  # Score critique
            blocked_ips.add(client_ip)
            log_event(
                client_ip,
                request.path,
                "CRITICAL",
                "BLOCK",
                analysis["reason"],
                threat_score,
            )
            send_alert_email(client_ip, "Cyber Attack", analysis["reason"])
            return render_template("error.html", error_message="IA: Accès refusé."), 403
        else:
            threat_score = 60  # Analysé mais autorisé

    log_event(client_ip, request.path, "OK", "ALLOW", "Trafic normal", threat_score)


# --- ROUTES ---
@app.route("/")
def home():
    return render_template("bank_index.html")


@app.route("/admin")
def admin():
    return render_template("dashboard.html")


# API pour les données du graphique
@app.route("/api/stats")
def get_stats():
    logs_data = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            # On prend les 30 dernières lignes
            for line in f.readlines()[-30:]:
                p = line.strip().split("|")
                # Compatibilité avec anciens et nouveaux logs (qui ont le score à la fin)
                score = int(p[6]) if len(p) >= 7 else (90 if p[4] == "BLOCK" else 10)
                logs_data.append(
                    {"time": p[0].split(" ")[1], "score": score, "ip": p[1]}
                )

    return jsonify(
        {
            "logs": logs_data,
            "blocked_ips": list(blocked_ips),
            "emails": sent_emails_log[-10:],  # Les 10 derniers emails
        }
    )


@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")
    log_context = ""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            log_context = "".join(f.readlines()[-10:])
    response = ai.chatbot_response(user_msg, context=log_context)
    return jsonify({"response": response})


@app.route("/api/unblock", methods=["POST"])
def unblock():
    target_ip = request.json.get("ip")
    if target_ip in blocked_ips:
        blocked_ips.remove(target_ip)
        return jsonify({"message": f"IP {target_ip} débloquée.", "status": "success"})
    return jsonify({"message": "IP non trouvée.", "status": "error"}), 404


if __name__ == "__main__":
    # Important pour le chargement des fichiers statiques
    app.run(host="0.0.0.0", port=5000, debug=True)
