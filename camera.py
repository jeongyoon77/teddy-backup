from datetime import datetime
from picamera2 import Picamera2
from ultralytics import YOLO


# 카메라 시작
def initialize_camera():
    camera = Picamera2()
    config = camera.create_video_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    )
    camera.configure(config)
    camera.start()

    return camera


# 객체탐지 모델 불러오기
def initialize_detector(model_path="yolo26n.pt"):
    return YOLO(model_path)


# 카메라 영상 한 장 가져오기
def capture_frame(camera):
    try:
        frame = camera.capture_array()
        return frame
    except Exception:
        return None


# 객체탐지
def detect_objects(detector, frame, confidence=0.5):
    results = detector.predict(
        source=frame,
        conf=confidence,
        imgsz=320,
        verbose=False
    )

    result = results[0]
    detected_objects = []

    if result.boxes is not None:
        for box in result.boxes:
            class_id = int(box.cls[0].item())
            object_name = result.names[class_id]
            object_confidence = round(float(box.conf[0].item()), 3)

            x1, y1, x2, y2 = [
                int(value)
                for value in box.xyxy[0].tolist()
            ]

            detected_objects.append({
                "name": object_name,
                "confidence": object_confidence,
                "box": [x1, y1, x2, y2]
            })

    detected_frame = result.plot()

    return detected_objects, detected_frame


# 객체탐지 결과를 COSS에 올릴 형태로 정리
def make_camera_data(detected_objects, camera_direction):
    object_name = None

    if detected_objects:
        best_object = max(
            detected_objects,
            key=lambda obj: obj["confidence"]
        )
        object_name = best_object["name"]

    return {
        "camera_direction": camera_direction,
        "object_name": object_name,
        "measured_at": datetime.now().isoformat()
    }
