from http import client
from flask import render_template, Flask, jsonify
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.laundry_jungle

app = Flask(__name__)

@app.route('/')
def signin():
    return render_template('signin.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

db.users.insert_one({'user_id':'kristi8041', 'username':'염혜지', 'password':'1111', 'sex':'female', 'team':'blue', 'room':'220', 'phone':'01036758041', 'washer':False, 'dryer':False})
db.users.insert_one({'user_id':'hieronimus92', 'username':'손창한', 'password':'1111', 'sex':'male', 'team':'blue', 'room':'510', 'phone':'01022224444', 'washer':False, 'dryer':False})
db.users.insert_one({'user_id':'hyunhong1012', 'username':'이현홍', 'password':'1111', 'sex':'male', 'team':'blue', 'room':'513', 'phone':'01011113333', 'washer':False, 'dryer':False})
db.users.insert_one({'user_id':'hana1111', 'username':'김하나', 'password':'1111', 'sex':'female', 'team':'blue', 'room':'217', 'phone':'01044445555', 'washer':False, 'dryer':False})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)