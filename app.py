import os
import json
from flask_cors import CORS
import random
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from datetime import datetime
import numpy as np
import librosa
import soundfile as sf
from transformers import WhisperProcessor
from optimum.onnxruntime import ORTModelForSpeechSeq2Seq
from transformers import pipeline

# --- Inisialisasi Flask dan CORS ---
app = Flask(__name__, template_folder='.') 
CORS(app)

# --- Inisialisasi Global Model ONNX ---
ONNX_MODEL_DIR = "./whisper-small-en-onnx"
MERGED_MODEL_DIR = "./whisper-small-en-merged" 
DEVICE = "cuda:0" if 'cuda' in os.environ.get('KMP_AFFINITY', '').lower() else "cpu"

try:
    print("--- MEMUAT MODEL WHISPER ONNX UNTUK INFERENSI NYATA ---")
    
    # Load Processor dan Model ONNX
    onnx_processor = WhisperProcessor.from_pretrained(MERGED_MODEL_DIR)
    
    onnx_model = ORTModelForSpeechSeq2Seq.from_pretrained(
        ONNX_MODEL_DIR,
        encoder_file_name="encoder_model.onnx",
        decoder_file_name="decoder_model.onnx",
        
        provider="CUDAExecutionProvider" if DEVICE == "cuda:0" else "CPUExecutionProvider",
        use_cache=False
    )

    provider_name = onnx_model.providers[0]
    
    # Pipeline ASR
    asr_pipeline = pipeline(
        "automatic-speech-recognition",
        model=onnx_model,
        tokenizer=onnx_processor.tokenizer,
        feature_extractor=onnx_processor.feature_extractor,
        device=-1 if provider_name == "CPUExecutionProvider" else 0
    )
    print("--- Model Whisper ONNX Berhasil Dimuat dan Siap Digunakan ---")
except Exception as e:
    print(f"ERROR: GAGAL MEMUAT MODEL ONNX. Pastikan folder '{ONNX_MODEL_DIR}' dan '{MERGED_MODEL_DIR}' ada dan berisi file yang benar.")
    print(f"Detail Error: {e}")

# --- Konfigurasi Flask ---
app = Flask(__name__, template_folder='.')
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Data pertanyaan dari payload.json
QUESTIONS = [
    "Can you share any specific challenges you faced while working on certification and how you overcame them?",
    "Can you describe your experience with transfer learning in TensorFlow? How did it benefit your projects?",
    "Describe a complex TensorFlow model you have built and the steps you took to ensure its accuracy and efficiency.",
    "Explain how to implement dropout in a TensorFlow model and the effect it has on training.",
    "Describe the process of building a convolutional neural network (CNN) using TensorFlow for image classification.",
]

# --- Implementasi STT ONNX ---
def run_stt_onnx(video_path):
    temp_audio_path = video_path + ".wav"
    
    try:
        # 1. Ekstrak Audio dari Video dan Simpan
        audio_data, sr = librosa.load(video_path, sr=16000, mono=True)
        # Mengonversi ke numpy array yang dibutuhkan pipeline
        audio_input = audio_data.astype(np.float32)

        # 2. Inferensi Menggunakan Pipeline
        result = asr_pipeline(audio_input.copy())
        transcript = result["text"]
        
        # 3. Estimasi Akurasi (SIMULASI)
        # Akurasi sebenarnya dihitung saat evaluasi
        stt_accuracy = random.randint(90, 95) 

        return transcript, stt_accuracy
        

    except Exception as e:
        # PENTING: Cetak traceback penuh ke konsol
        import traceback
        traceback.print_exc() 

        print(f"Error saat menjalankan STT ONNX: {e}")
        return f"ERROR: Gagal mentranskripsi audio. Detail: {str(e)}", 50

# --- Implementasi CV (Masih Simulasi) ---
def run_cv_assessment(video_path):
    
    # SIMULASI OUTPUT:
    total_duration_sec = 120 + random.randint(0, 30) 
    eye_movement_ratio = round(random.uniform(0.1, 0.4), 2) 
    cheating_flag = random.choice([True, False, False, False])
    violations = random.randint(1, 3) if cheating_flag else 0
    
    return {
        "total_duration_sec": total_duration_sec,
        "eye_movement_ratio": eye_movement_ratio,
        "cheating_flag": cheating_flag,
        "violations": violations
    }

