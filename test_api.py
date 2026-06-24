import os
from google import genai
from dotenv import load_dotenv

# Charge la clé depuis votre .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Erreur : Clé GEMINI_API_KEY introuvable dans le fichier .env")
    exit()

print("🔍 Interrogation de Google pour lister VOS modèles autorisés...\n")

try:
    client = genai.Client(api_key=api_key)
    # Demande la liste de tous les modèles disponibles pour votre clé
    models = client.models.list()
    
    print("✅ Voici les modèles que vous POUVEZ utiliser :")
    print("-" * 40)
    for m in models:
        # On affiche uniquement le nom brut du modèle (ex: gemini-1.5-flash)
        model_name = m.name.replace('models/', '')
        print(f"- {model_name}")
    print("-" * 40)
    
except Exception as e:
    print(f"❌ Impossible de lister les modèles. Erreur : {e}")