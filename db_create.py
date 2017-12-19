from models import db


def create_db_schema():
    db.create_all()


if __name__ == "__main__":
    create_db_schema()