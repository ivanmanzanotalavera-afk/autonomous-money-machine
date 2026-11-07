import os
import json
import datetime
import subprocess
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("ERROR: No se ha encontrado GEMINI_API_KEY en GitHub Secrets.")

client = genai.Client(api_key=GEMINI_API_KEY.strip())

ACTIVE_MODEL = None

def call_gemini(prompt):
    global ACTIVE_MODEL
    if ACTIVE_MODEL:
        return client.models.generate_content(model=ACTIVE_MODEL, contents=prompt).text

    # Probamos directamente los modelos activos y todos los que liste tu cuenta (saltando el 2.5)
    candidates = [
        "gemini-3.0-flash",
        "gemini-3.8-flash",
        "gemini-flash-latest",
        "gemini-2.0-flash",
    ]
    try:
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if "gemini" in name.lower() and "embedding" not in name.lower() and "2.5" not in name:
                if name not in candidates:
                    candidates.append(name)
    except Exception as e:
        print(f"Aviso listando modelos: {e}")

    last_err = None
    for model_name in candidates:
        try:
            print(f"Probando modelo: {model_name}...")
            resp = client.models.generate_content(model=model_name, contents=prompt)
            if resp and resp.text:
                ACTIVE_MODEL = model_name
                print(f"EXITO con el modelo: {ACTIVE_MODEL}")
                return resp.text
        except Exception as e:
            print(f"Saltando {model_name}: {e}")
            last_err = e

    raise RuntimeError(f"Ningun modelo respondio. Ultimo error: {last_err}")

def run_autonomous_cycle():
    today = datetime.date.today().isoformat()
    os.makedirs("content/posts", exist_ok=True)
    os.makedirs("output_media", exist_ok=True)

    seo_prompt = (
        "Escribe un artículo práctico en Markdown comparando las 3 mejores herramientas gratuitas "
        "de automatización e IA para ahorrar tiempo y dinero en 2026. Incluye tabla comparativa y llamadas a la acción."
    )
    article_md
