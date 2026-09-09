"use strict";

const out = document.getElementById("out");
const form = document.getElementById("form");
const input = document.getElementById("line");
const status = document.getElementById("status");
const resetBtn = document.getElementById("reset");
const ps1 = document.getElementById("ps1");

let sessionId = null;
let halted = false;
const history = [];
let historyAt = 0;

function paint(text) {
  out.textContent += text;
  out.scrollTop = out.scrollHeight;
}

function setStatus(text, isHalted) {
  status.textContent = text;
  status.classList.toggle("halted", Boolean(isHalted));
}

function updatePrompt() {
  // The shell prints its own prompt; mirror the last one for the input row.
  const lines = out.textContent.split("\n");
  for (let i = lines.length - 1; i >= 0; i--) {
    const match = lines[i].match(/^(\S*)\s\$\s$/);
    if (match) {
      ps1.textContent = (match[1] || "/") + " $";
      return;
    }
  }
}

async function api(path, body) {
  const response = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) throw new Error("HTTP " + response.status);
  return response.json();
}

async function boot() {
  const data = await api("/api/session", {});
  sessionId = data.id;
  halted = data.done;
  paint(data.out);
  updatePrompt();
  setStatus(halted ? "machine halted — press reboot" : "ready — type 'help'", halted);
}

async function send(line) {
  if (sessionId === null || halted) return;
  input.disabled = true;
  try {
    const data = await api(`/api/session/${sessionId}/exec`, { line });
    paint(data.out);
    halted = data.done;
    updatePrompt();
    if (halted) setStatus("machine halted — press reboot", true);
  } catch (error) {
    paint(`\n[net] ${error}\n`);
  } finally {
    input.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const line = input.value;
  input.value = "";
  if (line.trim()) {
    history.push(line);
    historyAt = history.length;
  }
  paint(line + "\n");
  send(line);
});

input.addEventListener("keydown", (event) => {
  if (event.key === "ArrowUp") {
    event.preventDefault();
    if (historyAt > 0) input.value = history[--historyAt];
  } else if (event.key === "ArrowDown") {
    event.preventDefault();
    if (historyAt < history.length - 1) input.value = history[++historyAt];
    else { historyAt = history.length; input.value = ""; }
  } else if (event.key === "l" && event.ctrlKey) {
    event.preventDefault();
    out.textContent = "";
  }
});

resetBtn.addEventListener("click", async () => {
  if (sessionId === null) return;
  out.textContent = "";
  halted = false;
  const data = await api(`/api/session/${sessionId}/reset`, {});
  paint(data.out);
  halted = data.done;
  updatePrompt();
  setStatus(halted ? "machine halted — press reboot" : "rebooted", halted);
  input.focus();
});

boot().catch((error) => {
  paint(`[net] cannot reach the kernel: ${error}\n`);
  setStatus("offline", true);
});
