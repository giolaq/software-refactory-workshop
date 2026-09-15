// Deterministic single-executor UI scenario; backend queueing has real CLI tests.
(async () => {
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const originalRequest = request, originalConfirm = window.confirm;
  const originalSnapshot = app.snapshot;
  const number = app.selectedTicket.number;
  const snapshot = structuredClone(originalSnapshot);
  const ticket = snapshot.factory.tickets.find(item => item.number === number);
  snapshot.operation = {status: 'running', action: 'run', title: 'Deliver tickets'};
  snapshot.config.max_parallel = 1;
  const busy = snapshot.factory.tickets.find(item => item.number !== number);
  Object.assign(busy, {status: 'In Progress', phase: 'implementation'});
  let submissions = 0;
  try {
    window.confirm = () => true;
    request = async (url, options) => {
      if (url === '/api/actions/approve-tests') {
        submissions++;
        const payload = JSON.parse(options.body);
        check(payload.qa_commit === ticket.qa_commit, 'Approval omitted the inspected revision');
        Object.assign(ticket, {status: 'Ready', phase: 'Queued', qa_approval_pending: true});
        return {companion: {action: 'approve-tests', title: 'Approve tests', status: 'succeeded'}};
      }
      if (url === '/api/snapshot') return snapshot;
      return originalRequest(url, options);
    };
    renderSnapshot(snapshot);
    await renderDrawer();
    document.querySelector('[data-ticket-action="approve-tests"]').click();
    await new Promise(resolve => setTimeout(resolve, 0));
    check(submissions === 1, 'Approval was not submitted once');
    check(document.querySelector('#ticket-drawer').hidden, 'Successful approval left the panel open');
    check(document.querySelector(`[data-ticket="${number}"]`).textContent.includes('Queued for implementation'),
      'Approved ticket has no visible queue status');
    check(document.querySelector('#toast-region').textContent.includes('when an executor is available'),
      'Success did not explain executor availability');
    openTicket(number);
    await renderDrawer();
    check(document.querySelector('#drawer-content').textContent.includes('Approval saved'), 'Queue status disappeared when reopened');
    check(!document.querySelector('[data-ticket-action="approve-tests"]'), 'Queued ticket asks for a duplicate approval');
    snapshot.operation = {status: 'succeeded', action: 'run'};
    check(approvalQueueMessage().includes('Choose Run factory'), 'Idle runner incorrectly promises automatic execution');
    snapshot.operation = {status: 'running', action: 'run-once'};
    check(approvalQueueMessage().includes('may finish before'), 'One-cycle mode incorrectly promises automatic execution');

    renderSnapshot(originalSnapshot);
    openTicket(number);
    await renderDrawer();
    request = async () => { throw new Error('The test revision changed.'); };
    await action('approve-tests', {issue: number, qa_commit: ticket.qa_commit});
    check(!document.querySelector('#ticket-drawer').hidden, 'Failed approval closed the panel');
    check(app.selectedTicket.status === 'QA Review', 'Failed approval was shown as queued');
    return 'PASS approval queues while executor busy, closes on success, and stays open on failure';
  } finally {
    request = originalRequest;
    window.confirm = originalConfirm;
    closeDrawer();
    renderSnapshot(originalSnapshot);
    document.querySelector(`[data-ticket="${number}"]`).focus();
    openTicket(number);
    await renderDrawer();
    document.querySelector('#toast-region').replaceChildren();
  }
})()
