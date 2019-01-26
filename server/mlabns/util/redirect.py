from mlabns.db import model

_redirect = None

def get_redirection():
    """Returns a cached redirect probability instance."""
    global _redirect
    if _redirect is None:
        update_redirection()
    return _redirect

def update_redirection():
    """Reloads the redirect probability instance from Datastore."""
    global _redirect
    _redirect = model.get_redirect_probability()