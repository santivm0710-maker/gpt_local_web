export class ChatApi {
  static async getJSON(url) {
    const res = await fetch(url);
    let body = {};
    try { body = await res.json(); } catch (_) { /* respuesta sin JSON */ }
    if (!res.ok) throw new Error(body.error || "Error " + res.status);
    return body;
  }

  static async postJSON(url, data) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data || {}),
    });
    let body = {};
    try { body = await res.json(); } catch (_) { /* respuesta sin JSON */ }
    if (!res.ok) throw new Error(body.error || "Error " + res.status);
    return body;
  }

  static async generateImage(prompt, model) {
    const res = await fetch("/api/imagen", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: prompt, model }),
    });
    if (!res.ok) {
      let body = {};
      try { body = await res.json(); } catch (_) { /* respuesta sin JSON */ }
      throw new Error(body.error || "Error " + res.status);
    }
    const blob = await res.blob();
    if (!blob.type.startsWith("image/")) {
      throw new Error("El servidor no devolvió una imagen válida");
    }
    return blob;
  }

  static async getInfo() {
    return this.getJSON("/api/info");
  }

  static async getConversations() {
    return this.getJSON("/api/conversaciones");
  }

  static async getConversation(id) {
    return this.getJSON("/api/conversaciones/" + encodeURIComponent(id));
  }

  static async createConversation() {
    return this.postJSON("/api/conversaciones");
  }

  static async sendMessage(conversationId, message) {
    return this.postJSON("/api/chat", { conversationId, message });
  }
}
