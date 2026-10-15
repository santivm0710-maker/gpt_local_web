import { ChatApi } from "./ChatApi.js";
import { ChatView } from "./ChatView.js";

export class ChatApp {
  constructor() {
    this.view = new ChatView();
    this.form = document.getElementById("form");
    this.clearBtn = document.getElementById("clear");
    this.exitBtn = document.getElementById("exit");
    this.bindEvents();
  }

  bindEvents() {
    this.form.addEventListener("submit", (ev) => {
      ev.preventDefault();
      this.sendMessage();
    });
    this.view.imageBtn.addEventListener("click", () => this.generateImage());
    this.clearBtn.addEventListener("click", () => this.view.clear());
    this.exitBtn.addEventListener("click", () => this.exitApp());
  }

  async exitApp() {
    try { await ChatApi.postJSON("/api/salir"); } catch (_) { /* el servidor ya pudo cerrarse */ }
    this.view.showStopped();
  }

  async sendMessage() {
    const msg = this.view.input.value.trim();
    if (!msg) return;
    if (msg.toLowerCase() === "salir") return this.exitApp();

    this.view.hideError();
    this.view.input.value = "";
    this.view.addMessage("user", msg);
    this.view.setBusy(true);
    const pending = this.view.addMessage("ia", "Pensando");
    pending.classList.add("typing");

    try {
      const { reply } = await ChatApi.postJSON("/api/chat", { message: msg });
      pending.remove();
      this.view.addMessage("ia", reply);
    } catch (e) {
      pending.remove();
      this.view.showError(e.message || String(e));
    } finally {
      this.view.setBusy(false);
    }
  }

  async generateImage() {
    const prompt = this.view.input.value.trim();
    if (!prompt) return;

    this.view.hideError();
    this.view.input.value = "";
    this.view.addMessage("user", prompt);
    this.view.setBusy(true);
    const pending = this.view.addMessage("ia", "Generando imagen");
    pending.classList.add("typing");

    try {
      const blob = await ChatApi.generateImage(prompt, this.view.imageModel.value);
      const url = URL.createObjectURL(blob);
      this.view.imageUrls.add(url);
      pending.remove();
      this.view.addImageMessage(url, prompt);
    } catch (e) {
      pending.remove();
      this.view.showError(e.message || String(e));
    } finally {
      this.view.setBusy(false);
    }
  }

  async start() {
    let model = "desconocido";
    try {
      const info = await ChatApi.getInfo();
      model = info.model;
      this.view.setImageModels(info.imageModels, info.defaultImageModel);
    } catch (_) {}
    this.view.setModel(model);
    this.view.showWelcome(model);
  }
}
