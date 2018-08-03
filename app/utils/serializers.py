import decimal

from app.models import db


def serializer(instance, args):
    """
    数据库模型的序列化器
    :param instance: 数据库实例
    :param args: 需要序列化的字段
    :return: 字典形式的序列化后的数据
    """
    data = {}
    for arg in args:
        temp = instance.__dict__[arg]
        if isinstance(temp, decimal.Decimal):
            temp = str(temp)
        data.update({arg: temp})
    return data


def save_or_not(instance, args, data):
    """
    当前端传来的字段的属性为可选的，此函数会将此次传来的数据和所有可修改的字段进行对照，只修改数据中有的字段
    :param instance: 数据库实例
    :param args: 可能需要序列化的字段
    :param data: 实际传来的数据
    """
    for arg in args:
        try:
            temp = data[arg]
        except:
            continue
        setattr(instance, arg, temp)
    db.session.add(instance)
    db.session.commit()
