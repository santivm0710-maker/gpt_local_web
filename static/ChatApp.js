import { ChatApi } from "./ChatApi.js";
import { ChatView } from "./ChatView.js";

export class ChatApp {
  constructor() {
    this.view = new ChatView();
    this.form = document.getElementById("form");
    this.exitBtn = document.getElementById("exit");
    this.conversationId = null;
    this.bindEvents();
  }

  bindEvents() {
    this.form.addEventListener("submit", (ev) => {
      ev.preventDefault();
      this.sendMessage();
    });
    this.view.imageBtn.addEventListener("click", () => this.generateImage());
    this.view.conversationSelect.addEventListener("change", () => {
      const id = Number(this.view.conversationSelect.value);
      if (id) this.loadConversation(id);
    });
    this.view.newConversationBtn.addEventListener("click", () => this.createConversation());
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
    const userMessage = this.view.addMessage("user", msg);
    this.view.setBusy(true);
    const pending = this.view.addMessage("ia", "Pensando");
    pending.classList.add("typing");

    try {
      const { reply } = await ChatApi.sendMessage(this.conversationId, msg);
      pending.remove();
      this.view.addMessage("ia", reply);
      try {
        await this.refreshConversations(this.conversationId);
      } catch (e) {
        this.view.showError("El mensaje se guardó, pero no se pudo actualizar la lista: " + (e.message || e));
      }
    } catch (e) {
      pending.remove();
      userMessage.remove();
      this.view.input.value = msg;
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
    const startupErrors = [];
    try {
      const info = await ChatApi.getInfo();
      const model = info.model;
      this.view.setImageModels(info.imageModels, info.defaultImageModel);
      this.view.setModel(model);
    } catch (e) { startupErrors.push(e.message || String(e)); }
    try {
      const { conversations } = await ChatApi.getConversations();
      if (conversations.length) {
        this.view.setConversations(conversations, conversations[0].id);
        await this.loadConversation(conversations[0].id);
      } else {
        await this.createConversation();
      }
    } catch (e) { startupErrors.push(e.message || String(e)); }
    if (startupErrors.length) this.view.showError(startupErrors.join("; "));
  }

  async refreshConversations(activeId) {
    const { conversations } = await ChatApi.getConversations();
    this.view.setConversations(conversations, activeId);
  }

  async createConversation() {
    this.view.setBusy(true);
    try {
      const { conversation } = await ChatApi.createConversation();
      await this.refreshConversations(conversation.id);
      await this.loadConversation(conversation.id);
    } catch (e) {
      this.view.showError(e.message || String(e));
    } finally {
      this.view.setBusy(false);
    }
  }

  async loadConversation(id) {
    this.view.setBusy(true);
    try {
      const { conversation } = await ChatApi.getConversation(id);
      this.conversationId = conversation.id;
      this.view.clear();
      this.view.conversationSelect.value = String(conversation.id);
      if (conversation.messages.length) {
        for (const message of conversation.messages) {
          this.view.addMessage(message.role === "user" ? "user" : "ia", message.content);
        }
      } else {
        this.view.showWelcome(this.view.modelLabel.textContent);
      }
    } catch (e) {
      this.view.showError(e.message || String(e));
      if (this.conversationId) this.view.conversationSelect.value = String(this.conversationId);
    } finally {
      this.view.setBusy(false);
    }
  }
}
