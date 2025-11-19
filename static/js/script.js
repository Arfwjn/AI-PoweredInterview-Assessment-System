let selectedFile = null;
let questionData = []; // Menyimpan data pertanyaan dari backend

// Array pertanyaan
const QUESTIONS = [
  "Challenges faced and how you overcame them?",
  "Experience with transfer learning in TensorFlow?",
  "Describe a complex TensorFlow model you have built?",
  "Explain how to implement dropout in TensorFlow?",
  "Process of building a CNN using TensorFlow?",
];

// --- Fungsi Global dan Inisialisasi ---

document.addEventListener("DOMContentLoaded", async () => {
  // Panggil endpoint untuk mengambil data pertanyaan dan skor saat ini
  const response = await fetch("/api/questions");
  if (response.ok) {
    const data = await response.json();
    questionData = data.questions;

    // Inisialisasi dropdown dan history
    populateQuestionDropdown(questionData, data.current_scores);
    renderScoreHistory(data.current_scores, questionData);
    updateProgress(data.current_scores.length);
  } else {
    console.error("Failed to load question data from backend. Check Flask server status.");
  }
});

// Menemukan data pertanyaan berdasarkan ID
function getQuestionById(id) {
  return questionData.find((q) => q.id === parseInt(id));
}

// --- Manajemen Tampilan dan Navigasi ---

function navigateTo(viewName) {
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.remove("active");
  });
  document.getElementById(viewName).classList.add("active");

  document.querySelectorAll(".nav-link").forEach((link) => {
    link.classList.remove("active");
  });
  const targetLink = document.querySelector(`.nav-link[onclick*='${viewName}']`);
  if (targetLink) {
    targetLink.classList.add("active");
  }
}

function confirmReset() {
  if (confirm("Are you sure you want to start a new session? This will erase all analyzed scores (Q1-Q5) currently stored.")) {
    resetSession();
  }
}

async function resetSession() {
  await fetch("/api/reset_session", { method: "POST" });
  alert("New session started. All previous scores have been cleared.");
  window.location.reload();
}

function resetAssessment() {
  selectedFile = null;
  document.getElementById("videoInput").value = "";
  document.getElementById("uploadZone").style.display = "block";
  document.getElementById("fileSelectedVisual").style.display = "none";
  document.getElementById("loadingIndicator").style.display = "none";

  // Pindah ke tampilan Assessment saat reset UI selesai
  navigateTo("assessment");
}

// --- Dropdown Pertanyaan ---

function populateQuestionDropdown(questions, currentScores) {
  const select = document.getElementById("questionSelect");
  const detail = document.getElementById("questionDetail");
  select.innerHTML = '<option value="" disabled selected>-- Pilih ID Pertanyaan --</option>';

  const reviewedIds = currentScores.map((score) => score.id);

  questions.forEach((q) => {
    const isReviewed = reviewedIds.includes(q.id);
    const marker = isReviewed ? " [Reviewed]" : "";
    const option = document.createElement("option");
    option.value = q.id;
    option.textContent = `Q${q.id}: ${q.question.substring(0, 50)}...${marker}`;
    select.appendChild(option);
  });

  select.addEventListener("change", () => {
    const selectedId = parseInt(select.value);
    const q = getQuestionById(selectedId);
    detail.textContent = q ? q.question : "";
  });
}

// --- Penanganan File dan Upload ---

function handleFileSelect(event) {
  // Menggunakan event.target.files untuk input standar, atau files jika dari drag drop
  const files = event.target.files || (event.target.files === undefined ? [] : event.target.files);
  const uploadZone = document.getElementById("uploadZone");
  const fileSelectedVisual = document.getElementById("fileSelectedVisual");
  const questionSelect = document.getElementById("questionSelect");

  if (files.length > 0) {
    if (!questionSelect.value) {
      alert("Harap pilih ID Pertanyaan terlebih dahulu.");
      event.target.value = "";
      return;
    }

    selectedFile = files[0];
    document.getElementById("fileName").textContent = selectedFile.name;
    uploadZone.style.display = "none";
    fileSelectedVisual.style.display = "block";
  } else {
    // Hanya reset UI jika file input dikosongkan secara manual
    if (event.target.id === "videoInput") {
      resetAssessment();
    }
  }
}

// --- Drag and Drop Handlers ---
const uploadZone = document.getElementById("uploadZone");

if (uploadZone) {
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
      const input = document.getElementById("videoInput");
      input.files = files;
      handleFileSelect({ target: { files: files } });
    }
  });
}

// --- Fungsi Proses Video (BARU) ---

