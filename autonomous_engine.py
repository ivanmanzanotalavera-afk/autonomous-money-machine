import os
import json
import datetime
import subprocess
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("ERROR: No se ha encontrado GEMINI_API_KEY en GitHub Secrets.")

client = genai.Client(
    api_key=GEMINI_API_KEY.strip(),
    http_options={"api_version": "v1beta"}
)

ACTIVE_MODEL = None

def call_gemini(prompt):
    global ACTIVE_MODEL
    if ACTIVE_MODEL:
        return client.models.generate_content(model=ACTIVE_MODEL, contents=prompt).text

    # Lista de candidatos en orden de prioridad + todos los modelos Gemini de tu cuenta
    candidates = [
        "gemini-flash-latest",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-pro-latest",
        "gemini-3.0-flash",
    ]
    for m in client.models.list():
        name = m.name.replace("models/", "")
        if "gemini" in name.lower() and "embedding" not in name.lower() and "2.5" not in name:
            if name not in candidates:
                candidates.append(name)

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
            print(f"Descartado {model_name}: {e}")
            last_err = e

    raise RuntimeError(f"Ningun modelo funciono. Ultimo error: {last_err}")

def run_autonomous_cycle():
    today = datetime.date.today().isoformat()
    os.makedirs("content/posts", exist_ok=True)
    os.makedirs("output_media", exist_ok=True)

    # 1. Generar artículo SEO
    seo_prompt = (
        "Escribe un artículo práctico en Markdown comparando las 3 mejores herramientas gratuitas "
        "de automatización e IA para ahorrar tiempo y dinero en 2026. Incluye tabla comparativa y llamadas a la acción."
    )
    article_md = call_gemini(seo_prompt)
    article_path = f"content/posts/articulo-{today}.md"
    with open(article_path, "w", encoding="utf-8") as f:
        f.write(article_md)

    # 2. Generar guion de vídeo corto
    script_prompt = (
        "Escribe un guion dinámico de 35 segundos (85 palabras) sobre cómo automatizar el control de gastos "
        "y tareas repetitivas sin saber programar. Devuelve SOLO el texto plano para locutar, sin títulos ni asteriscos."
    )
    script_text = call_gemini(script_prompt).strip().replace('"', '').replace('*', '')
    audio_path = f"output_media/voice_{today}.mp3"
    video_path = f"output_media/short_{today}.mp4"

    # 3. Voz neuronal + Vídeo vertical FFmpeg
    subprocess.run([
        "edge-tts", "--voice", "es-ES-AlvaroNeural", "--rate", "+10%",
        "--text", script_text, "--write-media", audio_path
    ], check=True)

    subprocess.run([
        "ffmpeg", "-y", "-i", audio_path,
        "-filter_complex", "[0:a]showwaves=s=1080x1920:mode=cline:rate=30:colors=0x10b981[v]",
        "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "fast",
        "-crf", "23", "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p", "-shortest", video_path
    ], check=True)

    # 4. Registro ERP
    log_entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model_used": ACTIVE_MODEL,
        "status": "ACTIVE_SUCCESS",
        "assets": [article_path, video_path],
        "spent_eur": 0.0
    }
    with open("erp_ledger.json", "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(log_entry) + "\n")

if __name__ == "__main__":
    run_autonomous_cycle()
