// static/js/main.js

function debounce(fn, delay) {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn(...args), delay);
    };
  }
  
  async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    return res.json();
  }
  
  function renderEmptyList() {
    const list = document.getElementById("topics-list");
    list.innerHTML = `
      <div class="empty-state">
        No topics found. Try a different search or create a new topic.
      </div>
    `;
  }
  
  function renderTopics(topics) {
    const list = document.getElementById("topics-list");
    list.innerHTML = "";
  
    if (!topics.length) {
      renderEmptyList();
      return;
    }
  
    topics.forEach((t) => {
      const item = document.createElement("button");
      item.className = "topic-item";
      item.setAttribute("type", "button");
      item.dataset.topicId = t.id;
      item.innerHTML = `
        <div class="topic-title">${t.title}</div>
      `;
      item.addEventListener("click", () => {
        selectTopic(t.id, item);
      });
      list.appendChild(item);
    });
  }
  
  function setActiveTopicButton(activeBtn) {
    const buttons = document.querySelectorAll(".topic-item");
    buttons.forEach((btn) => btn.classList.remove("active"));
    if (activeBtn) activeBtn.classList.add("active");
  }
  
  async function selectTopic(topicId, buttonEl) {
    setActiveTopicButton(buttonEl);
  
    const detail = document.getElementById("topic-detail");
    detail.innerHTML = `
      <div class="loading-state">Loading topic…</div>
    `;
  
    try {
      const data = await fetchJSON(`/api/topics/${topicId}`);
  
      detail.innerHTML = `
        <article>
            <div class="topic-detail-header">
            <h2 class="topic-detail-title">${data.title}</h2>

            <div class="topic-detail-actions">
                <a href="/topics/${data.id}/edit" class="btn small">Edit</a>
                <button type="button" class="btn small danger" data-delete-id="${data.id}">
                Delete
                </button>
            </div>
            </div>

            <div class="topic-meta">
            <span>Created: ${new Date(data.created_at).toLocaleString()}</span>
            <span>Last updated: ${new Date(data.updated_at).toLocaleString()}</span>
            </div>

            <div class="topic-body">
            ${data.body}
            </div>

            ${
            data.images && data.images.length
                ? `
                <h3 style="margin-top: 24px; margin-bottom: 8px;">Images</h3>
                <div class="image-gallery">
                ${data.images
                    .map(
                    (img) => `
                        <div class="image-card">
                        <img
                            src="${img.url}"
                            class="image-thumb"
                            data-full="${img.url}"
                        >
                        <div class="image-title">${img.title || ""}</div>
                        </div>
                    `
                    )
                    .join("")}
                </div>
            `
                : ""
            }
        </article>
        `;
  
      const deleteBtn = detail.querySelector("[data-delete-id]");
      deleteBtn.addEventListener("click", () => handleDelete(data.id));
    } catch (err) {
      detail.innerHTML = `
        <div class="error-state">Failed to load topic.</div>
      `;
      console.error(err);
    }
  }
  
  async function handleDelete(topicId) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this topic? This cannot be undone."
    );
    if (!confirmed) return;
  
    try {
      const res = await fetch(`/topics/${topicId}/delete`, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });
  
      if (!res.ok) throw new Error(`Delete failed with status ${res.status}`);
  
      const detail = document.getElementById("topic-detail");
      detail.innerHTML = `
        <div class="empty-state">
          Topic deleted. Select another topic or create a new one.
        </div>
      `;
  
      await loadTopics(currentSearchQuery);
    } catch (err) {
      alert("Error deleting topic.");
      console.error(err);
    }
  }
  
  let currentSearchQuery = "";
  
  async function loadTopics(query = "") {
    currentSearchQuery = query;
    const list = document.getElementById("topics-list");
    list.innerHTML = `<div class="loading-state">Loading topics…</div>`;
  
    try {
      const data = await fetchJSON(`/api/topics?q=${encodeURIComponent(query)}`);
      renderTopics(data);
    } catch (err) {
      list.innerHTML = `<div class="error-state">Failed to load topics.</div>`;
      console.error(err);
    }
  }
  
  document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("search");
    const debouncedSearch = debounce((value) => loadTopics(value.trim()), 250);
  
    searchInput.addEventListener("input", (e) => {
      debouncedSearch(e.target.value);
    });
  
    // Initial load (show all topics)
    loadTopics("");
  });
  
  // Use event delegation for dynamically loaded images
  document.addEventListener("click", (e) => {
    // Check if clicked element is an image-thumb or inside an image-thumb
    const imageThumb = e.target.closest(".image-thumb");
    if (imageThumb) {
      const modal = document.getElementById("img-modal");
      const modalImg = document.getElementById("modal-img");
      if (modal && modalImg) {
        modalImg.src = imageThumb.dataset.full || imageThumb.src;
        modal.classList.remove("hidden");
      }
      e.preventDefault();
      return;
    }
  
    // Close modal when clicking on modal background or close button
    if (e.target.classList.contains("modal") || e.target.classList.contains("modal-close")) {
      const modal = document.getElementById("img-modal");
      if (modal) {
        modal.classList.add("hidden");
      }
    }
  });
  