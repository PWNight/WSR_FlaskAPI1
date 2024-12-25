import calendar
import time
from flask import Flask, request, jsonify
from flaskext.mysql import MySQL
from passlib.hash import sha1_crypt
from flask_jwt_extended import (
    create_access_token, JWTManager, jwt_required
)

app = Flask(__name__)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'staff'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'
jwt = JWTManager(app)

mysql = MySQL()
mysql.init_app(app)
conn = mysql.connect()
cursor = conn.cursor()


@app.route("/api/v1/SignIn", methods=['POST'])
def sign_in():
    data = request.json
    if 'login' in data and 'password' in data:
        login = data['login']
        password = data['password']

        cursor.execute(f"SELECT * FROM users WHERE name = '{login}'")
        conn.commit()
        user_data = cursor.fetchone()
        if cursor.rowcount > 0:
            if sha1_crypt.verify(password,user_data[2]):
                access_token = create_access_token(identity=user_data[1])
                return jsonify(access_token=access_token)
            timestamp = calendar.timegm(time.gmtime())
            return jsonify(timestamp=timestamp, message="Неправильный пароль", errorCode="1400"), 400
        return jsonify(data), 400
    timestamp = calendar.timegm(time.gmtime())
    return jsonify(timestamp=timestamp,message="Отсутствует логин или пароль",errorCode="1400"), 400


@app.route("/api/v1/SignUp", methods=['POST'])
def sign_up():
    data = request.json
    if 'login' in data and 'password' in data and 'position' in data:
        login = data['login']
        password = data['password']
        position = data['position']

        cursor.execute(f"SELECT * FROM users WHERE name = '{login}'")
        conn.commit()
        if cursor.rowcount == 0:
            hashed_password = sha1_crypt.hash(password)
            cursor.execute(f"INSERT INTO users (name, password, position) VALUES (%s, %s, %s)", (login, hashed_password, position))
            conn.commit()

            access_token = create_access_token(identity=login)
            return jsonify(token=access_token)
        timestamp = calendar.timegm(time.gmtime())
        return jsonify(timestamp=timestamp, message="Пользователь уже существует", errorCode="1400"), 400
    timestamp = calendar.timegm(time.gmtime())
    return jsonify(timestamp=timestamp,message="Отсутствует логин или пароль",errorCode="1400"), 400


@app.route("/api/v1/Documents", methods=['GET'])
@jwt_required()
def get_documents():
    cursor.execute("SELECT * FROM documents")
    conn.commit()
    data = cursor.fetchall()

    if cursor.rowcount > 0:
        documents = []
        for row in data:
            document = {
                "id": row[0],
                "title": row[1],
                "date_created": row[2],
                "date_updated": row[3],
                "category": row[4],
                "has_comments": row[5]
            }
            documents.append(document)
        return jsonify(documents)
    timestamp = calendar.timegm(time.gmtime())
    return jsonify(timestamp=timestamp,message="Документы не найдены",errorCode="1404"), 404


@app.route("/api/v1/Documents/<document_id>/Comments", methods=['GET'])
@jwt_required()
def get_comments(document_id):
    cursor.execute(f"SELECT has_comments FROM documents WHERE id = '{document_id}'")
    conn.commit()
    data = cursor.fetchone()
    if cursor.rowcount > 0 and data[0]:
        cursor.execute(f"SELECT * FROM documents_comments WHERE fk_document = '{document_id}'")
        conn.commit()
        data = cursor.fetchall()

        comments = []
        for row in data:
            cursor.execute(f"SELECT * FROM users WHERE id = '{row[5]}'")
            conn.commit()
            data = cursor.fetchone()

            document = {
                "id": row[0],
                "document_id": row[1],
                "text": row[2],
                "date_created": row[3],
                "date_updated": row[4],
                "author": {
                    "name": data[1],
                    "position": data[3]
                }
            }
            comments.append(document)
        return jsonify(comments)
    timestamp = calendar.timegm(time.gmtime())
    return jsonify(timestamp=timestamp,message="Комментарии не найдены",errorCode="1404"), 404


if __name__ == '__main__':
    app.debug = True
    app.run()
