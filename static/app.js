const leaveForm = document.getElementById('leaveForm');
const requestsEl = document.getElementById('requests');

async function fetchRequests() {
  const response = await fetch('/api/requests');
  const payload = await response.json();
  renderRequests(payload.data || []);
}

function workflowHint(request) {
  if (request.status === 'approved' || request.status === 'rejected') {
    return `Final status: ${request.status}`;
  }
  return `Current stage: ${request.status.replace('pending_', '')}`;
}

function renderRequests(requests) {
  if (!requests.length) {
    requestsEl.innerHTML = '<p>No requests yet.</p>';
    return;
  }

  requestsEl.innerHTML = requests
    .map((request) => {
      const decisions = (request.decisions || [])
        .map((d) => `<li>${d.role}: ${d.action}${d.comment ? ` (${d.comment})` : ''}</li>`)
        .join('');

      return `
      <article class="request">
        <h3>#${request.id} - ${request.student_name}</h3>
        <p>${request.reason} (${request.from_date} → ${request.to_date})</p>
        <p class="status">${request.status}</p>
        <small>${workflowHint(request)}</small>
        <ul>${decisions || '<li>No decisions yet</li>'}</ul>

        <div class="actions">
          <select class="role">
            <option value="advisor">Advisor</option>
            <option value="hod">HOD</option>
            <option value="principal">Principal</option>
          </select>
          <select class="action">
            <option value="approve">Approve</option>
            <option value="reject">Reject</option>
          </select>
          <input class="comment" placeholder="Comment (optional)" />
          <button data-id="${request.id}">Apply</button>
        </div>
      </article>`;
    })
    .join('');

  document.querySelectorAll('.actions button').forEach((button) => {
    button.addEventListener('click', async (event) => {
      const id = event.target.dataset.id;
      const container = event.target.closest('.actions');
      const role = container.querySelector('.role').value;
      const action = container.querySelector('.action').value;
      const comment = container.querySelector('.comment').value;

      const response = await fetch(`/api/requests/${id}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role, action, comment }),
      });

      if (!response.ok) {
        const error = await response.json();
        alert(error.error || 'Action failed');
        return;
      }
      fetchRequests();
    });
  });
}

leaveForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(leaveForm);
  const payload = Object.fromEntries(formData.entries());

  const response = await fetch('/api/requests', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response.json();
    alert(error.error || 'Submission failed');
    return;
  }

  leaveForm.reset();
  fetchRequests();
});

fetchRequests();
