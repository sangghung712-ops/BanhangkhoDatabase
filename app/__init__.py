import os
from flask import Flask
from dotenv import load_dotenv


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY")

    from .routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)
    
    from .routes.customer_routes import customer_bp
    app.register_blueprint(customer_bp)

    from .routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp)
    return app