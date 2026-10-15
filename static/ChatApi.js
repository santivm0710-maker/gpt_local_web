export class ChatApi {
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
    const res = await fetch("/api/info");
    if (!res.ok) throw new Error("Error " + res.status);
    return res.json();
  }
}
