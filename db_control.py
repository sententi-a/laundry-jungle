from pymongo import MongoClient
from datetime import datetime

# 서버에는 아래 localhost → mongodb://test:test@localhost
client = MongoClient("localhost", 27017)
db = client.laundry_jungle

# machine collection에 총 4대의 세탁기, 건조기 정보 insert
machine_list = [
    {
        "machine_id": "a_325",
        "status": False,
        "user_id": "kristi8041",
        "username": "염혜지",
        "sex": "female",
        "team": "blue",
        "room": 220,
        "phone": "01036758041",
        "start_time": datetime(2022, 10, 25, 10, 11),
    },
    {
        "machine_id": "b_325",
        "status": True,
        "user_id": "hieronimus92",
        "username": "손창한",
        "sex": "male",
        "team": "blue",
        "room": 510,
        "phone": "01022224444",
        "start_time": datetime(2022, 10, 25, 12, 1),
    },
    {
        "machine_id": "a_326",
        "status": True,
        "user_id": "hyunhong1012",
        "username": "이현홍",
        "sex": "male",
        "team": "blue",
        "room": 513,
        "phone": "01011113333",
        "start_time": datetime(2022, 10, 25, 14, 20),
    },
    {"machine_id": "b_326", "status": False, "user_id": "hana1111", "username": "김하나", "sex": "female", "team": "blue", "room": 217, "phone": "01044445555", "start_time": datetime.now()},
]

machine_db = list(db.machine.find({}, {"_id": 0}).sort("machine_id"))

if len(machine_db) == 0:
    db.machine.insert_many(machine_list)


# 확인
machine_db = list(db.machine.find({}, {"_id": 0}).sort("machine_id"))
for machine in machine_db:
    print(machine)

# print(sorted(['a_325', 'b_326', 'a_326', 'b_325']))
