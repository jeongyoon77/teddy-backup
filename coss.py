import json
import os
import time
import uuid
from datetime import datetime
import requests
from dotenv import load_dotenv
load_dotenv(override=True)

_session = requests.Session()

COSS_BASE_URL = os.getenv("COSS_BASE_URL")
AE_NAME = os.getenv("AE_NAME")
ORIGIN = os.getenv("ORIGIN")
COSS_API_KEY = os.getenv("COSS_API_KEY")
COSS_CREATOR = os.getenv("COSS_CREATOR")
COSS_LECTURE = os.getenv("COSS_LECTURE")
TOF_CNT = os.getenv("TOF_CNT_NAME")
CAMERA_CNT = os.getenv("CAMERA_CNT_NAME")
GPS_CNT = os.getenv("GPS_CNT_NAME")
BTN_CNT = os.getenv("BTN_CNT_NAME")
LOG_PATH = "coss_log.jsonl"


# 업로드와 다운로드에서 같은 인증 코드를 반복하지 않고 요청마다 새 RI를 만들기 위해 사용
def make_headers(content_type=None):
    headers = {
        "X-M2M-Origin": ORIGIN,
        "X-M2M-RI": str(uuid.uuid4()),
        "X-M2M-RVI": "3",
        "X-API-KEY": COSS_API_KEY,
        "X-AUTH-CUSTOM-CREATOR": COSS_CREATOR,
        "X-AUTH-CUSTOM-LECTURE": COSS_LECTURE,
        "Accept": "application/vnd.onem2m-res+json"
    }

    if content_type is not None:
        headers["Content-Type"] = content_type

    return headers


# ToF와 camera 데이터를 각 COSS 컨테이너에 올릴 때 사용
def upload_data(cnt_name, data):
    url = f"{COSS_BASE_URL}/Mobius/{AE_NAME}/{cnt_name}"

    body = {
        "m2m:cin": {
            "con": json.dumps(data, ensure_ascii=False)
        }
    }

    try:
        response = _session.post(
            url,
            headers=make_headers(
                "application/vnd.onem2m-res+json;ty=4"
            ),
            json=body,
            timeout=5
        )

        response.raise_for_status()
        print(f"{cnt_name} 업로드 성공")
        return True

    except requests.RequestException as error:
        print(f"{cnt_name} 업로드 실패:", error)

        if error.response is not None:
            print(error.response.text)

        return False


# 컨테이너의 최신 데이터와 중복 확인용 RI를 한 번 가져올 때 사용
def download_latest_data(cnt_name):
    url = f"{COSS_BASE_URL}/Mobius/{AE_NAME}/{cnt_name}/la"

    try:
        response = _session.get(
            url,
            headers=make_headers(),
            timeout=5
        )

        response.raise_for_status()

        cin = response.json()["m2m:cin"]
        ri = cin["ri"]
        data = cin["con"]

        if isinstance(data, str):
            data = json.loads(data)

        return ri, data

    except requests.RequestException as error:
        print(f"{cnt_name} 다운로드 실패:", error)

        if error.response is not None:
            print(error.response.text)

        return None, None

    except (KeyError, json.JSONDecodeError):
        print(f"{cnt_name} 데이터 형식 오류")
        return None, None


# 새로 받은 값을 나중에 사용자 기록으로 활용할 수 있도록 파일에 누적할 때 사용
def save_data(cnt_name, ri, data):
    record = {
        "saved_at": datetime.now().isoformat(),
        "src_cnt": cnt_name,
        "cin_ri": ri,
        "data": data
    }

    with open(LOG_PATH, "a", encoding="utf-8") as file:
        file.write(
            json.dumps(record, ensure_ascii=False) + "\n"
        )


# 판단 코드가 새 COSS 값만 실시간으로 받고 같은 값을 기록 파일에도 저장하도록 계속 실행할 때 사용
def watch_coss(interval=0.3):
    cnt_list = [TOF_CNT, CAMERA_CNT, GPS_CNT, BTN_CNT]
    last_ri = {}

    while True:
        for cnt_name in cnt_list:
            ri, data = download_latest_data(cnt_name)

            if ri is None:
                continue

            if ri == last_ri.get(cnt_name):
                continue

            last_ri[cnt_name] = ri
            save_data(cnt_name, ri, data)

            yield cnt_name, data

        time.sleep(interval)


if __name__ == "__main__":
    try:
        for cnt_name, data in watch_coss():
            print(cnt_name, data)

    except KeyboardInterrupt:
        print("종료")
