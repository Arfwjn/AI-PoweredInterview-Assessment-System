# 🤖 AI-Powered Interview Assessment System (Capstone Project A25-CS349)

Sistem ini dikembangkan sebagai Capstone Project (Tim A25-CS349) untuk mengotomatisasi penilaian video wawancara, menggabungkan teknologi **Speech-to-Text (STT)**, **Large Language Models (LLM)** untuk penilaian objektif, dan analisis **Computer Vision (CV)**.

## ✨ Fitur Utama

- **Objective Rubric Scoring:** Menggunakan **Gemini LLM Hook** (via API) untuk memberikan skor rubrik (0-4) dan alasan (_reason_) yang sangat objektif berdasarkan kualitas transkripsi dan rubrik resmi.
- **STT Nyata & Optimasi:** Menggunakan model **Whisper ONNX** yang dioptimalkan untuk transkripsi audio yang cepat.
- **Akumulasi Sesi:** Mendukung _upload_ video per pertanyaan (Q1-Q5) dalam satu sesi, mengumpulkan semua skor sebelum membuat _payload_ JSON akhir.
- **Integrity Check (Simulated Hook):** Implementasi _hook_ untuk analisis non-verbal (Eye Movement) dari Computer Vision.

---

## 🛠️ Persyaratan Instalasi

### 1. Persyaratan Sistem Operasi & Tools

- **Python 3.11+**
- **FFMPEG:** Diperlukan oleh `librosa` untuk mengekstrak audio dari file video. **Wajib diinstal dan ditambahkan ke System PATH (CMD: Edit System Environment Variables)** Windows/OS Anda.
- **LLM API Key:** **GEMINI_API_KEY** (Wajib disiapkan sebagai variabel lingkungan untuk menjalankan Penilaian Objektif LLM).

### 2. Struktur Folder & Model

Pastikan proyek Anda memiliki struktur berikut:

interview_assessment_app/
├── app.py # Aplikasi Flask
├── requirements.txt # Daftar dependensi Python
├── index.html # Frontend UI
├── static/ # Assets (CSS, JS)
│ ├── css/
│ │ └── style.css # CSS
│ ├── js/
│ │ └── script.js # JS
│ ├── icons
│ │ └── (gambar/icon) # Icon
├── uploads/ # Folder untuk video yang diunggah
├── whisper-small-en-onnx/ # MODEL ONNX (encoder_model.onnx, decoder_model.onnx, ...)
└── whisper-small-en-merged/ # PROCESSOR (tokenizer.json, config.json, dll.)
└── computer_vision_model/ # MODEL CV (Masih simulasi, gunakan model CV Anda sendiri)

**Folder Tambahan:**
Anda bisa menambahkan folder:

1. uploads (tanpa isi)
2. whisper-small-en-merged
3. whisper-small-en-onnx
4. computer_vision_model (opsional, sekarang masih simulasi penilaian)

**Link Download Model & FFMPEG:**
Anda dapat mengunduh model ONNX dan FFMPEG di:
`https://drive.google.com/drive/folders/1goof4ua1n7VfZsfLzcbgUkTDdV1tb8Ff?usp=drive_link`

---

## 🚀 Panduan Menjalankan Proyek

### Langkah 1: Siapkan Lingkungan Python

Buka terminal di folder utama proyek dan buat serta aktifkan _virtual environment_:

===================================================

bash:

# Membuat venv (Sesuaikan nama environment Anda)

python -m venv venv_llm

# Mengaktifkan venv (Windows PowerShell)

.\venv_llm\Scripts\Activate.ps1

===================================================

### Langkah 2: Install Dependencies

===================================================

bash:

pip install -r requirements.txt

===================================================

### Langkah 3: Atur API LLM (Gemini 2.5 Flash)

===================================================

bash:

# Ganti dengan kunci Gemini rahasia Anda

set GEMINI_API_KEY="ISI_KUNCI_API_ANDA_DI_SINI"

===================================================

### Langkah 4: Jalankan Aplikasi Utama

===================================================

bash:

python app.py

===================================================

Jika berhasil, Anda akan melihat pesan "Klien Gemini berhasil diinisialisasi" dan alamat lokal (http://127.0.0.1:5000)

---

## 🛑 Troubleshooting:

### 1

**Masalah:**

- LLM API failed: 503 UNAVAILABLE

**Kemungkinan Penyebab:**

- API Gemini kelebihan beban atau kuota habis.

**Solusi:**

- Tunggu 5-10 menit dan coba ulang, atau periksa status/kuota API Anda.

### 2

**Masalah:**

- PERINGATAN: GEMINI_API_KEY tidak ditemukan

**Kemungkinan Penyebab:**

- Variabel lingkungan belum disetel.

**Solusi:**

- Ulangi Langkah 3. Pastikan Anda menggunakan set GEMINI_API_KEY=... di terminal yang aktif sebelum python app.py.

### 3

**Masalah:**

- audioread.NoBackendError

**Kemungkinan Penyebab:**

- FFMPEG tidak ditemukan di PATH sistem.

**Solusi:**

- Verifikasi bahwa Anda telah menambahkan jalur folder bin FFMPEG ke System PATH Windows Anda.

### 4

**Masalah:**

- "Import ""optimum..."" could not be resolved"

**Kemungkinan Penyebab:**

- Konflik namespace atau caching VS Code.

**Solusi:**

- Ulangi Langkah 1 dengan membuat venv baru.
