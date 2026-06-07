// Фирменный вид нод HOTCUT + кнопка баланса на ноде «HOTCUT API».
// Цвета ставим через nodeCreated И loadedGraphNode — чтобы и новые, и загруженные
// из сохранённого графа ноды были одинаковыми. Без рескина чрома ComfyUI.
import { app } from "../../scripts/app.js";

const ACCENT = "#ff6b35"; // бренд HOTCUT
const TITLE_BG = "#1a1412"; // тёмный тёплый заголовок
const BODY_BG = "#0e0e10"; // near-black тело

const HOTCUT_NODES = new Set([
  "HotcutConfig",
  "HotcutGptImage2",
  "HotcutGptImage2Edit",
  "HotcutRemoveBackground",
]);
const GEN_NODES = new Set(["HotcutGptImage2", "HotcutGptImage2Edit"]);
// Огни по resolution — синхронно с lib/economics.ts (GPT_IMAGE_2)
const FLAMES_BY_RES = { "1K": 39, "2K": 65, "4K": 103 };
// Модели с фиксированной ценой
const FLAMES_FIXED = { HotcutRemoveBackground: 10 };

const logo = new Image();
logo.src = new URL("./hotcut_logo.png", import.meta.url).href;
let logoReady = false;
logo.onload = () => {
  logoReady = true;
};

function applyStyle(node) {
  node.color = TITLE_BG;
  node.bgcolor = BODY_BG;
}

// Кнопка «Проверить баланс» на ноде HOTCUT API: дёргает локальный роут ComfyUI
// (/hotcut/balance, тот же origin → без CORS), показывает результат на себе.
function setupBalanceButton(node) {
  if (node.__hotcutBalanceBtn) return;
  node.__hotcutBalanceBtn = true;
  const btn = node.addWidget("button", "Проверить баланс 🔥", "", async () => {
    const apiKey = node.widgets?.find((w) => w.name === "api_key")?.value || "";
    const baseUrl = node.widgets?.find((w) => w.name === "base_url")?.value || "https://hotcut.ru";
    btn.name = "Проверяю…";
    node.setDirtyCanvas(true, true);
    try {
      const res = await fetch("/hotcut/balance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: apiKey, base_url: baseUrl }),
      });
      const data = await res.json();
      btn.name = res.ok
        ? `🔥 ${data.flames} огней — обновить`
        : `Ошибка: ${data.error || res.status} — повторить`;
    } catch (e) {
      btn.name = "Ошибка сети — повторить";
    }
    node.setDirtyCanvas(true, true);
  });
}

function setup(node) {
  if (!node || !HOTCUT_NODES.has(node.comfyClass)) return;
  applyStyle(node);
  if (node.comfyClass === "HotcutConfig") setupBalanceButton(node);
}

app.registerExtension({
  name: "HOTCUT.branding",
  nodeCreated(node) {
    setup(node);
  },
  loadedGraphNode(node) {
    setup(node);
  },
  async beforeRegisterNodeDef(nodeType, nodeData) {
    const className = nodeData?.name;
    if (!HOTCUT_NODES.has(className)) return;

    // Лого в заголовке + превью стоимости в огнях
    const onDrawForeground = nodeType.prototype.onDrawForeground;
    nodeType.prototype.onDrawForeground = function (ctx) {
      onDrawForeground?.apply(this, arguments);
      if (this.flags?.collapsed) return;

      const titleH = (window.LiteGraph && window.LiteGraph.NODE_TITLE_HEIGHT) || 20;
      const w = this.size[0];

      let logoLeft = w - 8;
      if (logoReady) {
        const s = 14;
        logoLeft = w - s - 8;
        ctx.drawImage(logo, logoLeft, -titleH + (titleH - s) / 2, s, s);
      }

      let flames = null;
      if (GEN_NODES.has(className)) {
        const resW = this.widgets?.find((wd) => wd.name === "resolution");
        const res = (resW && resW.value) || "1K";
        flames = FLAMES_BY_RES[res] || FLAMES_BY_RES["1K"];
      } else if (FLAMES_FIXED[className] != null) {
        flames = FLAMES_FIXED[className];
      }
      if (flames != null) {
        ctx.save();
        ctx.fillStyle = ACCENT;
        ctx.font = "12px sans-serif";
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        ctx.fillText(`≈ ${flames} 🔥`, logoLeft - 6, -titleH / 2);
        ctx.restore();
      }
    };
  },
});
