"""
start_studio.py — Lanzador de RevienDocker.
`python start_studio.py` levanta el servidor local (puerto 8765) y abre el navegador.
La interfaz vive en index.html y el backend en app.py.
"""

from app import serve

if __name__ == "__main__":
    serve(open_browser=True)
