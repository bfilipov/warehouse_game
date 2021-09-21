from app import db, create_app
from app import models

app = create_app()

app_dict = {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
app_dict.update({'db': db})


@app.shell_context_processor
def make_shell_context():
    return app_dict
