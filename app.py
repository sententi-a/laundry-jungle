from flask import Flask, session, request, render_template, redirect, url_for, flash
from pymongo import MongoClient
from datetime import datetime, timedelta
import atexit, csv, re, shutil
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from addon import sms

# 서버에는 아래 localhost → mongodb://test:test@localhost
client = MongoClient("localhost", 27017)
db = client.laundry_jungle
app = Flask(__name__)
app.secret_key = b"kraftonjungle"


def add_row(code, lst):
    with open(f"./log/{code}.csv", "a", newline="") as file:
        wr = csv.writer(file)
        wr.writerow(lst)


def send(machine: str):
    """
    예약 유저에게 sms를 보내기 위해 호출하는 함수입니다. machine 정보를 washer 또는 dryer로 설정하면
    해당 기기를 예약한 유저들에게 문자를 보냅니다.
    """
    if not machine in ["washer", "dryer"]:
        return TypeError
    users = list(map(lambda x: x["phone"], list(db.users.find({machine: True}))))
    m = "세탁기" if machine == "washer" else "건조기"
    content = f"사용 가능 {m} 안내. http://laundry-jungle.com 링크로 접속해 확인하세요"
    sms(users, content)


# scheduler → 서버에서 오류 발생하는 지 확인 필수
def auto_shutdown():
    """
    일정 시간마다 세탁기 및 건조기 시간을 검사하여 특정 시간 이상을 넘어섰을 경우 중단 및 예약자들에게 sms 전송
    """
    machines = ["a_325", "a_326", "b_325", "b_326"]
    for machine in machines:
        target = db.machine.find_one({"machine_id": machine})
        d = (datetime.now() - target["start_time"]) + timedelta(hours=9)
        content = "사용 상태 자동 종료 안내. 분실 방지 및 다음 사용자를 위해 빠른 수거 바랍니다."
        if d.seconds // 60 > 120 and (machine in ["b_325", "b_326"]) and target["status"] == False:
            sms([target["phone"]], "건조기" + content)
            send("dryer")
            db.machine.update_one({"machine_id": machine}, {"$set": {"status": True}})
        elif d.seconds // 60 > 90 and (machine in ["a_325", "a_326"]) and target["status"] == False:
            sms([target["phone"]], "세탁기" + content)
            send("washer")
            db.machine.update_one({"machine_id": machine}, {"$set": {"status": True}})


def cancel_reservation():
    """
    예약으로 발생하는 소요를 줄이기 위한 작업, 모든 예약 상태 False로 변경
    """
    users = list(db.users.find({"$or": [{"washer": True}, {"dryer": True}]}))
    numbers = list(map(lambda x: x["phone"], users))
    db.users.update_many({}, {"$set": {"washer": False, "dryer": False}})
    sms(numbers, "예약 취소되었습니다.")


def refresh_log():
    """
    로그 갱신을 위한 로직
    """
    codes = ["a_325", "a_326", "b_325", "b_326"]
    for code in codes:
        shutil.copy(f"./log/{code}.csv", f"./log/old/{code}.csv")
        df = pd.read_csv(f"./log/{code}")
        new_df = df.tail(2)
        new_df.to_csv(f"./log/{code}.csv", mode="w", index=False)


