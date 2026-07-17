// CareerMomentum Super Admin — app.js
// Table row interactions shared across dashboard / jobs / recruiters / users pages.
// Every action below calls the /api/super-admin/... endpoints (super_admin_api.py)
// so changes persist in the database, instead of just editing the DOM.

const CM_API_BASE = "/api/super-admin";

async function cmApiPost(path) {
  const res = await fetch(CM_API_BASE + path, { method: "POST" });
  let data = null;
  try {
    data = await res.json();
  } catch (e) {
    /* non-JSON error page */
  }
  if (!res.ok || !data || !data.ok) {
    const message = (data && data.error) || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

document.addEventListener("DOMContentLoaded", () => {
  const tableBody = document.body; // event-delegate from the body so this
                                    // still works after rows are re-rendered

  // ------------------------------------------------------------------
  // Job posting approve / reject
  // ------------------------------------------------------------------
  tableBody.addEventListener("click", async (e) => {
    const acceptBtn = e.target.closest(".action-pill.accept");
    const rejectBtn = e.target.closest(".action-pill.reject");
    const btn = acceptBtn || rejectBtn;
    if (!btn) return;

    const jobId = btn.dataset.jobId;
    if (!jobId) return;

    const row = btn.closest("tr");
    const group = btn.closest(".action-pill-group");
    const originalHtml = group.innerHTML;
    group.innerHTML = '<span class="table-panel-count">Saving…</span>';

    try {
      if (acceptBtn) {
        await cmApiPost(`/jobs/${jobId}/approve`);
        // This table only lists Pending jobs, so once approved it drops
        // out of the pending-approval list entirely (matches server truth).
        row.remove();
      } else {
        await cmApiPost(`/jobs/${jobId}/reject`);
        row.remove();
      }
    } catch (err) {
      group.innerHTML = originalHtml;
      alert(err.message);
    }
  });

  // ------------------------------------------------------------------
  // Recruiter (Employer) suspend / unsuspend / block / unblock
  // ------------------------------------------------------------------
  tableBody.addEventListener("click", async (e) => {
    const suspendBtn = e.target.closest(".action-pill.suspend");
    const unsuspendBtn = e.target.closest(".action-pill.unsuspend");
    const blockBtn = e.target.closest(".action-pill.block[data-employer-id]");
    const unblockBtn = e.target.closest(".action-pill.unblock[data-employer-id]");
    const btn = suspendBtn || unsuspendBtn || blockBtn || unblockBtn;
    if (!btn) return;

    const employerId = btn.dataset.employerId;
    if (!employerId) return;

    const action = suspendBtn ? "suspend"
      : unsuspendBtn ? "unsuspend"
      : blockBtn ? "block"
      : "unblock";

    const row = btn.closest("tr");
    const group = btn.closest(".action-pill-group");
    const originalHtml = group.innerHTML;
    btn.disabled = true;
    btn.style.opacity = "0.5";

    try {
      const data = await cmApiPost(`/employers/${employerId}/${action}`);
      cmUpdateEmployerRow(row, data.status);
    } catch (err) {
      group.innerHTML = originalHtml;
      alert(err.message);
    }
  });

  // ------------------------------------------------------------------
  // User (Seeker) block / unblock
  // ------------------------------------------------------------------
  tableBody.addEventListener("click", async (e) => {
    const blockBtn = e.target.closest(".action-pill.block[data-seeker-id]");
    const unblockBtn = e.target.closest(".action-pill.unblock[data-seeker-id]");
    const btn = blockBtn || unblockBtn;
    if (!btn) return;

    const seekerId = btn.dataset.seekerId;
    if (!seekerId) return;

    const action = blockBtn ? "block" : "unblock";

    const row = btn.closest("tr");
    const group = btn.closest(".action-pill-group");
    const originalHtml = group.innerHTML;
    btn.disabled = true;
    btn.style.opacity = "0.5";

    try {
      const data = await cmApiPost(`/seekers/${seekerId}/${action}`);
      cmUpdateSeekerRow(row, data.status);
    } catch (err) {
      group.innerHTML = originalHtml;
      alert(err.message);
    }
  });

  // Logout buttons (sidebar + profile page)
  document.querySelectorAll("[data-action='logout']").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      cmLogout();
    });
  });
});

// Re-renders an employer row's status pill + action buttons after a
// suspend/unsuspend/block/unblock call succeeds.
function cmUpdateEmployerRow(row, status) {
  const statusCell = row.querySelector(".statusCell") || row.children[3];
  const actionsCell = row.querySelector(".right .action-pill-group");
  const employerId = row.dataset.employerId;

  if (status === "Active") {
    statusCell.innerHTML = '<span class="status-dot-row active"><span class="status-dot"></span> Active</span>';
    actionsCell.innerHTML = `
      <button class="action-pill suspend" data-employer-id="${employerId}">Suspend</button>
      <button class="action-pill block" data-employer-id="${employerId}">Block</button>`;
  } else if (status === "Suspended") {
    statusCell.innerHTML = '<span class="status-dot-row suspended"><span class="status-dot"></span> Suspended</span>';
    actionsCell.innerHTML = `
      <button class="action-pill unsuspend" data-employer-id="${employerId}">Unsuspend</button>
      <button class="action-pill block" data-employer-id="${employerId}">Block</button>`;
  } else if (status === "Blocked") {
    statusCell.innerHTML = '<span class="status-dot-row suspended"><span class="status-dot"></span> Blocked</span>';
    actionsCell.innerHTML = `<button class="action-pill unblock" data-employer-id="${employerId}">Unblock</button>`;
  }
}

// Re-renders a seeker row's status pill + action button after a
// block/unblock call succeeds.
function cmUpdateSeekerRow(row, status) {
  const statusCell = row.children[4];
  const actionsCell = row.querySelector(".right .action-pill-group");
  const seekerId = row.dataset.seekerId;
  const editBtn = '<button class="table-icon-btn"><span class="material-symbols-outlined">edit</span></button>';

  if (status === "Active") {
    statusCell.innerHTML = '<span class="status-dot-row active"><span class="status-dot"></span> Active</span>';
    actionsCell.innerHTML = `${editBtn}<button class="action-pill block" data-seeker-id="${seekerId}">Block</button>`;
  } else {
    statusCell.innerHTML = '<span class="status-dot-row suspended"><span class="status-dot"></span> Blocked</span>';
    actionsCell.innerHTML = `${editBtn}<button class="action-pill unblock" data-seeker-id="${seekerId}">Unblock</button>`;
  }
}