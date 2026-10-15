const LABELS = { user: "Tú", ia: "IA", sistema: "Sistema" };

export class ChatView {
  constructor() {
    this.chat = document.getElementById("chat");
    this.input = document.getElementById("input");
    this.sendBtn = document.getElementById("send");
    this.imageBtn = document.getElementById("image");
    this.imageModel = document.getElementById("image-model");
    this.errorBox = document.getElementById("error");
    this.modelLabel = document.getElementById("model");
    this.imageUrls = new Set();
  }

  addMessage(kind, text) {
    const el = document.createElement("div");
    el.className = "msg " + kind;
    const who = document.createElement("span");
    who.className = "who";
    who.textContent = LABELS[kind];
    // Usa textContent para que el texto del modelo no pueda ejecutar HTML.
    el.append(who, document.createTextNode(text));
    this.chat.appendChild(el);
    this.scrollToBottom();
    return el;
  }

  addImageMessage(url, prompt) {
    const el = document.createElement("div");
    el.className = "msg ia image";
    const image = document.createElement("img");
    image.src = url;
    image.alt = prompt;
    const download = document.createElement("a");
    download.href = url;
    download.download = "imagen-generada.jpg";
    download.textContent = "Descargar imagen";
    el.append(image, download);
    this.chat.appendChild(el);
    this.scrollToBottom();
  }

  showError(text) {
    this.errorBox.textContent = text;
    this.errorBox.hidden = false;
  }

  hideError() {
    this.errorBox.hidden = true;
    this.errorBox.textContent = "";
  }

  setBusy(busy) {
    this.sendBtn.disabled = busy;
    this.imageBtn.disabled = busy;
    this.imageModel.disabled = busy;
    this.input.disabled = busy;
    if (!busy) this.input.focus();
  }

  clear() {
    this.chat.replaceChildren();
    for (const url of this.imageUrls) URL.revokeObjectURL(url);
    this.imageUrls.clear();
    this.hideError();
    this.input.focus();
  }

  showStopped() {
    document.body.innerHTML =
      '<main class="app"><p class="msg sistema">Servidor detenido. Ya puedes cerrar esta pestaña.</p></main>';
  }

  setModel(model) {
    this.modelLabel.textContent = model;
  }

  setImageModels(models, defaultModel) {
    this.imageModel.replaceChildren();
    for (const model of models) {
      const option = document.createElement("option");
      option.value = model.id;
      option.textContent = model.name + " — " + model.description;
      this.imageModel.appendChild(option);
    }
    this.imageModel.value = defaultModel;
  }

  showWelcome(model) {
    this.addMessage("sistema", "Chat local iniciado con el modelo: " + model);
    this.addMessage("sistema", "Escribí un mensaje y presioná Enter o Enviar. Para crear una imagen, escribí su descripción y presioná Crear imagen.");
    this.addMessage("sistema", "La generación usa Cloudflare Workers AI; tu descripción se envía a su servicio.");
  }

  scrollToBottom() {
    this.chat.scrollTop = this.chat.scrollHeight;
  }
}
