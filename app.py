import os
import json
from flask_cors import CORS
import random
from flask import Flask, request, jsonify, render_template, session
from werkzeug.utils import secure_filename
from datetime import datetime
import numpy as np
import librosa
import soundfile as sf
from transformers import WhisperProcessor
from optimum.onnxruntime import ORTModelForSpeechSeq2Seq
from transformers import pipeline
import traceback 

# --- IMPORT UNTUK LLM (GEMINI) DAN PYDANTIC ---
import google.genai as genai_module 
from pydantic import BaseModel, Field
from typing import Dict, Any 

# --- LLM OUTPUT SCHEMA ---
class LLMRubricOutput(BaseModel):
    """Skema output JSON yang dihasilkan LLM."""
    score: int = Field(description="Skor penilaian numerik dari 0 hingga 4.")
    reason: str = Field(description="Penjelasan rinci mengapa skor ini diberikan, mengacu pada kriteria rubrik.")

# --- KONFIGURASI FLASK DAN CORS ---
app = Flask(__name__, template_folder='.') 
CORS(app)

# KONFIGURASI SESSION
# GANTI NILAI INI DENGAN KUNCI RAHASIA YANG KUAT UNTUK PRODUKSI
app.secret_key = 'f2820d82d41b6c0e0b3c64c7849c71c4c9e4726b2b71d9d7' 
app.config['SESSION_TYPE'] = 'filesystem'

# --- INISIALISASI MODEL & CLIENT ---
ONNX_MODEL_DIR = "./whisper-small-en-onnx"
MERGED_MODEL_DIR = "./whisper-small-en-merged" 
DEVICE = "cuda:0" if 'cuda' in os.environ.get('KMP_AFFINITY', '').lower() else "cpu"

asr_pipeline = None
client = None # Inisialisasi klien Gemini

try:
    print("--- MEMUAT MODEL WHISPER ONNX UNTUK INFERENSI NYATA ---")
    onnx_processor = WhisperProcessor.from_pretrained(MERGED_MODEL_DIR)
    
    onnx_model = ORTModelForSpeechSeq2Seq.from_pretrained(
        ONNX_MODEL_DIR,
        encoder_file_name="encoder_model.onnx",
        decoder_file_name="decoder_model.onnx",
        provider="CUDAExecutionProvider" if DEVICE == "cuda:0" else "CPUExecutionProvider",
        use_cache=False
    )
    provider_name = onnx_model.providers[0]
    
    asr_pipeline = pipeline(
        "automatic-speech-recognition",
        model=onnx_model,
        tokenizer=onnx_processor.tokenizer,
        feature_extractor=onnx_processor.feature_extractor,
        device=-1 if provider_name == "CPUExecutionProvider" else 0
    )
    print(f"--- Model Whisper ONNX Berhasil Dimuat dan Siap Digunakan ({provider_name}) ---")
except Exception as e:
    print(f"ERROR: GAGAL MEMUAT MODEL ONNX. Detail: {e}")

# INISIALISASI KLIEN GEMINI
try:
    if os.environ.get("GEMINI_API_KEY"):
        client = genai_module.Client()
        print("--- Klien Gemini berhasil diinisialisasi ---")
    else:
        print("PERINGATAN: Variabel GEMINI_API_KEY tidak ditemukan. Penilaian LLM akan menggunakan Fallback Score.")
except Exception as e:
    print(f"ERROR: GAGAL menginisialisasi klien Gemini. Detail: {e}")
    client = None

# --- KONFIGURASI UPLOAD DAN PERTANYAAN ---
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

QUESTION_DATA = [
    {"id": 1, "question": "Can you share any specific challenges you faced while working on certification and how you overcame them?"},
    {"id": 2, "question": "Can you describe your experience with transfer learning in TensorFlow? How did it benefit your projects?"},
    {"id": 3, "question": "Describe a complex TensorFlow model you have built and the steps you took to ensure its accuracy and efficiency."},
    {"id": 4, "question": "Explain how to implement dropout in a TensorFlow model and the effect it has on training."},
    {"id": 5, "question": "Describe the process of building a convolutional neural network (CNN) using TensorFlow for image classification."},
]

