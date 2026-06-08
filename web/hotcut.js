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

// Ограничения провайдера — зеркало normalizeResolution на бэке
// (app/api/v1/images/route.ts): auto → только 1K; 1:1 не даёт 4K → 2K.
// Списание идёт по нормализованному разрешению, поэтому и превью считаем так же.
function normalizeRes(aspect, res) {
  if (aspect === "1:1" && res === "4K") return "2K";
  if (aspect === "auto" && res !== "1K") return "1K";
  return res;
}

// Сколько огней спишет нода данного класса. Для генерации цена зависит от
// resolution с учётом aspect_ratio (оба виджета есть и на ноде, и на сабграфе).
function flamesForClass(node, className) {
  if (GEN_NODES.has(className)) {
    const res = node.widgets?.find((wd) => wd.name === "resolution")?.value || "1K";
    const aspect = node.widgets?.find((wd) => wd.name === "aspect_ratio")?.value || "auto";
    const eff = normalizeRes(aspect, res);
    return FLAMES_BY_RES[eff] || FLAMES_BY_RES["1K"];
  }
  if (FLAMES_FIXED[className] != null) return FLAMES_FIXED[className];
  return null;
}

// Рисует лого в заголовке + превью «≈ N 🔥». Работает и для нашей ноды,
// и для ноды-сабграфа (className передаём явно). rightPad резервирует место
// справа под значок «войти в сабграф», чтобы лого на него не налезало.
function drawBadge(node, ctx, className, rightPad = 0) {
  const titleH = (window.LiteGraph && window.LiteGraph.NODE_TITLE_HEIGHT) || 20;
  const w = node.size[0] - rightPad;

  let logoLeft = w - 8;
  if (logoReady) {
    const s = 14;
    logoLeft = w - s - 8;
    ctx.drawImage(logo, logoLeft, -titleH + (titleH - s) / 2, s, s);
  }

  const flames = flamesForClass(node, className);
  if (flames != null) {
    ctx.save();
    ctx.fillStyle = ACCENT;
    ctx.font = "12px sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.fillText(`≈ ${flames} 🔥`, logoLeft - 6, -titleH / 2);
    ctx.restore();
  }
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

// Найти внутренние ноды свёрнутого сабграфа (API субграфов новый и ещё меняется,
// поэтому пробуем несколько мест и всё в try/catch).
function innerNodes(node) {
  const sg = node.subgraph || node._subgraph;
  if (!sg) return null;
  return sg.nodes || sg._nodes || (sg.graph && sg.graph.nodes) || null;
}

// Если нода — сабграф с нашими нодами внутри, вернуть класс для расчёта цены.
// Приоритет генерационным нодам (у них цена зависит от resolution).
function hotcutSubgraphClass(node) {
  try {
    const nodes = innerNodes(node);
    if (!nodes) return null;
    let fallback = null;
    for (const n of nodes) {
      const t = n.type || n.comfyClass;
      if (HOTCUT_NODES.has(t)) {
        if (GEN_NODES.has(t)) return t;
        fallback = t;
      }
    }
    return fallback;
  } catch (e) {
    return null;
  }
}

// Повесить фирменный вид + превью цены на ноду-сабграф (per-instance, т.к. её
// тип — это UUID сабграфа, а не наш класс — общий хук на прототип не цепляется).
function attachSubgraphPreview(node, innerClass) {
  if (node.__hotcutPreview) return;
  node.__hotcutPreview = true;
  applyStyle(node);
  const prev = node.onDrawForeground;
  node.onDrawForeground = function (ctx) {
    prev?.apply(this, arguments);
    if (this.flags?.collapsed) return;
    // Резерв справа под значок входа в сабграф (≈ высота заголовка).
    const titleH = (window.LiteGraph && window.LiteGraph.NODE_TITLE_HEIGHT) || 20;
    drawBadge(this, ctx, innerClass, titleH + 4);
  };
  node.setDirtyCanvas?.(true, true);
}

function setup(node) {
  if (!node) return;
  if (HOTCUT_NODES.has(node.comfyClass)) {
    applyStyle(node);
    if (node.comfyClass === "HotcutConfig") setupBalanceButton(node);
    return;
  }
  // Не наша нода напрямую — возможно, это сабграф с нашими нодами внутри.
  const innerClass = hotcutSubgraphClass(node);
  if (innerClass) attachSubgraphPreview(node, innerClass);
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
      drawBadge(this, ctx, className);
    };
  },
});
