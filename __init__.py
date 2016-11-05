import os
from .handlers import LandingHandler, RequestHandler

# Jupyter Extension points
def _jupyter_server_extension_paths():
    return [{
        'module': 'interact',
    }]

def _jupyter_nbextension_paths():
    return [{
        "section": "notebook",
        "dest": "interact",
        "src": "app/static",
        "require": "interact/script"
    }]

def load_jupyter_server_extension(nbapp):
    # https://jupyter-notebook.readthedocs.io/en/latest/extending/handlers.html
    web_app = nbapp.web_app
    host_pattern = '.*$'
    base_url = web_app.settings['base_url']
    web_app.add_handlers(host_pattern, [(base_url, LandingHandler), (base_url[:-1], LandingHandler), (base_url + r'socket/(\S+)', RequestHandler)])
    