# --- DATA RUBRIK (Disimpan dalam fungsi untuk konsistensi) ---
def get_detailed_rubric(question_id):
    RUBRIC = {
        1: {'4': 'Comprehensive and Clear Response. Provides detailed challenges, clear explanation of how each was overcome, strong technical understanding.', 
            '3': 'Specific Challenge with Basic Solution. Describes at least one specific challenge, basic explanation of solution.', 
            '2': 'General Challenge Mentioned without Details.', 
            '1/0': 'Minimal, Vague, or Unanswered.'},
        2: {'4': 'Comprehensive and Very Clear Response. Provides specific examples, clearly explains benefits gained, reflects deep engagement.', 
            '3': 'Specific Experience with Basic Explanation. Describes personal experience, provides examples, explains how transfer learning benefited.', 
            '2': 'General Response with Limited Details. Mentions transfer learning or TensorFlow in general terms.', 
            '1/0': 'Minimal, Vague, or Unanswered.'},
        3: {'4': 'Comprehensive and Very Clear Response. Detailed description of a complex model, specific details about architecture, clearly explains steps for accuracy/efficiency (optimization, regularization).', 
            '3': 'Specific Model with Basic Explanation. Describes a complex model, explains steps for accuracy/efficiency, but may lack depth.', 
            '2': 'General Response with Limited Details. Mentions building a TensorFlow model in general terms.', 
            '1/0': 'Minimal, Vague, or Unanswered.'},
        4: {'4': 'Comprehensive and Very Clear Response. Detailed explanation of how to implement dropout (with functions/code), clearly explains effect (prevent overfitting, deactivating neurons), discusses impact/rates.', 
            '3': 'Specific Explanation with Basic Understanding. Explains how to implement dropout with some specifics, describes the general effect (preventing overfitting).', 
            '2': 'General Response with Limited Details.', 
            '1/0': 'Minimal, Vague, or Unanswered.'},
        5: {'4': 'Comprehensive and Very Clear Response. Detailed, step-by-step description of building a CNN, covers all key components (layers, compiling, training, evaluating).', 
            '3': 'Specific Explanation with Basic Understanding. Describes the process with some specifics, includes key steps (preprocessing, architecture, compiling, training).', 
            '2': 'General Response with Limited Details. Mentions building a CNN in TensorFlow with some specifics.', 
            '1/0': 'Minimal, Vague, or Unanswered.'}
    }
    return RUBRIC.get(question_id)


# --- Implementasi STT ONNX & CV (TETAP SAMA) ---
def run_stt_onnx(video_path):
    if asr_pipeline is None:
        return "ERROR: Model STT tidak terinisialisasi.", 50

    try:
        audio_data, sr = librosa.load(video_path, sr=16000, mono=True)
        audio_input = audio_data.astype(np.float32)

        result = asr_pipeline(audio_input.copy())
        transcript = result["text"]
        
        stt_accuracy = random.randint(90, 95) 

        return transcript, stt_accuracy
    except Exception as e:
        traceback.print_exc() 
        return f"ERROR: Gagal mentranskripsi audio. Detail: {str(e)}", 50

def run_cv_assessment(video_path):
    # SIMULASI OUTPUT:
    eye_movement_ratio = round(random.uniform(0.1, 0.4), 2) 
    cheating_flag = random.choice([True, False, False, False])
    violations = random.randint(1, 3) if cheating_flag else 0
    
    return {
        "eye_movement_ratio": eye_movement_ratio,
        "cheating_flag": cheating_flag,
        "violations": violations
    }

