"""
start_studio.py — Lanzador de RevienDocker.
`python src/start_studio.py` levanta el servidor local (puerto 8765) y abre el navegador.
La interfaz vive en web/index.html y el backend en src/app.py.
"""

from app import serve

if __name__ == "__main__":
    serve(open_browser=True)
