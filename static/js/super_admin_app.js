// CareerMomentum Super Admin — app.js
// Table row interactions shared across dashboard / jobs / recruiters / users pages.

document.addEventListener("DOMContentLoaded", () => {
  // Job posting approve / reject
  document.querySelectorAll(".action-pill.accept").forEach((btn) => {
    btn.addEventListener("click", () => {
      const row = btn.closest("tr");
      const statusCell = row.querySelector(".pill");
      if (statusCell) {
        statusCell.textContent = "Approved";
        statusCell.className = "pill completed";
      }
      btn.closest(".action-pill-group").innerHTML = '<span class="table-panel-count">Approved ✓</span>';
    });
  });

  document.querySelectorAll(".action-pill.reject").forEach((btn) => {
    btn.addEventListener("click", () => {
      const row = btn.closest("tr");
      const statusCell = row.querySelector(".pill");
      if (statusCell) {
        statusCell.textContent = "Rejected";
        statusCell.className = "pill resolved";
      }
      btn.closest(".action-pill-group").innerHTML = '<span class="table-panel-count">Rejected</span>';
    });
  });

  // Recruiter suspend
  document.querySelectorAll(".action-pill.suspend").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.disabled) return;
      const row = btn.closest("tr");
      const statusEl = row.querySelector(".status-dot-row");
      if (statusEl) {
        statusEl.className = "status-dot-row suspended";
        statusEl.innerHTML = '<span class="status-dot"></span> Suspended';
      }
      btn.disabled = true;
      btn.style.opacity = "0.5";
      btn.style.cursor = "not-allowed";
    });
  });

  // Block (recruiters + users)
  document.querySelectorAll(".action-pill.block").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (btn.disabled) return;
      const row = btn.closest("tr");
      const statusEl = row.querySelector(".status-dot-row");
      if (statusEl) {
        statusEl.className = "status-dot-row suspended";
        statusEl.innerHTML = '<span class="status-dot"></span> Blocked';
      }
      btn.textContent = "Blocked";
      btn.disabled = true;
      btn.style.opacity = "0.5";
      btn.style.cursor = "not-allowed";
    });
  });

  // Logout buttons (sidebar + profile page)
  document.querySelectorAll("[data-action='logout']").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      cmLogout();
    });
  });
});
