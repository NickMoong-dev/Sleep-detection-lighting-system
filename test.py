import cv2
import mediapipe as mp
import time
import math
import numpy as np
import socket
from PIL import ImageFont, ImageDraw, Image # 한글 출력을 위한 핵심 라이브러리

# --- [통신 설정] ---
RASPBERRY_IP = '192.168.0.103' 
PORT = 8888 

def send_wake_signal():
    """라즈베리파이로 무선 신호 전송"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3) 
        sock.connect((RASPBERRY_IP, PORT))
        
        sock.send("WAKE_UP".encode())
        print(f" [Wi-Fi] 라즈베리파이({RASPBERRY_IP})로 신호 전송 완료!")
        
        sock.close()
        return True
    except Exception as e:
        print(f" 전송 실패: {e}")
        return False

# --- [졸음 감지 로직] ---
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def calculate_ear(landmarks, eye_indices):
    left_point = landmarks[eye_indices[0]]
    right_point = landmarks[eye_indices[3]]
    top_mid = ((landmarks[eye_indices[1]].x + landmarks[eye_indices[2]].x) / 2,
               (landmarks[eye_indices[1]].y + landmarks[eye_indices[2]].y) / 2)
    bottom_mid = ((landmarks[eye_indices[4]].x + landmarks[eye_indices[5]].x) / 2,
                  (landmarks[eye_indices[4]].y + landmarks[eye_indices[5]].y) / 2)
    h_len = ((left_point.x - right_point.x) ** 2 + (left_point.y - right_point.y) ** 2) ** 0.5
    v_len = ((top_mid[0] - bottom_mid[0]) ** 2 + (top_mid[1] - bottom_mid[1]) ** 2) ** 0.5
    return v_len / h_len if h_len > 0 else 0

def calculate_mar(landmarks, mouth_indices):
    top_mid = ((landmarks[mouth_indices[0]].x + landmarks[mouth_indices[1]].x) / 2,
               (landmarks[mouth_indices[0]].y + landmarks[mouth_indices[1]].y) / 2)
    bottom_mid = ((landmarks[mouth_indices[2]].x + landmarks[mouth_indices[3]].x) / 2,
                  (landmarks[mouth_indices[2]].y + landmarks[mouth_indices[3]].y) / 2)
    left_point = landmarks[mouth_indices[4]]
    right_point = landmarks[mouth_indices[5]]
    h_len = ((left_point.x - right_point.x) ** 2 + (left_point.y - right_point.y) ** 2) ** 0.5
    v_len = ((top_mid[0] - bottom_mid[0]) ** 2 + (top_mid[1] - bottom_mid[1]) ** 2) ** 0.5
    return v_len / h_len if h_len > 0 else 0

def calculate_head_tilt(landmarks):
    left = landmarks[234]
    right = landmarks[454]
    dx = right.x - left.x
    dy = right.y - left.y
    return abs(math.degrees(math.atan2(dy, dx)))

cap = cv2.VideoCapture(0)

# [폰트 설정 미리 로드] - 루프 밖에서 한 번만 로드하는 것이 성능에 좋습니다.
try:
    # 윈도우 기본 폰트 (맑은 고딕)
    font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 32)
except:
    # 폰트가 없으면 기본 폰트 (한글 깨질 수 있음)
    font = ImageFont.load_default()

with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5) as face_mesh:
    
    EAR_THRESHOLD = 0.2
    CLOSED_EYES_FRAMES = 30
    MAR_THRESHOLD = 0.5
    OPEN_MOUTH_FRAMES = 30
    HEAD_TILT_THRESHOLD = 15
    HEAD_TILT_FRAMES = 30

    closed_eyes_frame_count = 0
    open_mouth_frame_count = 0
    head_tilt_frame_count = 0
    show_landmarks = True

    sleep_start_time = None
    DELAY_SECONDS = 5.0
    is_motor_activated = False

    while cap.isOpened():
        success, image = cap.read()
        if not success: break

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = face_mesh.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        current_alert = False

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                landmarks = face_landmarks.landmark
                
                left_eye_indices = [362, 385, 387, 263, 373, 380]
                right_eye_indices = [33, 160, 158, 133, 153, 144]
                mouth_indices = [13, 14, 17, 18, 78, 308]

                ear = (calculate_ear(landmarks, left_eye_indices) + calculate_ear(landmarks, right_eye_indices)) / 2.0
                mar = calculate_mar(landmarks, mouth_indices)
                tilt = calculate_head_tilt(landmarks)

                if ear < EAR_THRESHOLD: closed_eyes_frame_count += 1
                else: closed_eyes_frame_count = 0
                if mar > MAR_THRESHOLD: open_mouth_frame_count += 1
                else: open_mouth_frame_count = 0
                if tilt > HEAD_TILT_THRESHOLD: head_tilt_frame_count += 1
                else: head_tilt_frame_count = 0

                if (closed_eyes_frame_count >= CLOSED_EYES_FRAMES or 
                    open_mouth_frame_count >= OPEN_MOUTH_FRAMES or 
                    head_tilt_frame_count >= HEAD_TILT_FRAMES):
                    current_alert = True

                # --- [5초 딜레이 및 전송 로직] ---
                if current_alert:
                    if sleep_start_time is None:
                        sleep_start_time = time.time()
                    
                    elapsed = time.time() - sleep_start_time
                    countdown = max(0, DELAY_SECONDS - elapsed)
                    
                    # 카운트다운 표시 (OpenCV로 표시 - 숫자와 영어는 폰트 필요 없음)
                    cv2.putText(image, f"Motor in: {countdown:.1f}s", (50, 250), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)

                    if elapsed >= DELAY_SECONDS and not is_motor_activated:
                        send_wake_signal()
                        is_motor_activated = True
                else:
                    sleep_start_time = None
                    is_motor_activated = False

                # --- [한글 텍스트 출력 부분] ---
                # 1. OpenCV 이미지(BGR)를 PIL 이미지(RGB)로 변환
                pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(pil_image)

                # 2. 한글 텍스트 그리기
                status_text = f"상태: {' 수면 감지' if closed_eyes_frame_count >= CLOSED_EYES_FRAMES else '비 수면'}"
                # 글자색: 수면시 빨강, 정상시 파랑
                text_color = (255, 0, 0) if closed_eyes_frame_count >= CLOSED_EYES_FRAMES else (0, 0, 255)
                
                draw.text((50, 50), status_text, font=font, fill=text_color)
                
                # 상세 정보 표시 (하품, 자세)
                detail_text = f"하품: {open_mouth_frame_count} | 고개: {int(tilt)}°"
                draw.text((50, 100), detail_text, font=font, fill=(0, 255, 0))

                # 3. PIL 이미지를 다시 OpenCV 이미지(BGR)로 변환
                image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

                if show_landmarks:
                    mp_drawing.draw_landmarks(image=image, landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style())

        if current_alert:
            # 경고 시 화면 전체 붉은색 깜빡임 효과
            mask = np.zeros_like(image, dtype=np.uint8)
            mask[:] = (0, 0, 255)
            image = cv2.addWeighted(image, 0.7, mask, 0.3, 0)

        cv2.imshow('Sleep detection program', image)
        if cv2.waitKey(5) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()