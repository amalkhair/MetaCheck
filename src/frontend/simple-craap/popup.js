(function () {
  'use strict';

  const btn = document.getElementById('showUrl');
  const result = document.getElementById('result');
  let urlText = document.getElementById('urlText') || document.createElement('a');
  const urlEl = document.getElementById('result-url');
  const statusText = document.getElementById('statusText') || document.createElement('span');
  const headersContainer = document.getElementById('headersContainer') || document.createElement('div');
  const headersPre = document.getElementById('headersPre') || document.createElement('pre');
  const responsePre = document.getElementById('response') || document.createElement('pre');

  // result elements (mirror main-page.html)
  const titleEl = document.getElementById('result-title');
  const pubEl = document.getElementById('result-publication_date');
  const doiEl = document.getElementById('result-pid');
  const lastModEl = document.getElementById('result-last_modification_date');
  const authorEl = document.getElementById('result-author');
  const authorsEl = document.getElementById('result-authors');
  const descEl = document.getElementById('result-description');
  const keywordsEl = document.getElementById('result-keywords');
  const publisherEl = document.getElementById('result-publisher');
  const extractEl = document.getElementById('result-extract');
  const jsonEl = document.getElementById('response');
  const errorEl = document.getElementById('result-error');
  const toggleBtn = document.getElementById('toggle-json');
  const footerEl = document.getElementById('result-footer');
  const idEl = document.getElementById('result-analysis_id');
  const genEl = document.getElementById('result-processed_at');
  let copyIdBtn = null;
  let copyUrlBtn = null;
  let copyDoiBtn = null;
  let idTextSpan = document.getElementById('result-analysis_text');

  function showResult() { result.style.display = 'block'; }

  function clearResults() {
    [titleEl, pubEl, lastModEl, authorEl, authorsEl, descEl, keywordsEl, publisherEl, extractEl, jsonEl, idEl, genEl, errorEl, urlEl, doiEl].forEach(el => {
      if (!el) return;
      el.hidden = true;
      if (el.textContent !== undefined) el.textContent = '';
    });
    if (footerEl) footerEl.hidden = true;
    // remove any dynamic copy buttons
    removeCopyButtons();
    // reset headers
    if (headersPre) headersPre.textContent = '';
    if (headersContainer) headersContainer.style.display = 'none';
  }

  // Remove any dynamically created copy buttons
  function removeCopyButtons() {
    try { if (copyIdBtn) { copyIdBtn.remove(); } } catch(e){}
    try { if (copyUrlBtn) { copyUrlBtn.remove(); } } catch(e){}
    try { if (copyDoiBtn) { copyDoiBtn.remove(); } } catch(e){}
    copyIdBtn = null;
    copyUrlBtn = null; copyDoiBtn = null;
    // also attempt to hide any lingering .copy-btn elements
    try { document.querySelectorAll('.copy-btn').forEach(b => { if (b) { b.hidden = true; b.style.display = 'none'; try { b.dataset.raw = ''; } catch{} } }); } catch(e){}
  }

  function fmtField(v) {
    if (v === null || v === undefined) return 'not available';
    if (Array.isArray(v)) return v.length === 0 ? 'not available' : v.join(', ');
    if (typeof v === 'string') return v.trim() === '' ? 'not available' : v;
    try { return String(v); } catch { return 'not available'; }
  }

  function formatDateLocalized(v) {
    if (!v) return null;
    try { const d = new Date(v); if (isNaN(d.getTime())) return null; return d.toLocaleString(); } catch { return null; }
  }

  function showParsed(title, meta, bodyText, rawJson, info) {
    titleEl.textContent = 'Title: ' + fmtField(title);
    pubEl.textContent = 'Publication date: ' + fmtField(meta.publication_date);
    lastModEl.textContent = 'Last modification date: ' + fmtField(meta.last_modification_date);
    authorEl.textContent = 'Author: ' + fmtField(meta.author);
    authorsEl.textContent = 'Authors: ' + fmtField(meta.authors);
    descEl.textContent = 'Description: ' + fmtField(meta.description);
    keywordsEl.textContent = 'Keywords: ' + fmtField(meta.keywords);
    publisherEl.textContent = 'Publisher: ' + fmtField(meta.publisher);

    jsonEl.textContent = rawJson ?? '';
    if (bodyText) extractEl.textContent = bodyText; else extractEl.textContent = '';

    // populate analysis id and ensure label span exists (do not overwrite container textContent)
    const rawId = info?.analysis_id ?? null;
    if (idEl) {
      // ensure label span
      let span = idEl.querySelector('#result-analysis_text');
      if (!span) {
        span = document.createElement('span');
        span.id = 'result-analysis_text';
        idEl.appendChild(span);
      }
      span.textContent = 'Analysis ID: ' + fmtField(rawId);
      idTextSpan = span;
      idEl.dataset.raw = rawId ?? '';
      // create copy button dynamically when we have a rawId
      if (rawId !== null && rawId !== undefined && String(rawId).trim() !== '') {
        if (!copyIdBtn) {
          copyIdBtn = document.createElement('button');
          copyIdBtn.className = 'copy-btn';
          copyIdBtn.id = 'copy-analysis-id';
          copyIdBtn.title = 'Copy Analysis ID';
          copyIdBtn.setAttribute('aria-label', 'Copy Analysis ID');
          // compact icon for clipboard; stored in dataset.orig for feedback restore
          copyIdBtn.dataset.orig = '';
          copyIdBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M16 4H8a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V6a2 2 0 00-2-2z" stroke="#444" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 8h-6a2 2 0 01-2-2V3" stroke="#444" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
          copyIdBtn.style.display = 'inline-block';
          idEl.appendChild(copyIdBtn);
          handleCopyButton(copyIdBtn);
        }
        copyIdBtn.dataset.raw = rawId ?? '';
        copyIdBtn.hidden = false;
        copyIdBtn.style.display = 'inline-block';
      } else {
        if (copyIdBtn) { try { copyIdBtn.remove(); } catch(e){} copyIdBtn = null; }
      }
    }

    // show processed at (formatted)
    const genFormatted = formatDateLocalized(info?.processed_at ?? null);
    if (genEl) genEl.textContent = 'Processed at: ' + fmtField(genFormatted ?? null);

    // URL handling: rebuild the URL container so label + value always appear (use server meta.url)
    const url = meta.url ?? null;
    if (urlEl) {
      // remove any previous copy button to prevent leftover-only-button state
      try { const previous = copyUrlBtn; if (previous) previous.remove(); } catch (e) {}
      copyUrlBtn = null;
      // clear container
      urlEl.innerHTML = '';

      // Always create label+anchor; show 'not available' when missing.
      const label = document.createElement('span');
      label.className = 'label';
      label.textContent = 'URL:';
      urlEl.appendChild(label);

      urlEl.appendChild(document.createTextNode(' '));

      const anchor = document.createElement('a');
      anchor.id = 'urlText';
      anchor.target = '_blank';
      anchor.setAttribute('aria-label', 'URL');
      anchor.style.color = '#0b66ff';
      anchor.style.textDecoration = 'none';
      anchor.style.wordBreak = 'break-all';
      anchor.style.display = 'inline-block';
      anchor.style.marginRight = '6px';

      const visibleUrl = (url && typeof url === 'string' && url.trim() !== '') ? url : null;
      if (visibleUrl) {
        anchor.href = visibleUrl;
        anchor.textContent = visibleUrl;
      } else {
        anchor.href = '#';
        anchor.textContent = 'not available';
      }

      urlEl.appendChild(anchor);
      urlText = anchor;

      // Only create the copy button when we have a real URL value
      if (visibleUrl) {
        // create copy button after the anchor
        copyUrlBtn = document.createElement('button');
        copyUrlBtn.className = 'copy-btn';
        copyUrlBtn.id = 'copy-url';
        copyUrlBtn.title = 'Copy URL';
        copyUrlBtn.setAttribute('aria-label', 'Copy URL');
        copyUrlBtn.dataset.orig = '';
        copyUrlBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M16 4H8a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V6a2 2 0 00-2-2z" stroke="#444" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 8h-6a2 2 0 01-2-2V3" stroke="#444" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
        // spacing and appending
        urlEl.appendChild(document.createTextNode(' '));
        urlEl.appendChild(copyUrlBtn);
        handleCopyButton(copyUrlBtn);
        copyUrlBtn.dataset.raw = visibleUrl;
        copyUrlBtn.hidden = false; copyUrlBtn.style.display = 'inline-block';
      } else {
        // ensure no copy button
        try { const prev = copyUrlBtn; if (prev) prev.remove(); } catch (e) {}
        copyUrlBtn = null;
      }
      urlEl.hidden = false;
    }

    // DOI handling: show under the URL always. If present, display uppercase DOI and copy button;
    // otherwise show 'not available' and ensure no copy button is shown.
    const doi = meta.doi ?? null;
    if (doiEl) {
      try { const previous = copyDoiBtn; if (previous) previous.remove(); } catch (e) {}
      copyDoiBtn = null;
      doiEl.innerHTML = '';
      const label = document.createElement('span');
      label.className = 'label';
      label.textContent = 'Persistent Identifier:';
      doiEl.appendChild(label);
      doiEl.appendChild(document.createTextNode(' '));

      const visibleDoi = (doi && typeof doi === 'string' && doi.trim() !== '') ? doi.trim() : null;
      if (visibleDoi) {
        const displayDoi = visibleDoi.toUpperCase();
        // normalize for link (strip leading doi: or doi.org URL)
        let normalized = visibleDoi.replace(/^\s*doi:\s*/i, '');
        normalized = normalized.replace(/^https?:\/\/(dx\.)?doi\.org\//i, '');
        normalized = normalized.trim();

        const doiLink = document.createElement('a');
        doiLink.href = 'https://doi.org/' + encodeURIComponent(normalized);
        doiLink.target = '_blank';
        doiLink.setAttribute('aria-label', 'Persistent Identifier');
        doiLink.style.color = '#0b66ff';
        doiLink.style.textDecoration = 'none';
        doiLink.style.wordBreak = 'break-all';
        doiLink.style.display = 'inline-block';
        doiLink.style.marginRight = '6px';
        doiLink.textContent = displayDoi;
        doiEl.appendChild(doiLink);

        // copy button copies uppercase persistent identifier — use compact SVG icon and tooltip
        copyDoiBtn = document.createElement('button');
        copyDoiBtn.className = 'copy-btn';
        copyDoiBtn.id = 'copy-pid';
        copyDoiBtn.title = 'Copy Persistent Identifier';
        copyDoiBtn.setAttribute('aria-label', 'Copy Persistent Identifier');
        copyDoiBtn.dataset.raw = displayDoi;
        // inline SVG clipboard icon (small)
        copyDoiBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M16 4H8a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V6a2 2 0 00-2-2z" stroke="#444" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/><path d="M21 8h-6a2 2 0 01-2-2V3" stroke="#444" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
        doiEl.appendChild(document.createTextNode(' '));
        doiEl.appendChild(copyDoiBtn);
        handleCopyButton(copyDoiBtn);
        copyDoiBtn.hidden = false; copyDoiBtn.style.display = 'inline-flex';
      } else {
        // show 'not available' when DOI missing
        const txt = document.createElement('span');
        txt.textContent = 'not available';
        doiEl.appendChild(txt);
        // ensure no copy button remains
        if (copyDoiBtn) { try { copyDoiBtn.remove(); } catch(e){} copyDoiBtn = null; }
      }
      doiEl.hidden = false;
    }

    [titleEl, pubEl, lastModEl, authorEl, authorsEl, descEl, keywordsEl, publisherEl].forEach(el => { if (el) el.hidden = false; });
    if (extractEl.textContent && extractEl.textContent.trim() !== '') extractEl.hidden = false;

    if (jsonEl.textContent && jsonEl.textContent.trim() !== '') { toggleBtn.hidden = false; jsonEl.hidden = true; } else { toggleBtn.hidden = true; }

    if (footerEl) footerEl.hidden = false;
    if (idEl) idEl.hidden = false;
    if (genEl) genEl.hidden = false;
    // show copy buttons when values are present
    if (copyIdBtn) copyIdBtn.hidden = !(copyIdBtn.dataset.raw && copyIdBtn.dataset.raw !== '');
    if (copyUrlBtn) copyUrlBtn.hidden = !(copyUrlBtn.dataset.raw && copyUrlBtn.dataset.raw !== '');
    if (copyDoiBtn) copyDoiBtn.hidden = !(copyDoiBtn.dataset.raw && copyDoiBtn.dataset.raw !== '');
  }

  function showError(msg) {
    clearResults();
    if (errorEl) { errorEl.textContent = msg; errorEl.hidden = false; }
  }

  btn.addEventListener('click', async () => {
    clearResults();
    showResult();

    // Update basic UI
    statusText.textContent = 'Preparing...';
    statusText.className = 'status muted';
    if (responsePre) responsePre.textContent = 'Waiting...';

    try {
      const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
      const url = tabs && tabs[0] && tabs[0].url ? tabs[0].url : null;
      if (!url) { showError('No URL available'); statusText.textContent = 'No URL'; statusText.className = 'status err'; return; }

      // send POST using query param so extension behavior remains
      const endpoint = 'http://localhost:10124/analyze/url?url=' + encodeURIComponent(url);
      statusText.textContent = 'Sending...';
      statusText.className = 'status muted';

      let resp;
      try { resp = await fetch(endpoint, { method: 'POST' }); } catch (networkErr) {
        statusText.textContent = 'Network error'; statusText.className = 'status err'; showError(networkErr && networkErr.message ? networkErr.message : String(networkErr)); return; }

      statusText.textContent = resp.status + ' ' + (resp.statusText || '');
      statusText.className = 'status ' + (resp.ok ? 'ok' : 'err');

      // headers
      const hdrs = []; resp.headers.forEach((v,k) => hdrs.push(k+': '+v));
      if (hdrs.length) { if (headersPre) headersPre.textContent = hdrs.join('\n'); if (headersContainer) headersContainer.style.display = 'block'; }
      else if (headersContainer) headersContainer.style.display = 'none';

      const text = await resp.text();

      if (!resp.ok) {
        // show backend-provided error for any non-2xx status
        try {
          const errJson = JSON.parse(text || '{}');
          let errMsg;
          if (errJson && errJson.detail) {
            errMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
          } else if (errJson && (errJson.message || errJson.error)) {
            errMsg = errJson.message || errJson.error;
          } else {
            errMsg = JSON.stringify(errJson);
          }
          showError(`Server error ${resp.status}: ${errMsg}`);
        } catch (pe) {
          showError(`Server error ${resp.status}: ${text || resp.statusText}`);
        }
        return;
      }

      try {
        const json = JSON.parse(text);
        let meta = json?.raw_meta_tags || {};
        try { if (typeof meta === 'string' && meta.trim() !== '') meta = JSON.parse(meta); } catch (e) { /* ignore */ }

        const title = json?.raw_meta_tags?.title || json?.title || null;

        let bodyText;
        if (json?.results && typeof json.results === 'object' && Object.keys(json.results).length > 0) { try { bodyText = JSON.stringify(json.results, null, 2); } catch { bodyText = String(json.results); } }
        else if (json?.content) bodyText = json.content;
        else bodyText = null;

        // Ensure meta contains ip_address if provided by backend (top-level or in raw_meta_tags)
        try {
          meta.ip_address = meta.ip_address ?? json?.ip_address ?? json?.ip ?? null;
        } catch (e) { meta.ip_address = meta.ip_address ?? null; }

        showParsed(title, {
           publication_date: meta.publication_date ?? null,
           last_modification_date: meta.last_modification_date ?? null,
           author: meta.author ?? null,
           authors: meta.authors ?? null,
           description: meta.description ?? null,
           keywords: meta.keywords ?? null,
           publisher: meta.publisher ?? null,
           url: meta.url ?? null,
           doi: meta.doi ?? null,
           ip_address: meta.ip_address ?? null
         }, bodyText, JSON.stringify(json, null, 2), {
           processed_at: json?.processed_at ?? null,
           analysis_id: json?.analysis_id ?? null,
         });
      } catch (pe) {
        // non-JSON response: show fallback messages without overwriting container children
        titleEl.textContent = 'Title: not available'; if (titleEl) titleEl.hidden = false;
        extractEl.textContent = 'No extracted text available.'; extractEl.hidden = false;
        jsonEl.textContent = `(non-JSON response, status ${resp.status})\n\n` + text; jsonEl.hidden = true;
        // ensure analysis label span exists and set fallback
        if (idEl) {
          let span = idEl.querySelector('#result-analysis_text');
          if (!span) {
            span = document.createElement('span');
            span.id = 'result-analysis_text';
            idEl.appendChild(span);
          }
          span.textContent = 'Analysis ID: not available';
          idEl.dataset.raw = '';
          idTextSpan = span;
          // remove any copy button if present
          if (copyIdBtn) { try { copyIdBtn.remove(); } catch {} }
        }
        if (genEl) genEl.textContent = 'Processed at: not available';
        if (footerEl) footerEl.hidden = false; idEl.hidden = false; genEl.hidden = false;
        if (toggleBtn) { toggleBtn.hidden = false; toggleBtn.textContent = 'Show raw JSON'; }
        // clear URL area
        if (urlEl) {
          urlEl.hidden = true;
          urlText.textContent = '';
          urlText.href = '#';
          if (copyUrlBtn) { try { copyUrlBtn.remove(); } catch(e) {} }
        }
      }

    } catch (err) {
      statusText.textContent = 'Error'; statusText.className = 'status err'; showError(err && err.message ? err.message : String(err));
    }
  });

  // toggle raw JSON (guard presence)
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      if (jsonEl.hidden) { jsonEl.hidden = false; toggleBtn.textContent = 'Hide raw JSON'; }
      else { jsonEl.hidden = true; toggleBtn.textContent = 'Show raw JSON'; }
    });
  }

  // copy button handlers
  function handleCopyButton(btn) {
    if (!btn) return;
    btn.addEventListener('click', () => {
      const raw = btn.dataset.raw || '';
      if (!raw) return;
      navigator.clipboard.writeText(raw).then(() => {
        const orig = btn.innerHTML;
        btn.innerHTML = '✅';
        setTimeout(() => btn.innerHTML = orig, 1500);
      }).catch(err => {
        console.error('copy failed', err);
      });
    });
  }

})();
