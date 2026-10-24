// Small progressive enhancements: tabs, lazy Mermaid rendering, code viewer, progress tracking, test runner.
(function () {
  const dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  if (window.mermaid) mermaid.initialize({ startOnLoad: false, theme: dark ? "dark" : "default", securityLevel: "strict", flowchart: { htmlLabels: true } });

  // Mermaid can't measure hidden elements, so only render diagrams that are currently visible.
  function renderVisibleDiagrams() {
    if (!window.mermaid) return;
    const nodes = [...document.querySelectorAll("pre.mermaid:not([data-processed])")].filter((n) => n.offsetParent !== null);
    if (nodes.length) mermaid.run({ nodes }).catch((e) => console.error(e));
  }

  // ---- progress (stored in this browser only)
  const KEY = "pp-progress";
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch { return {}; } };
  const save = (v) => { try { localStorage.setItem(KEY, JSON.stringify(v)); } catch {} };
  function paintProgress() {
    const done = load();
    document.querySelectorAll("[data-done]").forEach((el) => el.classList.toggle("done", !!done[el.dataset.done]));
    document.querySelectorAll("[data-complete]").forEach((el) => { el.checked = !!done[el.dataset.complete]; });
    const total = new Set([...document.querySelectorAll(".nav-level [data-done]")].map((e) => e.dataset.done)).size;
    const n = Object.values(done).filter(Boolean).length;
    const bar = document.getElementById("progress-bar");
    if (bar && total) { bar.style.width = `${(100 * n) / total}%`; document.getElementById("progress-text").textContent = `${n} / ${total} projects complete`; }
  }
  document.querySelectorAll("[data-complete]").forEach((box) => box.addEventListener("change", () => {
    const done = load(); done[box.dataset.complete] = box.checked; save(done); paintProgress();
  }));
  paintProgress();

  // ---- tabs (the URL hash remembers the open tab)
  const tabs = [...document.querySelectorAll("[data-tab]")];
  function openTab(name) {
    if (!tabs.length) return;
    if (!tabs.some((t) => t.dataset.tab === name)) name = tabs[0].dataset.tab;
    tabs.forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.toggle("active", p.id === `tab-${name}`));
    history.replaceState(null, "", `#${name}`);
    renderVisibleDiagrams();
  }
  tabs.forEach((t) => t.addEventListener("click", () => openTab(t.dataset.tab)));
  document.querySelectorAll("[data-tab-link]").forEach((b) => b.addEventListener("click", () => { openTab(b.dataset.tabLink); window.scrollTo({ top: document.querySelector(".tabs").offsetTop - 10, behavior: "smooth" }); }));
  openTab(location.hash.slice(1));

  // ---- code viewer
  function openFile(name) {
    document.querySelectorAll("[data-file]").forEach((b) => b.classList.toggle("active", b.dataset.file === name));
    document.querySelectorAll("[data-file-body]").forEach((f) => { f.hidden = f.dataset.fileBody !== name; });
  }
  document.querySelectorAll("[data-file]").forEach((b) => b.addEventListener("click", () => openFile(b.dataset.file)));
  document.querySelectorAll("[data-open-file]").forEach((a) => a.addEventListener("click", (e) => {
    e.preventDefault(); openTab("code"); openFile(a.dataset.openFile);
  }));

  // ---- test runner
  const runBtn = document.getElementById("run-tests");
  if (runBtn) runBtn.addEventListener("click", async () => {
    const out = document.getElementById("test-output");
    runBtn.disabled = true; out.className = "terminal"; out.textContent = "Running pytest…";
    try {
      const res = await fetch(`/api/projects/${runBtn.dataset.slug}/tests`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
      const data = await res.json();
      out.textContent = data.output; out.classList.add(data.ok ? "ok" : "fail");
    } catch (e) { out.textContent = `Could not run the tests: ${e}`; out.classList.add("fail"); }
    runBtn.disabled = false;
  });

  renderVisibleDiagrams();
})();
