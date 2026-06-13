// Lógica de la SPA de Trackion: tickets, detalle, creación, asignación, comentarios.
(function () {
  if (!localStorage.getItem("trackion_token")) { location.href = "login.html"; return; }

  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const fmt = (d) => (d ? new Date(d).toLocaleString("es-MX", { dateStyle: "short", timeStyle: "short" }) : "—");
  const STATUS_LABEL = { open: "Abierto", in_progress: "En progreso", resolved: "Resuelto", closed: "Cerrado" };

  let CATALOG = { priorities: [], categories: [], users: [] };

  // ── Usuario ──
  const user = JSON.parse(localStorage.getItem("trackion_user") || "{}");
  $("userName").textContent = user.name || user.email || "Usuario";
  $("avatar").textContent = (user.name || "U").trim().charAt(0).toUpperCase();
  $("logout").addEventListener("click", (e) => { e.preventDefault(); localStorage.clear(); location.href = "login.html"; });

  // ── Modal ──
  const modalBg = $("modalBg");
  const closeModal = () => modalBg.classList.remove("show");
  modalBg.addEventListener("click", (e) => { if (e.target === modalBg) closeModal(); });
  function openModal(html) { $("modal").innerHTML = html; modalBg.classList.add("show"); }

  // ── Carga de catálogos ──
  async function loadCatalog() {
    try {
      const [p, c, u] = await Promise.all([TrackionAPI.priorities(), TrackionAPI.categories(), TrackionAPI.users()]);
      CATALOG.priorities = p.items || [];
      CATALOG.categories = c.items || [];
      CATALOG.users = u.items || [];
      const sel = $("fPriority");
      CATALOG.priorities.forEach((pr) => {
        const o = document.createElement("option"); o.value = pr.name; o.textContent = pr.name; sel.appendChild(o);
      });
    } catch (e) { /* catálogos opcionales para la tabla */ }
  }

  // ── Tabla de tickets ──
  async function loadTickets() {
    const qs = new URLSearchParams();
    if ($("fStatus").value) qs.set("status", $("fStatus").value);
    if ($("fPriority").value) qs.set("priority", $("fPriority").value);
    const rows = $("rows");
    rows.innerHTML = `<tr><td colspan="7" class="muted">Cargando…</td></tr>`;
    try {
      const data = await TrackionAPI.listTickets(qs.toString());
      const items = data.items || [];
      renderKpis(items);
      if (!items.length) { rows.innerHTML = `<tr><td colspan="7" class="muted">Sin tickets</td></tr>`; return; }
      rows.innerHTML = items.map((t) => `
        <tr data-id="${t.id}">
          <td>${t.id}</td>
          <td>${esc(t.subject)}</td>
          <td>${esc(t.category)}</td>
          <td class="pr-${esc(t.priority)}">${esc(t.priority)}</td>
          <td><span class="badge st-${t.status}">${STATUS_LABEL[t.status] || t.status}</span></td>
          <td>${esc(t.assignee || "—")}</td>
          <td class="muted">${fmt(t.created_at)}</td>
        </tr>`).join("");
      rows.querySelectorAll("tr[data-id]").forEach((tr) => tr.addEventListener("click", () => openTicket(tr.dataset.id)));
    } catch (e) {
      rows.innerHTML = `<tr><td colspan="7" class="error">${esc(e.message)}</td></tr>`;
    }
  }

  function renderKpis(items) {
    const by = (s) => items.filter((t) => t.status === s).length;
    $("kAbiertos").textContent = by("open");
    $("kProgreso").textContent = by("in_progress");
    $("kResueltos").textContent = by("resolved");
    $("kTotal").textContent = items.length;
  }

  // ── Detalle de ticket ──
  async function openTicket(id) {
    try {
      const t = await TrackionAPI.getTicket(id);
      const userOpts = CATALOG.users.map((u) => `<option value="${u.id}" ${u.id === t.assignee_id ? "selected" : ""}>${esc(u.name)}</option>`).join("");
      const statusOpts = Object.keys(STATUS_LABEL).map((s) => `<option value="${s}" ${s === t.status ? "selected" : ""}>${STATUS_LABEL[s]}</option>`).join("");
      const comments = (t.comments || []).map((c) => `<div class="comment"><div class="who">${esc(c.author)} · ${fmt(c.created_at)}</div><div>${esc(c.body)}</div></div>`).join("") || `<div class="muted">Sin comentarios</div>`;
      openModal(`
        <h3>#${t.id} · ${esc(t.subject)}</h3>
        <div class="muted">${esc(t.category)}${t.subcategory ? " / " + esc(t.subcategory) : ""} · prioridad <b class="pr-${esc(t.priority)}">${esc(t.priority)}</b> · creado ${fmt(t.created_at)}</div>
        <p>${esc(t.description) || "<span class='muted'>Sin descripción</span>"}</p>
        <div class="row">
          <div><label>Estado</label><select id="dStatus">${statusOpts}</select></div>
          <div><label>Asignar a</label><select id="dAssignee"><option value="">— sin asignar —</option>${userOpts}</select></div>
        </div>
        <div class="right">
          <button class="btn ghost" id="dClose">Cerrar</button>
          <button class="btn accent" id="dSave">Guardar cambios</button>
        </div>
        <div class="comments">
          <h4>Comentarios</h4>
          <div id="dComments">${comments}</div>
          <label>Nuevo comentario</label>
          <textarea id="dComment" rows="2" placeholder="Escribe un comentario…"></textarea>
          <div class="right"><button class="btn" id="dAddComment">Comentar</button></div>
        </div>
        <div class="error" id="dErr"></div>
      `);
      $("dClose").addEventListener("click", closeModal);
      $("dSave").addEventListener("click", async () => {
        try {
          const newStatus = $("dStatus").value;
          if (newStatus !== t.status) await TrackionAPI.updateTicket(t.id, { status: newStatus });
          const a = $("dAssignee").value;
          if (a && Number(a) !== t.assignee_id) await TrackionAPI.assignTicket(t.id, Number(a));
          closeModal(); loadTickets();
        } catch (e) { $("dErr").textContent = e.message; }
      });
      $("dAddComment").addEventListener("click", async () => {
        const body = $("dComment").value.trim();
        if (!body) return;
        try { await TrackionAPI.addComment(t.id, body); openTicket(t.id); }
        catch (e) { $("dErr").textContent = e.message; }
      });
    } catch (e) { alert(e.message); }
  }

  // ── Nuevo ticket ──
  function openNew() {
    const catOpts = CATALOG.categories.map((c) => `<option value="${c.id}">${esc(c.name)}</option>`).join("");
    const priOpts = CATALOG.priorities.map((p) => `<option value="${p.id}">${esc(p.name)}</option>`).join("");
    openModal(`
      <h3>Nuevo ticket</h3>
      <label>Asunto</label><input id="nSubject" />
      <label>Descripción</label><textarea id="nDesc" rows="3"></textarea>
      <div class="row">
        <div><label>Categoría</label><select id="nCat">${catOpts}</select></div>
        <div><label>Prioridad</label><select id="nPri">${priOpts}</select></div>
      </div>
      <div class="right">
        <button class="btn ghost" id="nCancel">Cancelar</button>
        <button class="btn accent" id="nCreate">Crear</button>
      </div>
      <div class="error" id="nErr"></div>
    `);
    $("nCancel").addEventListener("click", closeModal);
    $("nCreate").addEventListener("click", async () => {
      try {
        await TrackionAPI.createTicket({
          subject: $("nSubject").value.trim(),
          description: $("nDesc").value.trim(),
          category_id: Number($("nCat").value),
          priority_id: Number($("nPri").value),
        });
        closeModal(); loadTickets();
      } catch (e) { $("nErr").textContent = e.message; }
    });
  }

  // ── Integraciones ──
  async function openIntegrations() {
    try {
      const data = await TrackionAPI.integrations();
      const rows = (data.items || []).map((i) => `
        <tr><td>${esc(i.name)}</td><td>${esc(i.description)}</td>
        <td><span class="badge ${i.is_active ? "st-resolved" : "st-closed"}">${i.is_active ? "activa" : "inactiva"}</span></td>
        <td class="muted">${(i.supported_events || []).join(", ")}</td></tr>`).join("");
      openModal(`<h3>Integraciones</h3><p class="muted">Módulo extensible: agrega integraciones sin tocar el núcleo.</p>
        <table><thead><tr><th>Nombre</th><th>Descripción</th><th>Estado</th><th>Eventos</th></tr></thead><tbody>${rows}</tbody></table>
        <div class="right"><button class="btn ghost" onclick="document.getElementById('modalBg').classList.remove('show')">Cerrar</button></div>`);
    } catch (e) { alert(e.message); }
  }

  // ── Estado / health ──
  async function openHealth() {
    try {
      const h = await TrackionAPI.health();
      openModal(`<h3>Estado del servicio</h3>
        <p>Servicio: <span class="badge st-resolved">${esc(h.status)}</span></p>
        <p>Base de datos: <b>${esc(h.db)}</b></p>
        <p class="muted">Versión ${esc(h.version)}</p>
        <div class="right"><button class="btn ghost" onclick="document.getElementById('modalBg').classList.remove('show')">Cerrar</button></div>`);
    } catch (e) { alert(e.message); }
  }

  // ── Eventos UI ──
  $("btnFilter").addEventListener("click", loadTickets);
  $("btnNew").addEventListener("click", openNew);
  $("navNew").addEventListener("click", (e) => { e.preventDefault(); openNew(); });
  $("navIntegrations").addEventListener("click", (e) => { e.preventDefault(); openIntegrations(); });
  $("navHealth").addEventListener("click", (e) => { e.preventDefault(); openHealth(); });

  // ── Arranque ──
  (async () => { await loadCatalog(); await loadTickets(); })();
})();
