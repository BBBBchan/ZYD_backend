import requests


def upload_avatar(file):
    upload_api = 'https://sm.ms/api/upload'
    files = {'smfile': file}
    req = requests.post(upload_api, files=files)
    return req.json()['data']['url']


def upload_avatar_v1(file):
    file_path = '../static/avatar/' + file.filename  # need change this
    with open(file_path, 'wb') as f:
        f.write(file.read())
    from flask import url_for
    url = 'http://127.0.0.1:5000' + url_for("static", filename="avatar/{}".format(file.filename))
    return url

