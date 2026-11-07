import os
import json
import datetime
import subprocess
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("ERROR: No se ha encontrado GEMINI_API_KEY en GitHub Secrets.")

# Conectamos explícitamente a v1beta donde están los modelos más recientes
client = genai.Client(
    api_key=GEMINI_API_KEY.strip(),
    http_options={"api_version": "v1beta"}
)

def get_working_model():
    # Autodetecta los modelos disponibles en tu cuenta para no fallar nunca por 404
    available = []
    for m in client.models.list():
        actions = getattr(m, "supported_actions", []) or []
        if "generateContent" in actions or not actions:
            available.append(m.name)
    
    print("Modelos disponibles detectados en tu cuenta:", available)
    
    # Priorizamos cualquier variante de Gemini Flash disponible
    for preferred in ["gemini-3.0-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest"]:
        for name in available:
            if preferred in name:
                print(f"Usando modelo autodetectado: {name}")
                return name
                
    # Si tienen otro nombre, elige el primer modelo Gemini disponible
    for name in available:
        if "gemini" in name.lower() and "embedding" not in name.lower():
            print(f"Usando modelo alternativo: {name}")
            return name
            
    return available[0]

ACTIVE_MODEL = get_working_model()

def call_gemini(prompt):
    response = client.models.generate_content(
        model=ACTIVE_MODEL,
        contents=prompt,
    )
    return response.text

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
