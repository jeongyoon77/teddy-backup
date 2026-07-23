import os
import time
from datetime import datetime
import serial
from dotenv import load_dotenv
load_dotenv()
ARDUINO_PORT = os.getenv("ARDUINO_PORT", "/dev/ttyACM0")
BAUD_RATE = int(os.getenv("ARDUINO_BAUD_RATE", "115200"))


# 아두이노 연결
def initialize_arduino():
    arduino = serial.Serial(
        port=ARDUINO_PORT,
        baudrate=BAUD_RATE,
        timeout=0.05
    )

    time.sleep(2)
    arduino.reset_input_buffer()

    return arduino


# 아두이노가 이미 cm 단위로 변환해서 보내므로, 실패값(-1)만 None으로 바꿔줌
def normalize_distance(value):
    if value < 0:
        return None

    return value


# 아두이노에서 새로 들어온 데이터 중 가장 최신 값 받기
def read_arduino_data(arduino):
    latest_data = None
    button_event = None

    while arduino.in_waiting > 0:
        line = arduino.readline().decode(
            "utf-8", errors="ignore"
        ).strip()

        if line.startswith("DATA,"):
            try:
                (
                    _, direction, left_cm, front_cm, right_cm
                ) = line.split(",")
                latest_data = {
                    "camera_direction": direction,
                    "left_distance": normalize_distance(int(left_cm)),
                    "front_distance": normalize_distance(int(front_cm)),
                    "right_distance": normalize_distance(int(right_cm)),
                    "measured_at": datetime.now().isoformat()
                }
            except ValueError:
                continue

        elif "정지 모드 진입" in line:
            button_event = "STOP"

        elif "동작 재개" in line:
            button_event = "START"

    return latest_data, button_event


# ToF 데이터만 COSS에 올릴 형태로 정리
def make_tof_data(arduino_data):
    return {
        "left_distance": arduino_data["left_distance"],
        "front_distance": arduino_data["front_distance"],
        "right_distance": arduino_data["right_distance"],
        "measured_at": arduino_data["measured_at"]
    }