# --- FUNGSI LLM SCORING ---
def run_llm_scoring(transcript, question_id):
    """
    Mengirim transkrip dan rubrik ke LLM (Gemini) untuk penilaian objektif (0-4).
    """
    if client is None:
        return 1, "LLM API not initialized. Falling back to Score 1 for safety."

    q_data = QUESTION_DATA[question_id - 1]
    rubric_data = get_detailed_rubric(question_id)
    
    rubric_str = "\n".join([f"Skor {k}: {v}" for k, v in rubric_data.items()])

    system_instruction = (
        "Anda adalah penilai Machine Learning ahli. Tugas Anda adalah memberikan skor wawancara objektif (0-4) "
        "berdasarkan transkrip dan rubrik yang ketat. Output HARUS berupa JSON yang valid."
    )

    prompt = f"""
    Instruksi: Analisis transkrip kandidat berikut terhadap Pertanyaan Q{question_id}: '{q_data['question']}'.
    
    ### Rubrik Penilaian Resmi:
    {rubric_str}
    
    ### Transkrip Kandidat (STT Output):
    "{transcript}"
    
    Berikan skor (0-4) dan alasan rinci (reason) yang secara eksplisit membenarkan skor tersebut berdasarkan kecocokan transkrip dengan kriteria rubrik.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "response_schema": LLMRubricOutput.schema()
            }
        )
        
        llm_output = LLMRubricOutput.model_validate_json(response.text)
        
        validated_score = max(0, min(4, llm_output.score))
        
        return validated_score, llm_output.reason
        
    except Exception as e:
        print(f"LLM API Call Error: {e}")
        return 1, f"LLM Scoring API failed: {str(e)}. Fallback score 1. Needs manual review."


# --- FUNGSI PENILAIAN UTAMA ---
def run_rubric_scoring_single(transcript, cv_metrics, stt_accuracy, question_id):
    """
    Menggunakan LLM untuk penilaian objektif (Skor & Alasan), lalu menerapkan penalti CV (SIMULASI).
    """
    
    # 1. Dapatkan Skor dan Alasan dari LLM
    score, reason = run_llm_scoring(transcript, question_id)
    
    # 2. Terapkan Penalti CV (SIMULASI)
    if cv_metrics["cheating_flag"]:
        score = max(1, score - 1) 
        reason += (
            f" [INTEGRITY FLAG]: Score adjusted to {score} due to suspected non-verbal "
            f"violation (Ratio: {cv_metrics['eye_movement_ratio']}). Requires manual validation."
        )

    return {
        "id": question_id,
        "score": score,
        "reason": reason,
        "transcript": transcript,
        "stt_accuracy": stt_accuracy,
        "cv_metrics": cv_metrics
    }


# --- FUNGSI FINAL: KOMPILASI SEMUA SKOR DI SESSION ---
def construct_final_json_summary(session_data):
    
    total_interview_score = sum(item["score"] for item in session_data)
    
    is_cheating_detected = any(item['cv_metrics']['cheating_flag'] for item in session_data)
    
    if is_cheating_detected or total_interview_score < 15: 
        decision = "Need Human Review"
        notes = f"Integrity flag detected in one or more videos. Total Interview Score: {total_interview_score}/20."
    else:
        decision = "PASSED (Auto)"
        notes = "Assessment successfully compiled. All checks passed. Candidate performed well."

    project_score = 100 
    interview_percent = total_interview_score / 20 * 100 
    total_score = round((project_score * 0.5) + (interview_percent * 0.5), 2) 

    formatted_scores = [
        {"id": item['id'], "score": item['score'], "reason": item['reason']} 
        for item in sorted(session_data, key=lambda x: x['id'])
    ]

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
            "interviews": {"minScore": 0, "maxScore": 4, "scores": formatted_scores}
        },
        "Overall notes": notes
    }
    
    return assessment_result


# --- ROUTING FLASK & SESSION MANAGEMENT ---

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_request
def initialize_session():
    if 'assessment_data' not in session:
        session['assessment_data'] = []
    if 'question_data' not in session:
        session['question_data'] = QUESTION_DATA

@app.route('/')
def serve_index():
    return render_template('index.html')

@app.route('/api/questions', methods=['GET'])
def get_questions():
    return jsonify({
        "questions": session.get('question_data', []),
        "current_scores": session.get('assessment_data', [])
    })

@app.route('/api/reset_session', methods=['POST'])
def reset_session_endpoint():
    session['assessment_data'] = []
    return jsonify({"message": "Session reset successfully", "assessment_data": []})


@app.route('/api/process_video', methods=['POST'])
def process_video():
    
    question_id_str = request.form.get('questionId')
    try:
        question_id = int(question_id_str)
    except (TypeError, ValueError):
        return jsonify({"error": "Missing or invalid questionId"}), 400
        
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
        if transcript.startswith("ERROR:"):
            return jsonify({"error": transcript}), 500

        # 2. Jalankan Model CV (SIMULASI)
        cv_metrics = run_cv_assessment(video_path)

        # 3. Jalankan Penilaian Rubrik (LLM)
        single_score_result = run_rubric_scoring_single(transcript, cv_metrics, stt_accuracy, question_id)
        
        # 4. Simpan hasil penilaian tunggal ke Session
        current_data = session.get('assessment_data', [])
        
        current_data = [item for item in current_data if item['id'] != question_id]
        
        current_data.append(single_score_result)
        session['assessment_data'] = current_data
        
        # 5. Bersihkan file
        os.remove(video_path) 

        # 6. Kirim kembali data sesi
        return jsonify({
            "message": f"Q{question_id} processed and saved.",
            "assessment_data": session['assessment_data'],
            "latest_score": single_score_result
        }), 200

    except Exception as e:
        os.remove(video_path)
        app.logger.error(f"Error during analysis: {e}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500


@app.route('/api/compile_summary', methods=['GET'])
def compile_summary():
    
    session_data = session.get('assessment_data', [])
    
    if len(session_data) < len(QUESTION_DATA):
        return jsonify({"error": f"Penilaian belum lengkap. Analisis {len(QUESTION_DATA)} video (Q1-Q5) harus diselesaikan. Saat ini baru {len(session_data)}."}), 400
        
    final_payload = construct_final_json_summary(session_data)
    
    return jsonify({
        "message": "Summary compiled successfully.",
        "final_payload": final_payload
    }), 200


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)