document.addEventListener("DOMContentLoaded", () => {

  const input = document.getElementById("main-input");
  const analyzeBtn = document.getElementById("analyze-btn");
  const toggleJsonBtn = document.getElementById("toggle-json");

  // JSON modal elements
  const modal = document.getElementById("modal");
  const modalBackdrop = document.getElementById("modal-backdrop");
  const modalJson = document.getElementById("modal-json");
  const modalClose = document.getElementById("modal-close");

  // Only the fields that exist in your cards
  const fields = {
    title: document.getElementById("result-title"),
    pid: document.getElementById("result-pid"),
    pub: document.getElementById("result-publication_date"),
    mod: document.getElementById("result-last_modification_date"),
    author: document.getElementById("result-author"),
    authors: document.getElementById("result-authors"),
    desc: document.getElementById("result-description"),
    keywords: document.getElementById("result-keywords")
  };

  function clearFields() {
    Object.values(fields).forEach(el => {
      el.textContent = "Not available";
    });
  }

  function setField(el, value) {
    if (!value || String(value).trim() === "") {
      el.textContent = "Not available";
    } else {
      el.textContent = value;
    }
  }

  function openModal(json) {
    modalJson.textContent = json;
    modal.style.display = "block";
    modalBackdrop.style.display = "block";
  }

  function closeModal() {
    modal.style.display = "none";
    modalBackdrop.style.display = "none";
  }

  modalClose.addEventListener("click", closeModal);
  modalBackdrop.addEventListener("click", closeModal);

  toggleJsonBtn.addEventListener("click", () => {
    if (modal.style.display === "block") {
      closeModal();
      toggleJsonBtn.textContent = "Show raw JSON";
    } else {
      openModal(modalJson.textContent);
      toggleJsonBtn.textContent = "Hide raw JSON";
    }
  });

  analyzeBtn.addEventListener("click", async () => {
    const url = input.value.trim();
    if (!url) return;

    clearFields();

    const res = await fetch("http://localhost:10124/analyze/url", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ url })
    });

    const text = await res.text();

    if (!res.ok) {
      alert("Server error: " + text);
      return;
    }

    const json = JSON.parse(text);
    const meta = json.raw_meta_tags || {};

    // Update JSON modal
    modalJson.textContent = JSON.stringify(json, null, 2);

    // Fill card fields
    setField(fields.title, json.title);
    setField(fields.pid, meta.doi);
    setField(fields.pub, meta.publication_date);
    setField(fields.mod, meta.last_modification_date);
    setField(fields.author, meta.author);
    setField(fields.authors, meta.authors);
    setField(fields.desc, meta.description);
    setField(fields.keywords, meta.keywords);
  });

});
