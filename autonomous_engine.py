import os
import json
import datetime
import urllib.request
import subprocess

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4}
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))
        return result["candidates"][0]["content"]["parts"][0]["text"]

def run_autonomous_cycle():
    today = datetime.date.today().isoformat()
    os.makedirs("content/posts", exist_ok=True)
    os.makedirs("output_media", exist_ok=True)

    # 1. Artículo SEO de conversión
    seo_prompt = (
        "Escribe un artículo práctico en Markdown comparando las 3 mejores herramientas gratuitas "
        "de automatización e IA para ahorrar tiempo y dinero en 2026. Incluye tabla comparativa y llamadas a la acción."
    )
    article_md = call_gemini(seo_prompt)
    article_path = f"content/posts/articulo-{today}.md"
    with open(article_path, "w", encoding="utf-8") as f:
        f.write(article_md)

    # 2. Guion + Audio + Vídeo Vertical 1080x1920 (Sin Pexels, 100% FFmpeg nativo)
    script_prompt = (
        "Escribe un guion dinámico de 40 segundos (95 palabras) sobre cómo automatizar el control de gastos "
        "y tareas repetitivas sin saber programar. Devuelve SOLO el texto plano para locutar, sin títulos ni acotaciones."
    )
    script_text = call_gemini(script_prompt).strip().replace('"', '')
    audio_path = f"output_media/voice_{today}.mp3"
    video_path = f"output_media/short_{today}.mp4"

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

    # 3. Registro contable y de producción (ERP)
    log_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "status": "ACTIVE_SUCCESS",
        "assets": [article_path, video_path],
        "spent_eur": 0.0
    }
    with open("erp_ledger.json", "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(log_entry) + "\n")

if __name__ == "__main__":
    run_autonomous_cycle()
