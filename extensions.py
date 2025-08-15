from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
# i tried putting this in app.py once, but then circular import, so just leave it here
# not sure if i need to configure anything else, docs say this is enough
# i saw on stackoverflow someone used a factory pattern, but that's too much for now
# if this breaks,  check flask-sqlalchemy version, i had issues with 3.x before