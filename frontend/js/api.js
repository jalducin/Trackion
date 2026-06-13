// Cliente HTTP de Trackion. Adjunta el JWT (localStorage.trackion_token) en cada petición.
const TrackionAPI = (() => {
  const base = () => (window.TRACKION_CONFIG && window.TRACKION_CONFIG.API_BASE) || "";
  const token = () => localStorage.getItem("trackion_token");

  async function request(method, path, body) {
    const headers = { "Content-Type": "application/json" };
    const t = token();
    if (t) headers["Authorization"] = `Bearer ${t}`;
    const res = await fetch(base() + path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
    let data = null;
    const text = await res.text();
    try { data = text ? JSON.parse(text) : null; } catch { data = text; }
    if (res.status === 401) {
      localStorage.removeItem("trackion_token");
      if (!location.pathname.endsWith("login.html")) location.href = "login.html";
    }
    if (!res.ok) {
      const msg = (data && data.error && data.error.message) || `HTTP ${res.status}`;
      throw new Error(msg);
    }
    return data;
  }

  return {
    login: (email, password) => request("POST", "/auth/login", { email, password }),
    me: () => request("GET", "/auth/me"),
    health: () => request("GET", "/health"),
    listTickets: (qs = "") => request("GET", "/tickets" + (qs ? `?${qs}` : "")),
    getTicket: (id) => request("GET", `/tickets/${id}`),
    createTicket: (payload) => request("POST", "/tickets", payload),
    updateTicket: (id, payload) => request("PUT", `/tickets/${id}`, payload),
    assignTicket: (id, assignee_id) => request("POST", `/tickets/${id}/assign`, { assignee_id }),
    addComment: (id, bodyText) => request("POST", `/tickets/${id}/comments`, { body: bodyText }),
    categories: () => request("GET", "/catalog/categories"),
    priorities: () => request("GET", "/catalog/priorities"),
    users: () => request("GET", "/catalog/users"),
    integrations: () => request("GET", "/integrations"),
  };
})();
