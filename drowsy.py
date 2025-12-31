import cv2
import mediapipe as mp
import time
import math
import numpy as np
from PIL import ImageFont, ImageDraw, Image

# MediaPipe 초기화
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# 졸음 감지를 위한 눈 비율 계산 함수
def calculate_ear(landmarks, eye_indices):
    left_point = landmarks[eye_indices[0]]
    right_point = landmarks[eye_indices[3]]
    top_mid = ((landmarks[eye_indices[1]].x + landmarks[eye_indices[2]].x) / 2,
               (landmarks[eye_indices[1]].y + landmarks[eye_indices[2]].y) / 2)
    bottom_mid = ((landmarks[eye_indices[4]].x + landmarks[eye_indices[5]].x) / 2,
                  (landmarks[eye_indices[4]].y + landmarks[eye_indices[5]].y) / 2)
    
    horizontal_length = ((left_point.x - right_point.x) ** 2 + (left_point.y - right_point.y) ** 2) ** 0.5
    vertical_length = ((top_mid[0] - bottom_mid[0]) ** 2 + (top_mid[1] - bottom_mid[1]) ** 2) ** 0.5
    return vertical_length / horizontal_length

# 하품 감지를 위한 입 비율 계산 함수
def calculate_mar(landmarks, mouth_indices):
    top_mid = ((landmarks[mouth_indices[0]].x + landmarks[mouth_indices[1]].x) / 2,
               (landmarks[mouth_indices[0]].y + landmarks[mouth_indices[1]].y) / 2)
    bottom_mid = ((landmarks[mouth_indices[2]].x + landmarks[mouth_indices[3]].x) / 2,
                  (landmarks[mouth_indices[2]].y + landmarks[mouth_indices[3]].y) / 2)
    left_point = landmarks[mouth_indices[4]]
    right_point = landmarks[mouth_indices[5]]
    
    horizontal_length = ((left_point.x - right_point.x) ** 2 + (left_point.y - right_point.y) ** 2) ** 0.5
    vertical_length = ((top_mid[0] - bottom_mid[0]) ** 2 + (top_mid[1] - bottom_mid[1]) ** 2) ** 0.5
    return vertical_length / horizontal_length

# 고개 기울기 계산 함수
def calculate_head_tilt(landmarks):
    left_shoulder = landmarks[234]
    right_shoulder = landmarks[454]
    
    dx = right_shoulder.x - left_shoulder.x
    dy = right_shoulder.y - left_shoulder.y
    angle = math.degrees(math.atan2(dy, dx))
    return abs(angle)

# 웹캠 열기
cap = cv2.VideoCapture(0)

# 얼굴 메시 모델 초기화
with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as face_mesh:
    
    closed_eyes_frame_count = 0
    open_mouth_frame_count = 0
    head_tilt_frame_count = 0
    EAR_THRESHOLD = 0.2  # 눈 비율 임계값, 눈이 닫힌 것으로 간주하는 기준
    CLOSED_EYES_FRAMES = 30  # 졸음으로 판단할 프레임 수
    MAR_THRESHOLD = 0.5  # 입 비율 임계값, 하품으로 간주하는 기준
    OPEN_MOUTH_FRAMES = 30  # 하품으로 판단할 프레임 수 (약 1초 기준)
    HEAD_TILT_THRESHOLD = 15  # 고개 기울기 각도 임계값
    HEAD_TILT_FRAMES = 30  # 고개 기울기 판단할 프레임 수 (약 1초 기준)

    show_landmarks = True

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("웹캠에서 영상을 읽을 수 없습니다.")
            break

        # BGR 이미지를 RGB로 변환
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        # 얼굴 메시 추론
        results = face_mesh.process(image)

        # 이미지를 다시 BGR로 변환
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        alert = False

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                landmarks = face_landmarks.landmark

                # 왼쪽 및 오른쪽 눈의 인덱스 (좌표는 MediaPipe의 얼굴 랜드마크 참조)
                left_eye_indices = [362, 385, 387, 263, 373, 380]
                right_eye_indices = [33, 160, 158, 133, 153, 144]

                # 입의 인덱스 (좌표는 MediaPipe의 얼굴 랜드마크 참조)
                mouth_indices = [13, 14, 17, 18, 78, 308]

                # 눈 비율 계산
                left_ear = calculate_ear(landmarks, left_eye_indices)
                right_ear = calculate_ear(landmarks, right_eye_indices)
                ear = (left_ear + right_ear) / 2.0

                # 입 비율 계산
                mar = calculate_mar(landmarks, mouth_indices)

                # 고개 기울기 각도 계산
                head_tilt_angle = calculate_head_tilt(landmarks)

                # 눈 비율에 따른 졸음 감지
                if ear < EAR_THRESHOLD:
                    closed_eyes_frame_count += 1
                else:
                    closed_eyes_frame_count = 0

                # 입 비율에 따른 하품 감지 (고개 기울기와 관계없이 동작하도록 수정)
                if mar > MAR_THRESHOLD:
                    open_mouth_frame_count += 1
                else:
                    open_mouth_frame_count = 0

                # 고개 기울기에 따른 기울기 감지
                if head_tilt_angle > HEAD_TILT_THRESHOLD:
                    head_tilt_frame_count += 1
                else:
                    head_tilt_frame_count = 0

                # 경고 조건 (개별 조건에 따라 별도로 알림 설정)
                if closed_eyes_frame_count >= CLOSED_EYES_FRAMES:
                    alert = True
                elif open_mouth_frame_count >= OPEN_MOUTH_FRAMES:
                    alert = True
                elif head_tilt_frame_count >= HEAD_TILT_FRAMES:
                    alert = True

                # 경고 메시지 O/X 표시
                pil_image = Image.fromarray(image)
                draw = ImageDraw.Draw(pil_image)
                font = ImageFont.truetype("NanumGothic.ttf", 32)  # 한글 폰트 지정
                draw.text((50, 50), f"수면: {'O' if closed_eyes_frame_count >= CLOSED_EYES_FRAMES else 'X'}", font=font, fill=(0, 0, 255))
                draw.text((50, 100), f"하품: {'O' if open_mouth_frame_count >= OPEN_MOUTH_FRAMES else 'X'}", font=font, fill=(0, 0, 255))
                draw.text((50, 150), f"자세: {'O' if head_tilt_frame_count >= HEAD_TILT_FRAMES else 'X'}", font=font, fill=(0, 0, 255))
                image = np.array(pil_image)

                # 얼굴 랜드마크 그리기 (토글 가능)
                if show_landmarks:
                    mp_drawing.draw_landmarks(
                        image=image,
                        landmark_list=face_landmarks,
                        connections=mp_face_mesh.FACEMESH_TESSELATION,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style())

        # 경고 화면 깜빡임 (붉은색 마스크 적용)
        if alert:
            mask = np.zeros_like(image, dtype=np.uint8)
            mask[:] = (0, 0, 255)
            image = cv2.addWeighted(image, 0.7, mask, 0.3, 0)

        # 결과 영상 출력
        cv2.imshow('DreamLight IoT System', image)

        key = cv2.waitKey(5) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('h'):
            show_landmarks = not show_landmarks

# 웹캠 해제 및 모든 창 닫기
cap.release()
cv2.destroyAllWindows()