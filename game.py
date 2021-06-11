from app import app, db
from app import models


@app.shell_context_processor
def make_shell_context():
    return {k: v for k, v in models.__dict__.items() if isinstance(v, type)}
