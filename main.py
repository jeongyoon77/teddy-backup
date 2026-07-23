import os
import time
from datetime import datetime
import cv2
from camera import (
    initialize_camera,
    initialize_detector,
    capture_frame,
    detect_objects,
    make_camera_data
)
from coss import (
    upload_data,
    watch_coss,
    TOF_CNT,
    CAMERA_CNT,
    GPS_CNT,
    BTN_CNT
)
from ToF import (
    initialize_arduino,
    read_arduino_data,
    make_tof_data
)
from hazard_zones import (
    init_db,
    record_obstacle,
    check_nearby_hazard,
    get_confirmed_zones
)
from speech import speak
import state
from dashboard import run_dashboard
import threading


camera = initialize_camera()
detector = initialize_detector()
arduino = initialize_arduino()

init_db()

latest_arduino_data = None
latest_coss_tof = None

latest_detected_frame = None
detected_objects = []

last_upload_time = 0
last_camera_upload_time = 0
last_warning_time = 0

WARNING_DISPLAY_SECONDS = 3
NO_DETECTION_RESET = 5

last_spoken_direction = None
last_detection_time = 0

# 같은 좌표라도 WARN_COOLDOWN 지나면 재경고 가능하도록 dict로 관리
warned_zones = {}          # {zone_key: last_warned_time} - 영구 유지, 중복 경고 방지용
walk_warned_zones = set()  # 이번 보행에서 경고 울린 좌표만 - 보행마다 리셋, 요약용

last_zone_check = 0
ZONE_CHECK_INTERVAL = 3
WARN_COOLDOWN = 300        # 같은 좌표 재경고까지 5분

direction_names = {
    "LEFT": "Left",
    "FRONT": "Front",
    "RIGHT": "Right"
}

direction_names_kr = {
    "LEFT": "왼쪽",
    "FRONT": "정면",
    "RIGHT": "오른쪽"
}

distance_keys = {
    "LEFT": "left_distance",
    "FRONT": "front_distance",
    "RIGHT": "right_distance"
}

# 실외 보행 중 실제로 마주칠 수 있는 장애물류만 추린 한글 매핑
object_names_kr = {
    "person": "사람",
    "bicycle": "자전거",
    "car": "자동차",
    "motorcycle": "오토바이",
    "bus": "버스",
    "truck": "트럭",
    "train": "기차",
    "traffic light": "신호등",
    "fire hydrant": "소화전",
    "stop sign": "정지 표지판",
    "parking meter": "주차 요금기",
    "bench": "벤치",
    "dog": "개",
    "cat": "고양이",
    "backpack": "가방",
    "umbrella": "우산",
    "handbag": "핸드백",
    "suitcase": "캐리어",
    "skateboard": "스케이트보드",
    "bottle": "병",
    "chair": "의자",
    "potted plant": "화분",
}


# ==================================================
# 보행 세션 상태 (음성 요약 및 팝업 리포트용, 메모리 상에서만 집계)
# ==================================================
walk_active = False
walk_start_time = None
walk_direction_counts = {"LEFT": 0, "FRONT": 0, "RIGHT": 0}
walk_object_counts = {}
walk_total_events = 0


def start_new_walk():
    global walk_active, walk_start_time
    global walk_direction_counts, walk_total_events
    global walk_warned_zones, walk_object_counts

    walk_active = True
    walk_start_time = time.time()
    walk_direction_counts = {"LEFT": 0, "FRONT": 0, "RIGHT": 0}
    walk_object_counts = {}
    walk_total_events = 0
    walk_warned_zones = set()

    state.set_walk_active(True)

    print(">>> 보행 시작")
    speak("Walk started")