scheduler = BackgroundScheduler()
scheduler.add_job(func=auto_shutdown, trigger="interval", seconds=600)
scheduler.add_job(func=cancel_reservation, trigger="cron", week="1-53", day_of_week="0-6", hour="19")
scheduler.add_job(func=refresh_log, trigger="cron", month="1-12", day="20", hour="15", minute="0", second="0")
scheduler.start()
atexit.register(lambda: scheduler.shutdown())
# -----------------------------------------------------------------------------------------------


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
    elif request.method == "POST":
        user_id = request.form.get("user_id")
        password = request.form.get("password")

        user = db.users.find_one({"user_id": user_id})
        # id/pw 입력, 패스워드 일치 여부 확인
        if user_id and password and user and user["password"] == password:
            session["user_id"] = user_id
            flash("Welcome to laundry jungle!")
            return redirect("/main")
        else:
            flash("아이디나 비밀번호를 확인하세요")
            return render_template("signin.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    elif request.method == "POST":
        user_id = request.form.get("user_id")
        username = request.form.get("username")
        password = request.form.get("password")
        sex = request.form.get("sex")
        team = request.form.get("team")
        room = request.form.get("room")
        phone = request.form.get("phone")

        user = {"user_id": user_id, "username": username, "password": password, "sex": sex, "team": team, "room": room, "phone": phone, "washer": False, "dryer": False}
        id_exist = bool(db.users.find_one({"user_id": user_id}))

        room_valid = re.compile("[0-9]{3}").search(room.replace(" ", ""))
        phone_valid = re.compile("[0-9]{11}").search(phone.replace(" ", ""))
        id_valid = re.compile("[a-zA-Z0-9]{4,20}").search(user_id.replace(" ", ""))
        pw_valid = re.compile("[a-zA-Z0-9!@#$%^&*]{4,20}").search(password.replace(" ", ""))
        # 전체 입력 확인
        if not (user_id and username and password and sex and team and room and phone):
            flash("정보를 모두 입력해 주세요")
            return render_template("signup.html")
        # id 중복 검사
        elif id_exist:
            flash("이미 존재하는 ID입니다")
            return render_template("signup.html")
        # room 숫자, 길이 검사
        elif len(room) != 3 or not room_valid:
            flash("방 번호를 확인하세요")
            return render_template("signup.html")
        # phone 숫자, 길이 검사
        elif len(phone) != 11 or not phone_valid:
            flash("휴대폰 번호를 확인하세요")
            return render_template("signup.html")
        elif not id_valid:
            flash("아이디 생성 규칙을 확인하세요")
            return render_template("signup.html")
        elif not pw_valid:
            flash("비밀번호 생성 규칙을 확인하세요")
            return render_template("signup.html")
        else:
            db.users.insert_one(user)
            session["user_id"] = user_id
            flash("Wash and Survive")
            return redirect("/main")


@app.route("/main")
def main():
    if not "user_id" in session:
        return redirect("/")
    machine_list = list(db.machine.find({}, {"_id": 0}).sort("machine_id"))
    user = db.users.find_one({"user_id": session["user_id"]})
    # machine_list[0] == 'a_325', machin_list[1] == 'a_326', machine_list[2] == 'b_325', machine_list[3] == 'b_326'

    elapsed = [(datetime.now() + timedelta(hours=9) - machine["start_time"]).seconds // 60 for machine in machine_list]
    return render_template("main.html", machine_list=machine_list, elapsed=elapsed, user=user)


@app.route("/reservation", methods=["GET", "POST"])
def book():
    if not "user_id" in session:
        return redirect("/")
    if request.method == "GET":
        flash("비정상적인 접근입니다.")
        return redirect("/")
    user = db.users.find_one({"user_id": session["user_id"]})
    print(session["user_id"])
    machine = request.form.get("machine")
    alter = False if user[machine] else True
    db.users.update_one({"user_id": session["user_id"]}, {"$set": {machine: alter}})
    return redirect(url_for("main"))


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")


@app.route("/update", methods=["GET", "POST"])
def update():
    if not "user_id" in session:
        return redirect("/")
    if request.method == "GET":
        flash("비정상적인 접근입니다.")
        return redirect("/")
    code = request.form.get("machine")
    machine = db.machine.find_one({"machine_id": code})
    if machine["status"]:
        user = db.users.find_one({"user_id": session["user_id"]})
        db.machine.update_one(
            {"machine_id": code},
            {
                "$set": {
                    "status": False,
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "sex": user["sex"],
                    "team": user["team"],
                    "room": user["room"],
                    "phone": user["phone"],
                    "start_time": datetime.now() + timedelta(hours=9),
                }
            },
        )
        target = "washer" if code in ["a_325", "a_326"] else "dryer"
        db.users.update_one({"user_id": session["user_id"]}, {"$set": {target: False}})
        machine_data = db.machine.find_one({"machine_id": code})
        add_row(code, [machine_data["user_id"], machine_data["start_time"], machine_data["phone"]])
    else:
        flash("이미 사용 중입니다.")
    return redirect(url_for("main"))


@app.route("/finish", methods=["GET", "POST"])
def finish():
    if not "user_id" in session:
        return redirect("/")
    if request.method == "GET":
        flash("비정상적인 접근입니다.")
        return redirect("/")
    code = request.form.get("machine")
    db.machine.update_one({"machine_id": code}, {"$set": {"status": True}})
    target = "washer" if (code in ["a_325", "a_326"]) else "dryer"
    send(target)
    flash("사용이 종료되었습니다. 감사합니다.")
    return redirect(url_for("main"))


@app.route("/alert", methods=["GET", "POST"])
def alert():
    if not "user_id" in session:
        return redirect("/")
    if request.method == "GET":
        flash("비정상적인 접근입니다.")
        return redirect("/")
    code = request.form.get("machine")
    log = pd.read_csv(f"./log/{code}.csv", dtype=object)
    phone = list(log.tail(2)["phone"])[:1]
    target = "세탁기" if code in ["a_325", "a_326"] else "건조기"
    content = f"{target}에 남은 물품 수거 바랍니다."
    sms(phone, content)
    flash("회수 요청 메시지를 전송하였습니다.")
    return redirect(url_for("main"))


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
