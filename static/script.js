let currentThreadId = localStorage.getItem("travel_thread_id") || null;
let latestAnswerMarkdown = "";
let progressInterval = null;

function setPrompt(text) {
    const input = document.getElementById("userInput");
    input.value = text;
    input.focus();
    input.scrollIntoView({ behavior: "smooth", block: "center" });
}

function setLoading(isLoading) {
    const sendBtn = document.getElementById("sendBtn");
    const btnText = document.getElementById("btnText");
    const btnLoader = document.getElementById("btnLoader");
    const agentTracker = document.getElementById("agentTracker");
    const trackerStatus = document.getElementById("trackerStatus");

    sendBtn.disabled = isLoading;

    if (isLoading) {
        btnText.classList.add("hidden");
        btnLoader.classList.remove("hidden");
        agentTracker.classList.remove("hidden");

        const progressMessages = [
            "Initializing LangGraph multi-agent pipeline...",
            "Scouting live flight routes & departure schedules...",
            "Discovering top-rated hotels and premier stays...",
            "Itinerary Architect synthesizing personalized daily schedule...",
            "Computing estimated budget breakdown & travel recommendations...",
            "Polishing and formatting final master travel plan..."
        ];

        let msgIndex = 0;
        trackerStatus.textContent = progressMessages[0];

        progressInterval = setInterval(() => {
            msgIndex = (msgIndex + 1) % progressMessages.length;
            trackerStatus.textContent = progressMessages[msgIndex];

            // Animate step badges
            const stepFlight = document.getElementById("stepFlight");
            const stepHotel = document.getElementById("stepHotel");
            const stepPlan = document.getElementById("stepPlan");

            if (msgIndex >= 1 && stepFlight) stepFlight.classList.add("active");
            if (msgIndex >= 2 && stepHotel) stepHotel.classList.add("active");
            if (msgIndex >= 3 && stepPlan) stepPlan.classList.add("active");
        }, 2200);

    } else {
        btnText.classList.remove("hidden");
        btnLoader.classList.add("hidden");
        agentTracker.classList.add("hidden");

        if (progressInterval) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
    }
}

function showError(message) {
    const errorBox = document.getElementById("errorBox");
    const errorText = document.getElementById("errorText");

    if (errorText) {
        errorText.textContent = message;
    } else {
        errorBox.textContent = message;
    }

    errorBox.classList.remove("hidden");
    errorBox.scrollIntoView({ behavior: "smooth", block: "center" });
}

function hideError() {
    const errorBox = document.getElementById("errorBox");
    errorBox.classList.add("hidden");
    const errorText = document.getElementById("errorText");
    if (errorText) errorText.textContent = "";
}

function showResult(answer, threadId) {
    latestAnswerMarkdown = answer;

    const resultSection = document.getElementById("resultSection");
    const resultBox = document.getElementById("resultBox");
    const threadInfo = document.getElementById("threadInfo");

    if (typeof marked !== "undefined") {
        resultBox.innerHTML = marked.parse(answer);
    } else {
        resultBox.innerText = answer;
    }

    threadInfo.textContent = `Conversation Thread: ${threadId}`;
    resultSection.classList.remove("hidden");

    resultSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

async function sendMessage() {
    hideError();

    const input = document.getElementById("userInput");
    const message = input.value.trim();

    if (!message) {
        showError("Please enter your travel details or select a destination idea above.");
        input.focus();
        return;
    }

    setLoading(true);

    try {
        const response = await fetch("/api/travel", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message,
                thread_id: currentThreadId
            })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Failed to generate travel plan. Please check server logs.");
        }

        currentThreadId = data.thread_id;
        localStorage.setItem("travel_thread_id", currentThreadId);

        showResult(data.answer, data.thread_id);

    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
}

function copyResult() {
    const resultBox = document.getElementById("resultBox");
    const text = resultBox.innerText;

    if (!text) {
        return;
    }

    navigator.clipboard.writeText(text)
        .then(() => {
            const copyBtn = document.querySelector(".copy-btn");
            const btnLabel = copyBtn.querySelector(".btn-label");
            const oldText = btnLabel ? btnLabel.textContent : copyBtn.textContent;

            if (btnLabel) {
                btnLabel.textContent = "Copied to Clipboard!";
            } else {
                copyBtn.textContent = "Copied to Clipboard!";
            }

            setTimeout(() => {
                if (btnLabel) {
                    btnLabel.textContent = oldText;
                } else {
                    copyBtn.textContent = oldText;
                }
            }, 1800);
        })
        .catch(() => {
            showError("Could not copy itinerary to clipboard.");
        });
}

function downloadPDF() {
    const pdfContent = document.getElementById("pdfContent");

    if (!latestAnswerMarkdown || !pdfContent) {
        showError("No travel plan available to download.");
        return;
    }

    const downloadBtn = document.querySelector(".download-btn");
    const btnLabel = downloadBtn.querySelector(".btn-label");
    const oldText = btnLabel ? btnLabel.textContent : downloadBtn.textContent;

    if (btnLabel) {
        btnLabel.textContent = "Generating PDF...";
    } else {
        downloadBtn.textContent = "Generating PDF...";
    }
    downloadBtn.disabled = true;

    const options = {
        margin: [0.5, 0.5, 0.5, 0.5],
        filename: "TripMate-AI-Travel-Plan.pdf",
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, backgroundColor: "#ffffff" },
        jsPDF: { unit: "in", format: "a4", orientation: "portrait" },
        pagebreak: { mode: ["avoid-all", "css", "legacy"] }
    };

    html2pdf()
        .set(options)
        .from(pdfContent)
        .save()
        .then(() => {
            if (btnLabel) {
                btnLabel.textContent = oldText;
            } else {
                downloadBtn.textContent = oldText;
            }
            downloadBtn.disabled = false;
        })
        .catch(() => {
            if (btnLabel) {
                btnLabel.textContent = oldText;
            } else {
                downloadBtn.textContent = oldText;
            }
            downloadBtn.disabled = false;
            showError("Could not generate PDF download.");
        });
}

function startNewPlan() {
    currentThreadId = null;
    localStorage.removeItem("travel_thread_id");
    const input = document.getElementById("userInput");
    input.value = "";
    document.getElementById("resultSection").classList.add("hidden");
    hideError();
    input.focus();
    input.scrollIntoView({ behavior: "smooth", block: "center" });
}

document.addEventListener("keydown", function (event) {
    if (event.ctrlKey && event.key === "Enter") {
        sendMessage();
    }
});
