🤖 AI-Powered Interview Assessment System (Capstone Project A25-CS349)
Sistem ini dikembangkan sebagai Capstone Project program Asah led by Dicoding & Accenture. Proyek ini bertujuan untuk mengotomatisasi evaluasi video wawancara dengan menggabungkan teknologi Speech-to-Text (STT) dan Computer Vision (CV) untuk meningkatkan skalabilitas dan objektivitas penilaian.

✨ Fitur Utama
Speech-to-Text (STT) Nyata: Menggunakan model Whisper ONNX yang telah di-fine-tune untuk transkripsi audio dari video wawancara.

Analisis Non-Verbal (SIMULASI SEMENTARA): Implementasi hook untuk integrasi model Computer Vision (Eye Movement Tracking) untuk penilaian integritas kandidat.

Penilaian Otomatis: Menghasilkan skor rubrik (0-4) dan Overall Notes sesuai dengan struktur payload Capstone.

Antarmuka Dashboard: Antarmuka web Flask dengan fitur drag-and-drop untuk upload video dan menampilkan hasil penilaian secara dashboard-style.

🛠️ Persyaratan Sistem
Pastikan Anda memiliki tool dan perangkat lunak berikut terinstal di sistem Anda:

A. Persyaratan Sistem Operasi
Python 3.11.9

FFMPEG: Diperlukan oleh librosa untuk mengekstrak audio dari file video. Pastikan FFMPEG terinstal dan jalur (ffmpeg.exe) telah ditambahkan ke Variabel Lingkungan (System PATH) Windows Anda.

B. Struktur Folder Proyek
Pastikan folder proyek Anda memiliki struktur dan file model yang benar:

interview_assessment_app/
├── app.py # Aplikasi Flask
├── requirements.txt # Daftar dependensi Python
├── index.html # Frontend UI
├── static/ # Assets (CSS, JS)
│ ├── css/
│ │ └── style.css
│ ├── js/
│ │ └── script.js
│ ├── icons
├── uploads/ # Folder untuk video yang diunggah
├── whisper-small-en-onnx/ # MODEL ONNX (encoder_model.onnx, decoder_model.onnx, ...)
└── whisper-small-en-merged/ # PROCESSOR (tokenizer.json, config.json, dll.)

Link untuk model dan ffmpeg bisa di download di:
https://drive.google.com/drive/folders/1goof4ua1n7VfZsfLzcbgUkTDdV1tb8Ff?usp=drive_link

🚀 Instalasi dan Menjalankan Proyek
Ikuti langkah-langkah ini secara berurutan untuk menyiapkan dan menjalankan aplikasi Flask.

Langkah 1: Siapkan Lingkungan Python
Buka terminal di folder utama proyek dan buat serta aktifkan lingkungan virtual:

Bash:

# Membuat venv (Windows)

python -m venv venv

# Mengaktifkan venv (PowerShell)

.\venv\Scripts\Activate.ps1

# Mengaktifkan venv (Linux/macOS)

source venv/bin/activate

Langkah 2: Instal Dependensi
Instal semua library Python yang dibutuhkan.

Bash:

pip install -r requirements.txt

# Jika Anda menggunakan Flask-CORS, pastikan juga terinstal.

Langkah 3: Jalankan Aplikasi Flask
Jalankan skrip utama app.py. Catatan: Kami menggunakan debug=False untuk menghindari MemoryError saat memuat model ONNX.

Bash:

python app.py
Setelah server dimulai, Anda akan melihat output yang menunjukkan pemuatan model dan alamat yang digunakan:

--- MEMUAT MODEL WHISPER ONNX UNTUK INFERENSI NYATA ---
...
--- Model Whisper ONNX Berhasil Dimuat dan Siap Digunakan ---

- Running on http://127.0.0.1:5000

Langkah 4: Akses Antarmuka Web
Buka browser Anda dan navigasikan ke alamat lokal:
http://127.0.0.1:5000/

Anda sekarang dapat mengunggah file video (MP4, WEBM, dll.) di halaman Assessment dan memulai proses penilaian.

💻 Integrasi Model (Lanjutan)
Integrasi Model Computer Vision (CV)
Saat ini, fungsi analisis non-verbal menggunakan simulasi. Untuk mengintegrasikan model CV Anda (Eye Movement Tracking), Anda harus memodifikasi fungsi di app.py:

Python:

# app.py

def run_cv_assessment(video_path):
"""
HOOK/SIMULASI: Ganti dengan logika deteksi wajah dan mata CV Anda.
Gunakan library seperti OpenCV (cv2) untuk memproses frame video.
"""

# ... (Tambahkan kode pemrosesan frame dan metrik CV di sini) ...

    return {
        "total_duration_sec": 150,
        "eye_movement_ratio": 0.25,
        "cheating_flag": False,
        "violations": 0
    }
