from http import client
from types import NoneType
from flask import Flask, session, request, render_template, redirect, url_for
from pymongo import MongoClient
from message import sms

client = MongoClient("localhost", 27017)
db = client.laundry_jungle
app = Flask(__name__)
app.secret_key = b"kraftonjungle"


@app.route("/")
def login():
    if "user_id" in session:
        user_id = session["user_id"]
        return redirect("/main")
    else:
        return redirect("/signin")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "GET":
        return render_template("signin.html")
    else:
        user_id = request.form.get("user_id")
        password = request.form.get("password")

        user = db.users.find_one({"user_id": user_id})
        # Nonetype error 방지, 패스워드 일치 여부 확인
        if user_id and password and user and user["password"] == password:
            session["user_id"] = user_id
            return redirect("/main")
        else:
            return render_template("signin.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    else:
        user_id = request.form.get("user_id")
        username = request.form.get("username")
        password = request.form.get("password")
        sex = request.form.get("sex")
        team = request.form.get("team")
        room = request.form.get("room")
        phone = request.form.get("phone")

        user = {"user_id": user_id, "username": username, "password": password, "sex": sex, "team": team, "room": room, "phone": phone, "washer": False, "dryer": False}
        if db.users.find_one({"user_id": user_id}) is not NoneType:
            return render_template("signup.html")
        # user_id 중복검사
        # phone 숫자만, 중복 검사
        else:
            db.users.insert_one(user)
            return redirect("/signin")


@app.route("/main")
def main():
    session["id"] = "hyunhong1012"
    machine_list = list(db.machine.find({}, {"_id": 0}).sort("machine_id"))
    user = db.users.find_one({"user_id": session["id"]})
    # machine_list[0] == 'a_325', machin_list[1] == 'a_326', machine_list[2] == 'b_325', machine_list[3] == 'b_326'
    return render_template("main.html", machine_list=machine_list, user=user)


@app.route("/reservation", methods=["POST"])
def book():
    user = db.users.find_one({"user_id": session["id"]})
    machine = request.form.get("machine")
    alter = False if user[machine] else True
    db.users.update_one({"user_id": session["id"]}, {"$set": {machine: alter}})
    return redirect(url_for("main"))


@app.route("/logout")
def logout():
    session.pop("id", None)
    return redirect("/")


def alarm(machine: str, number: int):
    """
    유저에게 sms를 보내기 위해 호출하는 함수입니다. machine 정보를 washer 또는 dryer로 설정하면
    해당 기기를 예약한 유저들에게 문자를 보냅니다.
    """
    if not machine in ["washer", "dryer"]:
        return
    users = list(map(lambda x: x["phone"], list(db.users.find({machine: True}))))
    m = "세탁기" if machine == "washer" else "건조기"
    contents = [f"사용 가능 {m} 안내. https://www.laundry-jungle.com 링크로 접속해 선점하세요", f"{m} 사용 상태 자동 종료 안내. 분실 방지 및 다음 사용자를 위해 빠른 수거 바랍니다."]
    sms(users, contents[number])


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
