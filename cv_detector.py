import cv2
from ultralytics import YOLO
import math
import os
import traceback
import torch

# ========================= MODEL INITIALIZATION =========================
CV_MODEL_PATH = "computer_vision_model/yolo11n-pose.pt"
POSE_MODEL = None 

CV_DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu' 
print(f"Menggunakan Perangkat CV: {CV_DEVICE}")

try:
    # Cek apakah file model ada
    if not os.path.exists(CV_MODEL_PATH):
        CV_MODEL_PATH = "yolo11n-pose.pt" # Fallback ke root
        if not os.path.exists(CV_MODEL_PATH):
             raise FileNotFoundError(f"Model file not found at {CV_MODEL_PATH}")

    # Pemuatan model hanya sekali saat server start
    POSE_MODEL = YOLO(CV_MODEL_PATH)
    print("--- Model YOLO-Pose Berhasil Dimuat (Global) ---")
except Exception as e:
    print(f"ERROR: Gagal memuat model YOLO-Pose. Detail: {e}")


# Keypoint IDs: Nose (0), Right Eye (1), Left Eye (2)
NOSE_KP_ID = 0
RIGHT_EYE_KP_ID = 1
LEFT_EYE_KP_ID = 2
THRESHOLD = 15 # Threshold deviasi horizontal (dalam piksel, dapat disesuaikan)
FRAME_SKIP_RATE = 5 # Sampling: Proses 1 dari setiap 5 frame (efisiensi)

# ========================= UTILITY FUNCTIONS =========================
def get_gaze_direction(kp):
    """
    Menghitung arah pandangan (gaze) berdasarkan keypoint hidung, mata kanan, dan mata kiri.
    """
    # 1. Pastikan keypoint penting tersedia
    if kp[NOSE_KP_ID] is None or kp[RIGHT_EYE_KP_ID] is None or kp[LEFT_EYE_KP_ID] is None:
        return "Unknown", 0.0

    nose = kp[NOSE_KP_ID]
    right_eye = kp[RIGHT_EYE_KP_ID]
    left_eye = kp[LEFT_EYE_KP_ID]

    nx, ny = nose[:2]
    rx, ry = right_eye[:2]
    lx, ly = left_eye[:2]

    center_eye_x = (rx + lx) / 2
    diff_x = nx - center_eye_x
    
    # Logika Arah Pandangan (Horizontal)
    if diff_x > THRESHOLD:
        gaze = "Looking Left (Away)"
    elif diff_x < -THRESHOLD:
        gaze = "Looking Right (Away)"
    else:
        gaze = "Looking Forward"
    
    # Confidence dihitung berdasarkan deviasi relatif terhadap jarak antar mata
    eye_distance = math.sqrt((rx - lx)**2 + (ry - ly)**2)
    
    if eye_distance < 30: # Jika wajah terlalu jauh
        confidence = 0.0 
    else:
        relative_deviasi = abs(diff_x) / eye_distance 
        confidence = min(relative_deviasi * 1.5, 1.0) 

    return gaze, round(confidence, 2)


# ================= MAIN CV ASSESSMENT FUNCTION =================
def run_cv_assessment(video_path):
    """
    Memproses video untuk menghitung rasio frame yang tidak melihat ke depan.
    """
    # Penanganan error yang spesifik
    if POSE_MODEL is None:
        return {
            "eye_movement_ratio": 1.0, 
            "cheating_flag": True,
            "violations": 1,
            "error": "CV Model (YOLO-Pose) failed to initialize due to missing model file or dependencies."
        }
        
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {
            "eye_movement_ratio": 1.0,
            "cheating_flag": True,
            "violations": 1,
            "error": "Failed to open video file."
        }

    total_frames = 0
    away_gaze_frames = 0
    processed_frames_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            total_frames += 1

            # OPTIMASI: Lewati beberapa frame untuk kecepatan (Sampling)
            if total_frames % FRAME_SKIP_RATE != 0:
                continue
            
            processed_frames_count += 1

            # YOLO Pose Inference
            # Mode 'stream=True' dapat meningkatkan throughput
            results = POSE_MODEL(frame, verbose=False, device=CV_DEVICE, stream=True)

            for r in results:
                # Hanya memproses hasil dari orang pertama yang terdeteksi
                if r.keypoints is None or len(r.keypoints.xy) == 0:
                    continue
                
                # Ambil keypoints dari orang pertama yang terdeteksi
                keypoints = r.keypoints.xy[0].cpu().numpy() 
                
                if len(keypoints) < 3:
                    continue

                kp = {
                    NOSE_KP_ID: keypoints[NOSE_KP_ID],
                    RIGHT_EYE_KP_ID: keypoints[RIGHT_EYE_KP_ID],
                    LEFT_EYE_KP_ID: keypoints[LEFT_EYE_KP_ID],
                }

                gaze, conf = get_gaze_direction(kp)

                # Hitung frame 'away' hanya pada frame yang di-sampling dan memiliki confidence tinggi
                if gaze != "Looking Forward" and conf > 0.5: 
                    away_gaze_frames += 1
                
                # KELUAR dari loop 'for r in results' setelah mendeteksi orang pertama
                break 
    
    except Exception as e:
        traceback.print_exc()
        return {
            "eye_movement_ratio": 1.0,
            "cheating_flag": True,
            "violations": 1,
            "error": f"CV Runtime Error: {str(e)}"
        }
    finally:
        cap.release()
    
    if processed_frames_count == 0:
        return {
            "eye_movement_ratio": 0.0,
            "cheating_flag": False,
            "violations": 0,
            "error": "Video too short or no face detected in sampled frames."
        }

    not_looking_ratio = (away_gaze_frames / processed_frames_count)
    
    # Logika Penentuan Kecurangan
    # Jika ratio > 20% (dapat disesuaikan) dianggap potensi curang
    INTEGRITY_THRESHOLD = 0.20
    is_cheating = not_looking_ratio > INTEGRITY_THRESHOLD
    # Violations sebanding dengan rasio pergerakan mata, dibulatkan ke atas
    violations_count = math.ceil(not_looking_ratio * 10) 

    return {
        "eye_movement_ratio": round(not_looking_ratio, 2),
        "cheating_flag": is_cheating,
        "violations": violations_count,
        "error": None
    }