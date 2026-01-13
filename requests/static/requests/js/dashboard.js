function openRequestDetail(dbId, requestCode) {
  const modal = document.getElementById("requestModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalBody = document.getElementById("modalBody");

  modal.classList.add("open");
  modalTitle.textContent = `Request Details - ${requestCode}`;
  modalBody.innerHTML = `<div class="loading">Loading...</div>`;

  fetch(`/request/${dbId}/`)
    .then(r => r.text())
    .then(html => {
      modalBody.innerHTML = html;
      wireButtons(dbId);
    })
    .catch(() => {
      modalBody.innerHTML = `<div class="loading">Error loading request details.</div>`;
    });
}

function closeModal() {
  document.getElementById("requestModal").classList.remove("open");
}

window.addEventListener("click", (e) => {
  const modal = document.getElementById("requestModal");
  if (e.target === modal) closeModal();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let c of cookies) {
      c = c.trim();
      if (c.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(c.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function wireButtons(dbId) {
  const approve = document.querySelector(".btn-approve");
  const reject = document.querySelector(".btn-reject");
  const info = document.querySelector(".btn-info");

  if (approve) approve.onclick = () => submitDecision(dbId, "approved");
  if (reject) reject.onclick = () => submitDecision(dbId, "rejected");
  if (info) info.onclick = () => submitDecision(dbId, "needs_info");
}

function submitDecision(dbId, status) {
  const feedback = document.getElementById("lecturer_feedback")?.value || "";
  const csrftoken = getCookie("csrftoken");

  fetch(`/api/update-status/${dbId}/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-CSRFToken": csrftoken
    },
    body: `status=${encodeURIComponent(status)}&feedback=${encodeURIComponent(feedback)}`
  })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        closeModal();
        location.reload();
      } else {
        alert("Error updating request.");
      }
    })
    .catch(() => alert("Error updating request."));
}
