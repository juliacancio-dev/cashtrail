"""Servidor estático mínimo para testar o export do Next (equivale ao try_files do nginx do projeto)."""
import http.server
import os
import sys

ROOT = sys.argv[1]
PORT = int(sys.argv[2])


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def translate_path(self, path):
        resolved = super().translate_path(path)
        if os.path.isfile(resolved):
            return resolved
        if os.path.isfile(resolved + ".html"):
            return resolved + ".html"
        return resolved

    def log_message(self, *args):
        pass


http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
