from sqlalchemy.orm import Session


def get_or_create(db: Session, model, filtre: dict, **attrs):
    obj = db.query(model).filter_by(**filtre).first()
    if obj:
        return obj
    obj = model(**filtre, **attrs)
    db.add(obj)
    db.flush()
    return obj
