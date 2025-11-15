let selectedFile = null;

// Array pertanyaan (digunakan untuk labeling skor)
const QUESTIONS = [
  "Challenges faced and how you overcame them?",
  "Experience with transfer learning in TensorFlow?",
  "Describe a complex TensorFlow model you have built?",
  "Explain how to implement dropout in TensorFlow?",
  "Process of building a CNN using TensorFlow?",
];

// --- Fungsi Navigasi ---
function navigateTo(viewName) {
  // Hide all views
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.remove("active");
  });

  // Show selected view
  document.getElementById(viewName).classList.add("active");

  // Update nav links
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.classList.remove("active");
  });

  // Mencari link yang sesuai secara manual dan mengaktifkannya
  const targetLink = document.querySelector(`.nav-link[onclick*='${viewName}']`);
  if (targetLink) {
    targetLink.classList.add("active");
  }
}

// --- Penanganan File ---
function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) {
    selectedFile = file;
    document.getElementById("fileName").textContent = file.name;
    document.getElementById("fileSelected").style.display = "block";
  }
}

// --- Drag and Drop Handlers ---
const uploadZone = document.getElementById("uploadZone");
uploadZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadZone.classList.add("dragover");
});

uploadZone.addEventListener("dragleave", () => {
  uploadZone.classList.remove("dragover");
});

uploadZone.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadZone.classList.remove("dragover");
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    document.getElementById("videoInput").files = files;
    handleFileSelect({ target: { files } });
  }
});

// --- Fungsi Analisis Video (Perbaikan URL fetch) ---
async function analyzeVideo() {
  if (!selectedFile) {
    alert("Please select a video file first.");
    return;
  }

  const formData = new FormData();
  formData.append("videoFile", selectedFile);

  // Show loading
  document.getElementById("uploadZone").style.display = "none";
  document.getElementById("fileSelected").style.display = "none";
  document.getElementById("loadingIndicator").style.display = "block";

  try {
    // PERBAIKAN: Menggunakan URL RELATIF untuk menghindari konflik CORS/IP.
    // Ini akan mengirim request ke host dan port yang sama (e.g., 192.168.18.51:5000/api/analyze)
    const response = await fetch("/api/analyze", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      let errorDetail = response.statusText;
      try {
        const errorData = await response.json();
        errorDetail = errorData.error || errorDetail;
      } catch (e) {
        // Jika respons bukan JSON, gunakan status text
      }
      throw new Error(`Analysis failed: ${errorDetail}`);
    }

    const data = await response.json();
    displayResults(data);
  } catch (error) {
    console.error("Error:", error);
    alert(`Error analyzing video. Details: ${error.message}. Please check that the backend server is running and accessible.`);

    // Reset state
    document.getElementById("loadingIndicator").style.display = "none";
    document.getElementById("uploadZone").style.display = "block";
    document.getElementById("fileSelected").style.display = "block";
  }
}

// --- Fungsi Menampilkan Hasil ---
function displayResults(data) {
  // 1. Update STT Score
  document.getElementById("sttScore").textContent = Math.round(data.stt_accuracy) + "%";

  // 2. Update Cheating Alert & Violations
  const cheatingAlert = document.getElementById("cheatingAlert");
  if (data.cheating_flag) {
    cheatingAlert.innerHTML = '<div class="flag-warning">⚠️ <strong>Potential Integrity Concern Detected</strong><br>This assessment flagged potential violations. Please review details below.</div>';
  } else {
    cheatingAlert.innerHTML = '<div class="flag-success">✓ <strong>No Integrity Concerns</strong><br>Assessment passed integrity verification.</div>';
  }
  document.getElementById("violations").textContent = data.violations;

  // 3. Update Non-Verbal Analysis (Eye Movement)
  document.getElementById("eyeMovementRatio").textContent = data.eye_movement_ratio.toFixed(2);

  // 4. Update Overall Notes & Decision
  document.getElementById("finalDecision").textContent = data.decision;
  document.getElementById("overallNotes").textContent = data.overall_notes;

  // 5. Update Rubric Scores
  const rubricScoresDiv = document.getElementById("rubricScores");
  rubricScoresDiv.innerHTML = "";

  data.rubric_scores.forEach((score, index) => {
    const questionText = QUESTIONS[index] || `Question ${index + 1}`;
    const reason = data.rubric_reasons[index] || "Assessment reason missing.";

    rubricScoresDiv.innerHTML += `
            <div class="result-item">
                <div class="flex items-center justify-between mb-2">
                    <span class="font-semibold text-gray-900">Q${index + 1}: ${questionText}</span>
                    <span class="score-badge score-badge-${score}">${score}/4</span>
                </div>
                <p class="text-gray-600 text-sm italic">${reason}</p>
            </div>
        `;
  });

  // 6. Update Transcript
  document.getElementById("transcript").textContent = data.transcript;

  // 7. Download JSON
  const downloadBtn = document.getElementById("downloadJsonBtn");
  const jsonString = JSON.stringify(data.full_json_payload, null, 2);
  downloadBtn.onclick = () => {
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "assessment_result_" + data.full_json_payload.reviewedAt.split(" ")[0] + ".json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // 8. Hide loading and show results
  document.getElementById("loadingIndicator").style.display = "none";
  navigateTo("results");
}