def end_walk_and_report():
    global walk_active

    if not walk_active or walk_start_time is None:
        walk_active = False
        return

    walk_active = False
    state.set_walk_active(False)

    start_dt = datetime.fromtimestamp(walk_start_time)
    end_dt = datetime.now()
    duration_min = round((time.time() - walk_start_time) / 60)

    summary_lines = [
        f"오늘 {start_dt.strftime('%H:%M')}부터 {end_dt.strftime('%H:%M')}까지, "
        f"총 {duration_min}분 동안 이동했습니다.",
        f"이동 중 총 {walk_total_events}회의 가까운 장애물이 감지되었습니다."
    ]

    # 물체 종류 기준으로 가장 많이 감지된 것을 안내 (방향 대신 실제로 "무엇이었는지")
    if walk_object_counts:
        top_object = max(walk_object_counts, key=walk_object_counts.get)
        top_object_count = walk_object_counts[top_object]

        if top_object == "unknown object":
            display_name = "알 수 없는 장애물"
        else:
            display_name = object_names_kr.get(top_object, top_object)

        if top_object_count > 0:
            summary_lines.append(
                f"{display_name}이(가) {top_object_count}회로 가장 많이 감지되었습니다."
            )

    # 이번 보행에서 경고가 울린 좌표가 실제로 확정 위험구간과 겹치는지 확인
    if walk_warned_zones:
        confirmed = get_confirmed_zones()
        confirmed_keys = {
            (round(z["lat"], 4), round(z["lon"], 4)) for z in confirmed
        }
        hit_confirmed = walk_warned_zones & confirmed_keys

        if hit_confirmed:
            summary_lines.append(
                f"오늘 이동 중 이전에도 위험했던 구간을 {len(hit_confirmed)}곳 지나갔습니다."
            )
            summary_lines.append(
                "다음 이동 시 해당 구간에서 다시 한번 주의가 필요합니다."
            )
        else:
            summary_lines.append("오늘은 새로운 위험구간이 감지되지 않았습니다.")
    else:
        summary_lines.append("이번 보행에서는 특별한 위험구간이 감지되지 않았습니다.")

    summary_text = "\n".join(summary_lines)

    print(">>> 보행 종료:", summary_text)
    speak(summary_text)
    state.set_walk_summary(summary_text)


# COSS 판단 결과(방향)를 아두이노에 명령으로 전송 (서보/LED 실행용)
def send_direction_command(direction):
    try:
        arduino.write(f"CMD,{direction}\n".encode("utf-8"))
    except Exception as error:
        print("아두이노 명령 전송 실패:", error)


# COSS에서 받아온 ToF 거리값 중 지정한 threshold 이내로 가까워진 쪽이 있을 때만 그쪽으로 판별
def get_direction_from_tof(tof_data, threshold=100):
    left = tof_data.get("left_distance")
    front = tof_data.get("front_distance")
    right = tof_data.get("right_distance")

    values = {
        "LEFT": left if left is not None else 9999,
        "FRONT": front if front is not None else 9999,
        "RIGHT": right if right is not None else 9999
    }

    closest_direction = min(values, key=values.get)
    closest_distance = values[closest_direction]

    if closest_distance > threshold:
        return "FRONT"

    return closest_direction


# COSS의 최신 ToF와 카메라 데이터를 합쳐 위험할 때 음성 안내 + 대시보드 경고 갱신 + 서보 명령 전송
def use_coss_data():
    global latest_coss_tof
    global last_warning_time
    global last_spoken_direction
    global last_detection_time
    global walk_total_events

    for cnt_name, data in watch_coss():

        if cnt_name == BTN_CNT:
            state_value = data.get("state")

            if state_value == "STOP":
                end_walk_and_report()
            elif state_value == "START":
                start_new_walk()

            continue

        if cnt_name == GPS_CNT:
            state.set_location(data["lat"], data["lon"])
            continue

        if cnt_name == TOF_CNT:
            latest_coss_tof = data

            direction_for_servo = get_direction_from_tof(latest_coss_tof)
            send_direction_command(direction_for_servo)
            continue

        if cnt_name != CAMERA_CNT:
            continue
        if latest_coss_tof is None:
            continue

        current_time = time.time()

        direction = get_direction_from_tof(latest_coss_tof)

        if direction not in distance_keys:
            continue

        distance = latest_coss_tof.get(
            distance_keys[direction]
        )

        if distance is None:
            continue

        if distance > 100:
            continue

        gap_since_last_detection = current_time - last_detection_time

        should_speak = (
            direction != last_spoken_direction or
            gap_since_last_detection > NO_DETECTION_RESET
        )

        detected_name = data.get("object_name")
        object_name = detected_name if detected_name else "unknown object"

        distance_rounded = round(distance)
        direction_name = direction_names[direction]
        direction_name_kr = direction_names_kr[direction]

        if should_speak:
            message = f"Warning, {direction_name}, {object_name}, {distance_rounded} cm"

            dashboard_message = f"!주의! {direction_name_kr}에서 장애물 감지"
            state.set_warning(dashboard_message)

            loc = state.get_location()
            record_obstacle(loc["lat"], loc["lon"])

            speak(message)

            print("Voice alert:", message)

            last_warning_time = current_time
            last_spoken_direction = direction

            if walk_active:
                walk_total_events += 1
                if direction in walk_direction_counts:
                    walk_direction_counts[direction] += 1

                walk_object_counts[object_name] = (
                    walk_object_counts.get(object_name, 0) + 1
                )

        last_detection_time = current_time


