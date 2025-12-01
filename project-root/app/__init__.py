from flask import Flask
from config import Config
from models import init_db, db


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_object(Config)

    # initialize DB and models
    init_db(app)

    with app.app_context():
        from models import schema  # noqa: F401, ensure models are registered
        db.create_all()

        # seed default rooms if there are none
        from models.operations import ensure_default_rooms
        ensure_default_rooms()

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
