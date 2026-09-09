"use strict";

const out = document.getElementById("out");
const form = document.getElementById("form");
const input = document.getElementById("line");
const status = document.getElementById("status");
const resetBtn = document.getElementById("reset");
const ps1 = document.getElementById("ps1");
const chips = document.querySelectorAll(".chip");

let sessionId = null;
let halted = false;
const history = [];
let historyAt = 0;

function paint(text) {
  out.textContent += text;
  out.scrollTop = out.scrollHeight;
}

function setStatus(stats, isHalted) {
  const parts = [];
  if (isHalted) parts.push('<span class="halted">machine halted — press reboot</span>');
  if (stats) {
    parts.push(`tick ${stats.ticks}`);
    parts.push(`${stats.processes} procs`);
    parts.push(`${stats.objects} objects`);
    parts.push(`${stats.used_frames}/${stats.total_frames} frames`);
    parts.push(`${stats.syscalls} syscalls`);
  }
  status.innerHTML = parts.join("<span> · </span>") || "ready";
}

function syncInput() {
  input.disabled = halted;
  input.placeholder = halted
    ? "machine halted — press reboot"
    : "type a command — try: help";
  if (!halted) input.focus();
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

function apply(data) {
  paint(data.out || "");
  halted = Boolean(data.done);
  updatePrompt();
  setStatus(data.stats, halted);
  syncInput();
}

async function boot() {
  apply(await api("/api/session", {}));
}

async function send(line) {
  if (sessionId === null || halted) return;
  input.disabled = true;
  try {
    apply(await api(`/api/session/${sessionId}/exec`, { line }));
  } catch (error) {
    paint(`\n[net] ${error}\n`);
  } finally {
    syncInput();
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

chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    if (halted) return;
    paint(chip.dataset.cmd + "\n");
    send(chip.dataset.cmd);
    input.focus();
  });
});

resetBtn.addEventListener("click", async () => {
  if (sessionId === null) return;
  out.textContent = "";
  halted = false;
  syncInput();
  try {
    apply(await api(`/api/session/${sessionId}/reset`, {}));
  } catch (error) {
    paint(`[net] ${error}\n`);
  }
});

boot().catch((error) => {
  paint(`[net] cannot reach the kernel: ${error}\n`);
  status.innerHTML = '<span class="halted">offline</span>';
  syncInput();
});