coss_thread = threading.Thread(
    target=use_coss_data,
    daemon=True
)
coss_thread.start()

dashboard_thread = threading.Thread(
    target=run_dashboard,
    daemon=True
)
dashboard_thread.start()


try:
    while True:
        new_arduino_data, button_event = read_arduino_data(arduino)

        if new_arduino_data is not None:
            latest_arduino_data = new_arduino_data

        if button_event is not None:
            upload_data(
                BTN_CNT,
                {
                    "state": button_event,
                    "changed_at": datetime.now().isoformat()
                }
            )

        frame = capture_frame(camera)

        if frame is None:
            print("카메라 영상을 가져오지 못했습니다.")
            break

        should_detect = False

        if latest_arduino_data is not None:
            for key in ("left_distance", "front_distance", "right_distance"):
                value = latest_arduino_data.get(key)

                if value is not None and value <= 100:
                    should_detect = True
                    break

        if should_detect:
            detected_objects, latest_detected_frame = detect_objects(
                detector,
                frame
            )
        else:
            detected_objects = []

        detected_frame = (
            latest_detected_frame
            if latest_detected_frame is not None
            else frame
        )

        success, jpeg = cv2.imencode(".jpg", detected_frame)

        if success:
            state.set_frame(jpeg.tobytes())

        if latest_arduino_data is not None:
            state.set_distances(
                latest_arduino_data["left_distance"],
                latest_arduino_data["front_distance"],
                latest_arduino_data["right_distance"]
            )

        current_time = time.time()

        if current_time - last_warning_time > WARNING_DISPLAY_SECONDS:
            state.set_warning("-")

        if current_time - last_zone_check > ZONE_CHECK_INTERVAL:
            last_zone_check = current_time

            loc = state.get_location()

            if loc["lat"] is not None:
                zone_key = (
                    round(loc["lat"], 4),
                    round(loc["lon"], 4)
                )

                last_warned = warned_zones.get(zone_key)
                cooldown_passed = (
                    last_warned is None or
                    (current_time - last_warned) > WARN_COOLDOWN
                )

                if cooldown_passed:
                    if check_nearby_hazard(loc["lat"], loc["lon"]):
                        speak("Warning, hazard zone ahead")
                        warned_zones[zone_key] = current_time
                        walk_warned_zones.add(zone_key)

        if current_time - last_upload_time >= 0.2:
            if latest_arduino_data is not None:
                tof_data = make_tof_data(
                    latest_arduino_data
                )

                upload_data(TOF_CNT, tof_data)

            last_upload_time = current_time

        if current_time - last_camera_upload_time >= 1:
            if latest_arduino_data is not None:
                camera_data = make_camera_data(
                    detected_objects,
                    latest_arduino_data["camera_direction"]
                )

                upload_data(CAMERA_CNT, camera_data)

            last_camera_upload_time = current_time


finally:
    camera.stop()
    arduino.close()
