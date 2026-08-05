import os

from app import create_app

app = create_app()

# Production security and logging
if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler

    if not os.path.exists("logs"):
        os.makedirs("logs")

    file_handler = RotatingFileHandler("logs/onice.log", maxBytes=10240, backupCount=10)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("On Ice startup")
