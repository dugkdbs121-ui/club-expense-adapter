const form = document.getElementById("analysis-form");
const formatSelect = document.getElementById("format");
const fileInput = document.getElementById("csv-file");
const analyzeButton = document.getElementById("analyze-button");
const formatHints = {
  club: "날짜는 2026-11-17, 금액은 1000처럼 적습니다.",
  event: "사용일은 2026/11/17, 지출액은 1000처럼 적습니다.",
  bank: '거래일은 2026.11.17, 출금액은 "1,000원"처럼 적습니다.',
};
const sampleFiles = {
  club: "club_normal.csv",
  event: "event_normal.csv",
  bank: "bank_normal.csv",
};
let csvText = "";
let hasInput = false;
let busy = false;
let inputRevision = 0;

function setStatus(message, kind = "") {
  const status = document.getElementById("result-status");
  status.textContent = message;
  status.className = "status-badge " + kind;
  document.getElementById("live-message").textContent = message;
}

function clearResult() {
  document.getElementById("total-amount").textContent = "—";
  document.getElementById("expense-count").textContent = "—";
  document.getElementById("category-count").textContent = "분류별로 묶어 보여드려요";
  document.getElementById("category-rows").replaceChildren();
  document.getElementById("table-wrapper").hidden = true;
  document.getElementById("download-area").hidden = true;
  document.getElementById("empty-state").hidden = false;
  document.getElementById("error-box").hidden = true;
}

function showError(message) {
  clearResult();
  document.getElementById("error-text").textContent = message;
  document.getElementById("error-box").hidden = false;
  setStatus("확인이 필요해요", "error");
}

function setBusy(value) {
  busy = value;
  analyzeButton.disabled = busy || !hasInput;
  fileInput.disabled = busy;
  formatSelect.disabled = busy;
  document.querySelectorAll("[data-sample]").forEach(function (button) {
    button.disabled = busy;
  });
  analyzeButton.textContent = busy ? "검사하고 정리하는 중…" : "검사하고 정리하기 →";
}

function loadText(text, filename) {
  csvText = text;
  hasInput = true;
  document.getElementById("file-name").textContent = filename;
  document.getElementById("file-description").textContent = "불러오기 완료 · 아래 버튼으로 검사하세요";
  document.getElementById("csv-preview").textContent = text;
  document.getElementById("preview-details").hidden = false;
  clearResult();
  setStatus("검사 준비 완료");
  analyzeButton.disabled = false;
}

function showResult(result) {
  clearResult();
  const number = new Intl.NumberFormat("ko-KR");
  document.getElementById("total-amount").textContent = number.format(result.total);
  document.getElementById("expense-count").textContent = number.format(result.count);
  document.getElementById("category-count").textContent = result.categories.length + "개 분류로 정리했어요";
  const body = document.getElementById("category-rows");
  result.categories.forEach(function (category) {
    const row = document.createElement("tr");
    const values = [category.category, number.format(category.count), number.format(category.total)];
    values.forEach(function (value) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.appendChild(cell);
    });
    body.appendChild(row);
  });
  document.getElementById("table-count").textContent = number.format(result.count);
  document.getElementById("table-total").textContent = number.format(result.total);
  document.getElementById("empty-state").hidden = true;
  document.getElementById("table-wrapper").hidden = false;
  document.getElementById("download-area").hidden = false;
  setStatus("검사·저장 완료", "success");
}

formatSelect.addEventListener("change", function () {
  document.getElementById("format-hint").textContent = formatHints[formatSelect.value];
  clearResult();
  setStatus(hasInput ? "양식 변경 · 다시 검사해 주세요" : "파일을 기다리는 중");
});

fileInput.addEventListener("change", async function () {
  const file = fileInput.files[0];
  if (!file) return;
  inputRevision += 1;
  const revision = inputRevision;
  hasInput = false;
  analyzeButton.disabled = true;
  if (file.size > 1024 * 1024) {
    showError("파일 크기는 1MB 이하여야 합니다.");
    return;
  }
  if (!file.name.toLowerCase().endsWith(".csv")) {
    showError("확장자가 .csv인 파일을 선택해 주세요.");
    return;
  }
  try {
    const buffer = await file.arrayBuffer();
    const text = new TextDecoder("utf-8", { fatal: true }).decode(buffer);
    if (revision === inputRevision) loadText(text, file.name);
  } catch (error) {
    if (revision === inputRevision) showError("UTF-8 CSV 파일을 읽을 수 없습니다. 파일 인코딩을 확인해 주세요.");
  }
});

document.querySelectorAll("[data-sample]").forEach(function (button) {
  button.addEventListener("click", async function () {
    const format = button.dataset.sample;
    inputRevision += 1;
    const revision = inputRevision;
    setBusy(true);
    try {
      const response = await fetch("/samples/" + sampleFiles[format]);
      if (!response.ok) throw new Error("예제 파일을 읽지 못했습니다.");
      const text = await response.text();
      if (revision !== inputRevision) return;
      formatSelect.value = format;
      document.getElementById("format-hint").textContent = formatHints[format];
      fileInput.value = "";
      loadText(text, sampleFiles[format]);
    } catch (error) {
      showError(error.message || "예제 파일을 읽지 못했습니다.");
    } finally {
      setBusy(false);
    }
  });
});

form.addEventListener("submit", async function (event) {
  event.preventDefault();
  if (!hasInput || busy) return;
  clearResult();
  setBusy(true);
  setStatus("입력 검사 중");
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ csv_text: csvText, format: formatSelect.value }),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || "처리하지 못했습니다.");
    showResult(data.result);
  } catch (error) {
    showError(error.message || "서버 연결을 확인해 주세요.");
  } finally {
    setBusy(false);
  }
});
