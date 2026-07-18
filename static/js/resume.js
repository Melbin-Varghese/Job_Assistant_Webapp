(function () {
  const form = document.getElementById("ats-form");
  const fileInput = document.getElementById("resume_file");
  const dropzone = document.getElementById("dropzone");
  const dzText = document.getElementById("dz-text");
  const jdInput = document.getElementById("job_description");
  const submitBtn = document.getElementById("submit-btn");
  const submitLabel = document.getElementById("submit-label");
  const formError = document.getElementById("form-error");

  const resultsEmpty = document.getElementById("results-empty");
  const resultsContent = document.getElementById("results-content");

  const steps = document.querySelectorAll(".step");

  const GAUGE_CIRCUMFERENCE = 2 * Math.PI * 60; // r=60

  function setStep(n) {
    steps.forEach((el) => {
      const step = parseInt(el.dataset.step, 10);
      el.classList.toggle("active", step === n);
      el.classList.toggle("done", step < n);
    });
  }

  // ---- Dropzone interactions ----
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) {
      dzText.textContent = fileInput.files[0].name;
      setStep(2);
    }
  });

  ["dragover", "dragenter"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    })
  );

  ["dragleave", "drop"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    })
  );

  dropzone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length) {
      fileInput.files = files;
      dzText.textContent = files[0].name;
      setStep(2);
    }
  });

  jdInput.addEventListener("input", () => {
    if (jdInput.value.trim().length > 0 && fileInput.files.length) {
      setStep(3);
    }
  });

  // ---- Gauge helper ----
  function setGauge(circleEl, numberEl, percent) {
    const clamped = Math.max(0, Math.min(100, percent));
    const offset = GAUGE_CIRCUMFERENCE - (clamped / 100) * GAUGE_CIRCUMFERENCE;
    requestAnimationFrame(() => {
      circleEl.style.strokeDashoffset = offset;
    });
    numberEl.textContent = clamped.toFixed(0) + "%";
  }

  function renderTags(container, items) {
    container.innerHTML = "";
    if (!items || !items.length) {
      const span = document.createElement("span");
      span.className = "kw-note";
      span.textContent = "None";
      container.appendChild(span);
      return;
    }
    items.forEach((kw) => {
      const span = document.createElement("span");
      span.className = "tag";
      span.textContent = kw;
      container.appendChild(span);
    });
  }

  function showError(msg) {
    formError.textContent = msg;
    formError.hidden = false;
  }

  function clearError() {
    formError.hidden = true;
    formError.textContent = "";
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearError();

    if (!fileInput.files.length) {
      showError("Please choose a resume file.");
      return;
    }
    if (!jdInput.value.trim()) {
      showError("Please paste the job description.");
      return;
    }

    submitBtn.disabled = true;
    submitLabel.textContent = "Analyzing…";

    const fd = new FormData();
    fd.append("resume_file", fileInput.files[0]);
    fd.append("job_description", jdInput.value.trim());

    try {
      // Use relative URL that works with blueprint url_prefix='/resume'
      const res = await fetch("./process", { method: "POST", body: fd });
      const data = await res.json();

      if (!res.ok) {
        showError(data.error || "Something went wrong. Please try again.");
        return;
      }

      resultsEmpty.hidden = true;
      resultsContent.hidden = false;

      setGauge(
        document.getElementById("gauge-before"),
        document.getElementById("score-before-num"),
        data.before_score
      );
      setGauge(
        document.getElementById("gauge-after"),
        document.getElementById("score-after-num"),
        data.after_score
      );

      const matchedAll = [...data.matched, ...data.matched_bigrams];
      const missingAll = [...data.missing, ...data.missing_bigrams].filter(
        (kw) => !data.added_skills.includes(kw)
      );

      renderTags(document.getElementById("matched-tags"), matchedAll);
      renderTags(document.getElementById("added-tags"), data.added_skills);
      renderTags(document.getElementById("missing-tags"), missingAll);

      document.getElementById("matched-count").textContent = matchedAll.length;
      document.getElementById("added-count").textContent = data.added_skills.length;
      document.getElementById("missing-count").textContent = missingAll.length;

      const downloadLink = document.getElementById("download-link");
      // Use relative URL that works with blueprint url_prefix='/resume'
      downloadLink.href = "./download/" + encodeURIComponent(data.download_file);

      resultsContent.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      showError("Network error — please try again.");
    } finally {
      submitBtn.disabled = false;
      submitLabel.textContent = "Analyze & Tailor Resume";
    }
  });

  document.getElementById("reset-btn").addEventListener("click", () => {
    form.reset();
    dzText.textContent = "Drop your .pdf or .docx here, or click to browse";
    resultsContent.hidden = true;
    resultsEmpty.hidden = false;
    setStep(1);
    clearError();
  });
})();