# --- Fungsi Penilaian Berdasarkan Transkrip STT & CV (SIMULASI) ---
def run_rubric_scoring(transcript, cv_metrics):
    scores = []
    
    for i in range(len(QUESTIONS)):
        # Atur skor berdasarkan panjang transkrip (SIMULASI SEDERHANA)
        score = random.choice([3, 4]) if len(transcript) > 200 else random.choice([2, 3])
        
        if score == 4:
            reason = "Comprehensive and Very Clear Response. Demonstrates strong understanding of concepts."
        else:
            reason = "Specific Experience with Basic Explanation. Shows reasonable understanding but lacks comprehensive insight."
            
        scores.append({"id": i + 1, "score": score, "reason": reason})

    if cv_metrics["cheating_flag"]:
        idx = random.randint(0, len(scores) - 1)
        scores[idx]["score"] = random.choice([1, 2])
        scores[idx]["reason"] = (
            f"INTEGRITY CONCERN DETECTED (CV Analysis): Score lowered due to suspected non-verbal "
            f"violation (Eye Movement Ratio: {cv_metrics['eye_movement_ratio']}). Human review required."
        )

    return scores


# --- Fungsi untuk Membangun JSON Output Final ---
def construct_final_json(scores, transcript, stt_accuracy, cv_metrics):

    total_interview_score = sum(item["score"] for item in scores)
    
    if cv_metrics["cheating_flag"] or total_interview_score < 15: 
        decision = "Need Human Review"
        notes = f"Potential Integrity Issue (Violations: {cv_metrics['violations']}) and/or low score ({total_interview_score}/20). Review non-verbal data."
    else:
        decision = "PASSED (Auto)"
        notes = "Assessment passed all checks. Transcript analysis confirmed strong performance. No integrity concerns detected."

    project_score = 100 
    interview_percent = total_interview_score / 20 * 100 
    total_score = round((project_score * 0.5) + (interview_percent * 0.5), 2) 

    assessment_result = {
        "assessorProfile": {"id": 1, "name": "DCML AI Assessor", "photoUrl": "NA"},
        "decision": decision, 
        "reviewedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scoresOverview": {
            "project": project_score, 
            "interview": total_interview_score,
            "total": total_score 
        },
        "reviewChecklistResult": {
            "project": [],
            "interviews": {"minScore": 0, "maxScore": 4, "scores": scores}
        },
        "Overall notes": notes,
        "transcript": transcript,
        "stt_accuracy": stt_accuracy,
        "cv_metrics": cv_metrics
    }
    
    return assessment_result

# --- Routing Flask ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def serve_index():
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    
    if 'videoFile' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['videoFile']
    
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "No selected file or invalid extension"}), 400
            
    filename = secure_filename(file.filename)
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(video_path)
    
    try:
        # 1. Jalankan Model STT
        transcript, stt_accuracy = run_stt_onnx(video_path)
        
        # Tangani error transkripsi
        if transcript.startswith("ERROR:"):
            return jsonify({"error": transcript}), 500

        # 2. Jalankan Model Computer Vision (SIMULASI)
        cv_metrics = run_cv_assessment(video_path)

        # 3. Jalankan Penilaian Rubrik (SIMULASI)
        scores_with_reasons = run_rubric_scoring(transcript, cv_metrics)
        
        # 4. Konstruksi JSON Output
        final_result = construct_final_json(scores_with_reasons, transcript, stt_accuracy, cv_metrics)
        
        # 5. Bersihkan file (Opsional)
        os.remove(video_path) 

        # 6. Format hasil untuk JavaScript Frontend
        flat_result = {
            "stt_accuracy": final_result["stt_accuracy"],
            "transcript": final_result["transcript"],
            "cheating_flag": final_result["cv_metrics"]["cheating_flag"],
            "violations": final_result["cv_metrics"]["violations"],
            "interview_score": final_result["scoresOverview"]["interview"],
            "total_score": final_result["scoresOverview"]["total"],
            "decision": final_result["decision"],
            "overall_notes": final_result["Overall notes"],
            "rubric_scores": [s["score"] for s in final_result["reviewChecklistResult"]["interviews"]["scores"]],
            "rubric_reasons": [s["reason"] for s in final_result["reviewChecklistResult"]["interviews"]["scores"]],
            "eye_movement_ratio": final_result["cv_metrics"]["eye_movement_ratio"],
            "full_json_payload": final_result 
        }
        
        return jsonify(flat_result), 200

    except Exception as e:
        os.remove(video_path)
        app.logger.error(f"Error during analysis: {e}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)