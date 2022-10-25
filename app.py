from http import client
from types import NoneType
from flask import Flask, session, request, render_template, redirect
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client.laundry_jungle
app = Flask(__name__)
app.secret_key = b"kraftonjungle"

@app.route('/')
def login():
    if 'user_id' in session:
        user_id = session['user_id']
        return redirect('/main')
    else:
        return redirect('/signin')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        return render_template('signin.html')
    else:
        user_id = request.form.get('user_id')
        password = request.form.get('password')

        user = db.users.find_one({'user_id':user_id})
        # Nonetype error 방지, 패스워드 일치 여부 확인
        if user_id and password and user and user['password'] == password:
            session['user_id'] = user_id
            return redirect('/main')
        else:
            return render_template('signin.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    else:
        user_id = request.form.get('user_id')
        username = request.form.get('username')
        password = request.form.get('password')
        sex = request.form.get('sex')
        team = request.form.get('team')
        room = request.form.get('room')
        phone = request.form.get('phone')
        
        user = {'user_id':user_id, 'username':username, 'password':password, 'sex':sex, 'team':team, 'room':room, 'phone':phone, 'washer':False, 'dryer':False}
        if db.users.find_one({'user_id':user_id}) is not NoneType:
            return render_template('signup.html')
        # user_id 중복검사
        # phone 숫자만, 중복 검사
        else:
            db.users.insert_one(user)
            return redirect('/signin')

@app.route('/main', methods=['GET', 'POST'])
def main():
    machine_list = list(db.machine.find({}, {"_id": 0}).sort("machine_id"))
    user = db.users.find_one({"user_id": "hyunhong1012"})
    return render_template("main.html", machine_list=machine_list, user=user["user_id"])

@app.route("/reservation")
def book():
    request.user
    user_list = db.users.find({"user_id":})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)