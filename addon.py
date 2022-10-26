import hmac, hashlib, base64
import time, requests, json


def sms(numbers: list, content: str):
    "numbers: List, content: String"
    with open("./key.json", "r") as j:
        data = json.load(j)

    service_id = data["service_id"]
    sms_uri = f"/sms/v2/services/{service_id}/messages"
    sms_url = f"https://sens.apigw.ntruss.com{sms_uri}"
    secret_key = data["secret_key"]
    access_id = data["access_id"]
    access_secret_key = bytes(data["access_secret_key"], "utf-8")

    stime = int(float(time.time()) * 1000)
    hash_str = f"POST {sms_uri}\n{stime}\n{access_id}"

    digest = hmac.new(access_secret_key, msg=hash_str.encode("utf-8"), digestmod=hashlib.sha256).digest()
    d_hash = base64.b64encode(digest).decode()

    from_no = "01041051012"
    to_numbers = numbers
    message = content

    msg_data = {"type": "SMS", "countryCode": "82", "from": f"{from_no}", "contentType": "COMM", "content": f"{message}", "messages": [{"to": f"{to_number}"} for to_number in to_numbers]}

    response = requests.post(
        sms_url,
        data=json.dumps(msg_data),
        headers={"Content-Type": "application/json; charset=utf-8", "x-ncp-apigw-timestamp": str(stime), "x-ncp-iam-access-key": access_id, "x-ncp-apigw-signature-v2": d_hash},
    )

    print(response.text)
