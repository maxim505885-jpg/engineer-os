/* Read-only original PDF raster viewer. Vendored pdfjs-dist 5.4.624, Apache-2.0. */
(function () {
  'use strict';
  const MAX_BYTES = 100 * 1024 * 1024, MAX_PIXELS = 4000000, MAX_SIDE = 4096;
  let current = null, libraryPromise = null;
  const loadLibrary = () => libraryPromise || (libraryPromise = import('/vendor/pdfjs/pdf.mjs').catch(error => {
    libraryPromise = null; throw error;
  }));
  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function destroy(state) {
    if (!state || state.closed) return;
    state.closed = true;
    if (state.renderTask) state.renderTask.cancel();
    if (state.loadingTask) Promise.resolve(state.loadingTask.destroy()).catch(() => {});
    state.dialog.remove();
    if (state.restoreFocus && state.restoreFocus.isConnected) state.restoreFocus.focus();
  }
  function closePDFViewer() {
    const state = current; current = null; destroy(state);
  }
  const alive = state => current === state && !state.closed;
  function controls(state) {
    state.previous.disabled = !state.pdf || state.page <= 1;
    state.next.disabled = !state.pdf || state.page >= state.pdf.numPages;
    state.zoomOut.disabled = !state.pdf || state.zoom <= 0.5;
    state.zoomIn.disabled = !state.pdf || state.zoom >= 3;
    state.position.textContent = state.pdf ? `Страница ${state.page} / ${state.pdf.numPages} · ${Math.round(state.zoom * 100)}%` : 'Загрузка PDF';
  }
  function requestRender(state) {
    state.revision += 1; controls(state);
    if (state.renderTask) state.renderTask.cancel();
    if (!state.rendering) void render(state);
  }
  async function render(state) {
    state.rendering = true;
    try {
      while (alive(state) && state.pdf && state.renderedRevision !== state.revision) {
        const revision = state.revision, pageNumber = state.page, zoom = state.zoom;
        state.status.textContent = 'Отображение оригинальной страницы PDF…';
        let page;
        try {
          page = await state.pdf.getPage(pageNumber);
          if (!alive(state) || revision !== state.revision) continue;
          const native = page.getViewport({scale: 1});
          const ratio = Math.min(zoom, MAX_SIDE / native.width, MAX_SIDE / native.height,
            Math.sqrt(MAX_PIXELS / (native.width * native.height)));
          const viewport = page.getViewport({scale: ratio});
          if (!Number.isFinite(viewport.width) || !Number.isFinite(viewport.height) || viewport.width <= 0 || viewport.height <= 0) throw new Error('Invalid page dimensions');
          state.canvas.width = Math.max(1, Math.floor(viewport.width));
          state.canvas.height = Math.max(1, Math.floor(viewport.height));
          state.canvas.setAttribute('aria-label', `Оригинальный PDF page ${pageNumber}`);
          state.renderTask = page.render({canvasContext: state.canvas.getContext('2d'), viewport, annotationMode: 0});
          await state.renderTask.promise;
          if (alive(state) && revision === state.revision) {
            state.renderedRevision = revision;
            state.status.textContent = 'Оригинальная страница PDF · содержимое источника не проверено';
          }
        } catch (error) {
          if (!alive(state)) break;
          if (revision !== state.revision || error.name === 'RenderingCancelledException') continue;
          state.renderedRevision = revision;
          state.status.textContent = 'Не удалось отобразить страницу. Оригинальный файл сохранён.';
        } finally {
          state.renderTask = null;
          if (page) page.cleanup();
        }
      }
    } finally { state.rendering = false; }
  }
  async function openPDFViewer(bytesUint8Array, sourceSha, caption) {
    closePDFViewer();
    if (!(bytesUint8Array instanceof Uint8Array) || !bytesUint8Array.length || bytesUint8Array.length > MAX_BYTES) {
      throw new Error('Предпросмотр требует непустой оригинальный PDF размером не более 100 MiB.');
    }
    const dialog = element('dialog', 'pdf-viewer');
    const panel = element('section', 'pdf-viewer-panel');
    const heading = element('h2', 'pdf-viewer-heading', 'Оригинальный PDF');
    heading.id = 'pdf-viewer-heading'; dialog.setAttribute('aria-labelledby', heading.id);
    const captionNode = element('p', 'pdf-viewer-caption', String(caption || ''));
    const identity = element('p', 'pdf-viewer-caption', `SHA-256 источника: ${String(sourceSha || 'неизвестен')}`);
    const toolbar = element('div', 'pdf-viewer-toolbar');
    const position = element('span', 'pdf-viewer-controls');
    const status = element('p', 'pdf-viewer-status', 'Загрузка оригинального PDF…');
    status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
    const wrap = element('div', 'pdf-viewer-canvas-wrap');
    const canvas = element('canvas', 'pdf-viewer-canvas'); wrap.append(canvas);
    const state = {dialog, canvas, position, status, page: 1, zoom: 1, revision: 0,
      renderedRevision: -1, rendering: false, closed: false, restoreFocus: document.activeElement};
    function button(text, action) {
      const node = element('button', '', text); node.type = 'button';
      node.addEventListener('click', action); toolbar.append(node); return node;
    }
    state.previous = button('Предыдущая страница', () => {if (state.pdf && state.page > 1) {state.page--; requestRender(state);}});
    state.next = button('Следующая страница', () => {if (state.pdf && state.page < state.pdf.numPages) {state.page++; requestRender(state);}});
    state.zoomOut = button('Уменьшить', () => {if (state.pdf && state.zoom > .5) {state.zoom = Math.max(.5, state.zoom - .25); requestRender(state);}});
    state.zoomIn = button('Увеличить', () => {if (state.pdf && state.zoom < 3) {state.zoom = Math.min(3, state.zoom + .25); requestRender(state);}});
    toolbar.append(position); const close = button('Закрыть PDF', closePDFViewer);
    panel.append(heading, captionNode, identity, toolbar, status, wrap); dialog.append(panel);
    dialog.addEventListener('cancel', event => {event.preventDefault(); closePDFViewer();});
    dialog.addEventListener('close', () => {if (alive(state)) closePDFViewer();});
    current = state; controls(state); document.body.append(dialog); dialog.showModal(); close.focus();
    try {
      const pdfjs = await loadLibrary();
      if (!alive(state)) return;
      pdfjs.GlobalWorkerOptions.workerSrc = '/vendor/pdfjs/pdf.worker.mjs';
      // Data-only canvas API: no annotation layer, scripting manager, actions, or forms.
      state.loadingTask = pdfjs.getDocument({data: bytesUint8Array.slice(), isEvalSupported: false,
        enableXfa: false, useWasm: false, useWorkerFetch: false, disableFontFace: true,
        useSystemFonts: false, disableAutoFetch: true, disableStream: true, disableRange: true,
        maxImageSize: MAX_PIXELS, canvasMaxAreaInBytes: MAX_PIXELS * 4,
        cMapUrl: undefined, standardFontDataUrl: undefined, wasmUrl: undefined});
      state.loadingTask.onPassword = () => {
        if (alive(state)) state.status.textContent = 'Предпросмотр PDF с паролем недоступен. Оригинальный файл сохранён.';
        Promise.resolve(state.loadingTask.destroy()).catch(() => {});
      };
      const pdf = await state.loadingTask.promise;
      if (!alive(state)) {await pdf.destroy(); return;}
      state.pdf = pdf; requestRender(state);
    } catch (error) {
      if (alive(state) && !state.status.textContent.startsWith('Предпросмотр PDF с паролем')) {
        state.status.textContent = 'Предпросмотр PDF недоступен. Оригинальный файл сохранён.';
      }
    }
  }
  window.openPDFViewer = openPDFViewer;
  window.closePDFViewer = closePDFViewer;
})();
