// Calculator form handler — posts inputs to /api/calc/<id> and renders results.
(function () {
  const form = document.getElementById('calcForm');
  if (!form) return;

  const calcId      = form.dataset.calcId;
  const placeholder = document.getElementById('resultPlaceholder');
  const tbl         = document.getElementById('resultTable');
  const tbody       = tbl.querySelector('tbody');
  const notesBox    = document.getElementById('resultNotes');
  const errBox      = document.getElementById('resultError');
  const diagBox     = document.getElementById('resultDiagram');
  const dsBox       = document.getElementById('resultDatasheet');
  const chartsBox   = document.getElementById('resultCharts');

  function clearResults() {
    tbody.innerHTML = '';
    notesBox.innerHTML = '';
    errBox.hidden = true;
    errBox.textContent = '';
    tbl.hidden = true;
    placeholder.hidden = false;
    if (diagBox) { diagBox.innerHTML = ''; diagBox.hidden = true; }
    if (dsBox)   { dsBox.innerHTML   = ''; dsBox.hidden   = true; }
    if (chartsBox) { chartsBox.innerHTML = ''; chartsBox.hidden = true; }
  }

  function showError(msg) {
    clearResults();
    placeholder.hidden = true;
    errBox.hidden = false;
    errBox.textContent = msg;
  }

  function showResults(payload) {
    clearResults();
    placeholder.hidden = true;

    if (payload.diagram && diagBox) {
      diagBox.innerHTML = payload.diagram;
      diagBox.hidden = false;
    }

    if (payload.results && payload.results.length) {
      tbl.hidden = false;
      (payload.results || []).forEach(r => {
        const tr = document.createElement('tr');
        [r.label, r.value, r.unit || ''].forEach(v => {
          const td = document.createElement('td');
          td.textContent = v;
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
    }

    if (payload.datasheet && payload.datasheet.length && dsBox) {
      dsBox.hidden = false;
      payload.datasheet.forEach(section => {
        const h = document.createElement('h4');
        h.textContent = section.title || 'Datasheet';
        dsBox.appendChild(h);
        const t = document.createElement('table');
        t.className = 'data';
        const tb = document.createElement('tbody');
        (section.rows || []).forEach(row => {
          const tr = document.createElement('tr');
          row.forEach(cell => {
            const td = document.createElement('td');
            td.textContent = cell == null ? '' : cell;
            tr.appendChild(td);
          });
          tb.appendChild(tr);
        });
        t.appendChild(tb);
        dsBox.appendChild(t);
      });
    }

    if (payload.charts && payload.charts.length && chartsBox) {
      chartsBox.hidden = false;
      payload.charts.forEach(ch => {
        if (ch.title) {
          const h = document.createElement('h4');
          h.textContent = ch.title;
          chartsBox.appendChild(h);
        }
        const wrap = document.createElement('div');
        wrap.className = 'chart';
        wrap.innerHTML = ch.svg || '';
        chartsBox.appendChild(wrap);
      });
    }

    if (payload.notes && payload.notes.length) {
      const ul = document.createElement('ul');
      payload.notes.forEach(n => {
        const li = document.createElement('li');
        li.textContent = n;
        ul.appendChild(li);
      });
      notesBox.appendChild(ul);
    }
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {};
    new FormData(form).forEach((v, k) => { data[k] = v; });

    try {
      const r = await fetch('/api/calc/' + encodeURIComponent(calcId), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const payload = await r.json();
      if (!r.ok) {
        showError(payload.error || ('Request failed: ' + r.status));
        return;
      }
      showResults(payload);
    } catch (err) {
      showError('Network error: ' + err.message);
    }
  });

  // PDF download button
  const pdfBtn = document.getElementById('downloadPdf');
  if (pdfBtn) {
    pdfBtn.addEventListener('click', async () => {
      const data = {};
      new FormData(form).forEach((v, k) => { data[k] = v; });
      try {
        pdfBtn.disabled = true;
        pdfBtn.textContent = 'Generating PDF…';
        const r = await fetch('/api/report/' + encodeURIComponent(calcId), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
        if (!r.ok) {
          let msg = 'Request failed: ' + r.status;
          try { msg = (await r.json()).error || msg; } catch (_) {}
          showError(msg);
          return;
        }
        const blob = await r.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href = url;
        a.download = 'chemeng_' + calcId + '_report.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      } catch (err) {
        showError('Network error: ' + err.message);
      } finally {
        pdfBtn.disabled = false;
        pdfBtn.textContent = 'Download PDF Report';
      }
    });
  }
})();
