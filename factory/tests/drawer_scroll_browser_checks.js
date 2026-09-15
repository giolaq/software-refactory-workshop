// Run in the real Control Center after opening a ticket's Tests tab.
(async () => {
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const savedProposal = app.testProposal;
  const originalRequest = request;
  try {
    app.testProposal = {
      key: `${app.snapshot.repo.path}:${app.selectedTicket.number}:${app.selectedTicket.qa_commit}`,
      value: {
        revision: app.selectedTicket.qa_commit,
        files: Array.from({length: 8}, (_, index) => ({
          path: `tests/test_reading_${index}.py`,
          content: Array.from({length: 100}, (_, line) => `# Line ${line}: ${'acceptance evidence '.repeat(15)}`).join('\n'),
        })),
      },
    };
    await renderDrawer();
    const drawer = document.querySelector('#ticket-drawer');
    const source = () => document.querySelector('#qa-test-source pre');
    source().scrollTop = 130;
    const feedback = document.querySelector('#qa-revision-feedback');
    feedback.value = 'Please retain this draft during refresh.';
    feedback.focus({preventScroll: true});
    feedback.setSelectionRange(7, 13);
    drawer.scrollTop = drawer.scrollHeight - drawer.clientHeight - 200;
    const top = drawer.scrollTop;
    check(top > 500, 'Fixture must overflow the drawer');
    check(source().scrollTop === 130, 'Fixture must overflow the test source');
    for (let refresh = 0; refresh < 3; refresh++) {
      await renderDrawer({preservePosition: true});
      check(Math.abs(drawer.scrollTop - top) < 2, `Refresh moved the drawer from ${top} to ${drawer.scrollTop}`);
      check(source().scrollTop === 130, `Refresh reset the test-source scroll position to ${source().scrollTop}`);
      check(document.querySelector('#qa-revision-feedback').value === feedback.value, 'Refresh erased revision feedback');
      check(document.activeElement.id === 'qa-revision-feedback' && document.activeElement.selectionStart === 7,
        'Refresh moved feedback focus or selection');
    }
    const proposal = app.testProposal.value;
    app.testProposal = null;
    let complete;
    request = () => new Promise(resolve => { complete = resolve; });
    const pending = renderDrawer({preservePosition: true});
    check(source() && drawer.scrollTop === top, 'Pending refresh replaced readable content with a placeholder');
    check(document.querySelector('[data-ticket-action="approve-tests"]').disabled,
      'Approval must wait until the displayed proposal revision is verified');
    drawer.scrollTop = top - 150;
    source().scrollTop = 200;
    complete(proposal);
    await pending;
    check(drawer.scrollTop === top - 150 && source().scrollTop === 200,
      'Delayed response undid scrolling performed while waiting');
    app.testProposal = null;
    const stale = renderDrawer({preservePosition: true});
    app.drawerTab = 'history';
    await renderDrawer();
    complete(proposal);
    await stale;
    check(!document.querySelector('#qa-test-source'), 'Late test response replaced another tab');
    return 'PASS Tests tab keeps reading position and feedback across refreshes';
  } finally {
    request = originalRequest;
    app.testProposal = savedProposal;
    app.drawerTab = 'tests';
    await renderDrawer();
  }
})()
