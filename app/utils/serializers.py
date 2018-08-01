import decimal

from app.models import db


def serializer(instance, args):
    data = {}
    for arg in args:
        temp = instance.__dict__[arg]
        if isinstance(temp, decimal.Decimal):
            temp = str(temp)
        data.update({arg: temp})
    return data


def save_or_not(instance, args, data):
    for arg in args:
        try:
            temp = data[arg]
        except:
            continue
        setattr(instance, arg, temp)
    db.session.add(instance)
    db.session.commit()
    return 1
