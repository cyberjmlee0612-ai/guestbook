const form = document.querySelector("#entry-form");
const entries = document.querySelector("#entries");
const statusText = document.querySelector("#form-status");

function showStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.className = isError ? "status error" : "status success";
}

function renderEntries(items) {
  entries.replaceChildren();
  if (items.length === 0) {
    entries.textContent = "아직 방명록이 없습니다. 첫 인사를 남겨 보세요.";
    return;
  }
  for (const item of items) {
    const article = document.createElement("article");
    article.className = "entry";
    const heading = document.createElement("div");
    heading.className = "entry-heading";
    const name = document.createElement("strong");
    name.textContent = item.name;
    const date = document.createElement("time");
    date.textContent = item.created_at;
    heading.append(name, date);
    const message = document.createElement("p");
    message.textContent = item.message;
    const remove = document.createElement("button");
    remove.className = "delete-button";
    remove.type = "button";
    remove.textContent = "삭제";
    remove.addEventListener("click", () => removeEntry(item.id));
    article.append(heading, message, remove);
    entries.append(article);
  }
}

async function loadEntries() {
  entries.textContent = "불러오는 중...";
  try {
    const response = await fetch("/api/entries");
    if (!response.ok) throw new Error("목록을 불러오지 못했습니다.");
    renderEntries(await response.json());
  } catch (error) {
    entries.textContent = error.message;
  }
}

async function removeEntry(id) {
  if (!window.confirm("이 방명록을 삭제할까요?")) return;
  const response = await fetch(`/api/entries/${id}`, { method: "DELETE" });
  if (response.ok) await loadEntries();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const body = {
    name: document.querySelector("#name").value,
    message: document.querySelector("#message").value,
  };
  try {
    const response = await fetch("/api/entries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) throw new Error("이름과 메시지를 확인해 주세요.");
    form.reset();
    showStatus("방명록을 남겼습니다.");
    await loadEntries();
  } catch (error) {
    showStatus(error.message, true);
  }
});

document.querySelector("#refresh-button").addEventListener("click", loadEntries);
loadEntries();
