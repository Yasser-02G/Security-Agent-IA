import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

class GeminiAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Clé API manquante dans le fichier .env")
        
        # Initialisation propre
        self.client = genai.Client(api_key=api_key)
        # Nom exact validé par votre script de diagnostic test_api.py
        self.model_name = 'gemini-flash-latest' # Adapter selon la disponibilité du modèle

    def chatbot_response(self, prompt, context=""):
        full_prompt = f"Logs récents:\n{context}\n\nQuestion: {prompt}"
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )
            return response.text
        except Exception as e:
            return f"Erreur IA ({self.model_name}) : {str(e)}"

    def analyze_and_judge(self, request_data):
        prompt = f"Réponds par BLOCK ou ALLOW. Est-ce une attaque ? : {request_data}"
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            decision = "BLOCK" if "BLOCK" in response.text.upper() else "ALLOW"
            return {"decision": decision, "reason": f"Analyse par {self.model_name}"}
        except Exception as e:
            print(f"⚠️ Mode secours : {e}")
            # Sécurité manuelle si l'API sature
            blacklist = ["'", "<", ">", "SELECT", "SCRIPT"]
            if any(x in request_data.upper() for x in blacklist):
                return {"decision": "BLOCK", "reason": "Détection par patterns (IA indisponible)"}
            return {"decision": "ALLOW", "reason": "Trafic normal"}