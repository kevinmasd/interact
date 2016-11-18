from notebook.utils import url_path_join
from interact.handlers import LandingHandler, RequestHandler

# Jupyter Extension points
def _jupyter_server_extension_paths():
    return [{
        'module': 'interact',
    }]

def _jupyter_nbextension_paths():
    return [{
        "section": "notebook",
        "dest": "interact",
        "src": "static",
        "require": "interact/script"
    }]

def load_jupyter_server_extension(nbapp):
    # https://jupyter-notebook.readthedocs.io/en/latest/extending/handlers.html
    web_app = nbapp.web_app
    host_pattern = '.*$'
    base_url = url_path_join(web_app.settings['base_url'], "/interact")
    web_app.add_handlers(host_pattern, [(base_url, LandingHandler), (base_url[:-1], LandingHandler), (base_url + r'socket/(\S+)', RequestHandler)])