async function processNewVideo() {
  const questionId = document.getElementById("questionSelect").value;
  if (!selectedFile || !questionId) {
    alert("Please select a file and a Question ID.");
    return;
  }

  const formData = new FormData();
  formData.append("videoFile", selectedFile);
  formData.append("questionId", questionId);

  document.getElementById("fileSelectedVisual").style.display = "none";
  document.getElementById("loadingIndicator").style.display = "block";

  try {
    const response = await fetch("/api/process_video", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      let errorDetail = response.statusText;
      try {
        const errorData = await response.json();
        errorDetail = errorData.error || errorDetail;
      } catch (e) {}
      throw new Error(`Processing failed: ${errorDetail}`);
    }

    const data = await response.json();

    renderScoreHistory(data.assessment_data, questionData);
    displayLatestAlert(data.latest_score);
    populateQuestionDropdown(questionData, data.assessment_data);
    updateProgress(data.assessment_data.length);

    document.getElementById("loadingIndicator").style.display = "none";
    // Hanya reset UI upload, tetapi tidak reset session
    selectedFile = null;
    navigateTo("results");
  } catch (error) {
    console.error("Error:", error);
    alert(`Error during processing. Details: ${error.message}`);
    document.getElementById("loadingIndicator").style.display = "none";
    resetAssessment();
  }
}

// --- Rendering History Hasil ---

function updateProgress(count) {
  const total = 5;
  document.getElementById("progressCount").textContent = `${count}/${total}`;
  const compileBtn = document.getElementById("compileSummaryBtn");
  compileBtn.disabled = count < total;

  document.getElementById("finalSummarySection").style.display = "none";
}

function displayLatestAlert(latestScore) {
  const alertDiv = document.getElementById("latestAnalysisAlert");
  const statusClass = latestScore.cv_metrics.cheating_flag ? "flag-warning" : "flag-success";
  const statusText = latestScore.cv_metrics.cheating_flag ? "INTEGRITY ALERT!" : "SUCCESS!";

  alertDiv.innerHTML = `
        <div class="${statusClass} mb-4 p-4 rounded">
            <strong>${statusText}</strong> Q${latestScore.id} processed and saved.
            <br>STT Accuracy: ${latestScore.stt_accuracy}% | Non-Verbal Violations: ${latestScore.cv_metrics.violations}
        </div>
    `;
}

function renderScoreHistory(scores, questions) {
  const historyDiv = document.getElementById("individualScoreHistory");
  historyDiv.innerHTML = "";

  if (scores.length === 0) {
    historyDiv.innerHTML = '<p class="text-gray-600 text-center">No assessments analyzed yet. Start by uploading a video.</p>';
    return;
  }

  scores.sort((a, b) => a.id - b.id);

  scores.forEach((scoreItem) => {
    const questionObj = getQuestionById(scoreItem.id) || { question: "Unknown Question" };
    const score = scoreItem.score;
    const reason = scoreItem.reason;
    const cv = scoreItem.cv_metrics;
    const stt = scoreItem.stt_accuracy;

    historyDiv.innerHTML += `
            <div class="result-item p-4 border-l-8 border-indigo-500">
                <div class="flex justify-between items-start mb-3">
                    <h4 class="text-lg font-bold text-gray-900">Q${scoreItem.id}: ${questionObj.question.substring(0, 80)}...</h4>
                    <span class="score-badge score-badge-${score} text-xl">${score}/4</span>
                </div>
                
                <p class="text-gray-700 italic mb-2">${reason}</p>
                
                <div class="flex text-sm text-gray-500 justify-between mt-3 pt-2 border-t">
                    <span>STT Acc: ${stt}%</span>
                    <span>Non-Verbal Ratio: ${cv.eye_movement_ratio.toFixed(2)}</span>
                    <span class="${cv.cheating_flag ? "text-red-600 font-semibold" : ""}">Violations: ${cv.violations}</span>
                </div>
                <div class="mt-3">
                    <p class="text-sm font-semibold mb-1">Transcript Preview:</p>
                    <p class="text-xs italic text-gray-600 truncate">${scoreItem.transcript}</p>
                </div>
            </div>
        `;
  });
}

// --- Final Summary Compilation ---

async function compileFinalSummary() {
  const compileBtn = document.getElementById("compileSummaryBtn");
  compileBtn.disabled = true;

  try {
    const response = await fetch("/api/compile_summary", { method: "GET" });

    if (!response.ok) {
      const errorData = await response.json();
      alert(`Compilation failed: ${errorData.error}`);
      return;
    }

    const data = await response.json();
    const finalPayload = data.final_payload;

    // Render Final Summary Section
    document.getElementById("finalSummarySection").style.display = "block";
    document.getElementById("finalTotalInterviewScore").textContent = `${finalPayload.scoresOverview.interview}/20`;
    document.getElementById("finalDecisionSummary").textContent = finalPayload.decision;
    document.getElementById("finalOverallTotalScore").textContent = finalPayload.scoresOverview.total;
    document.getElementById("finalOverallNotes").textContent = finalPayload["Overall notes"];

    // Siapkan tombol download
    const downloadBtn = document.getElementById("downloadFinalJsonBtn");
    const jsonString = JSON.stringify(finalPayload, null, 2);
    downloadBtn.onclick = () => {
      const blob = new Blob([jsonString], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `final_assessment_payload_${finalPayload.reviewedAt.split(" ")[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    };
    downloadBtn.style.display = "block";

    alert("Final Summary Compiled! Scroll down to view the final payload and download the JSON.");
  } catch (error) {
    console.error("Compilation error:", error);
    alert("An error occurred during final summary compilation.");
  } finally {
    compileBtn.disabled = false;
  }
}
