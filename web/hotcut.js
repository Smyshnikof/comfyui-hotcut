// Лёгкий фирменный пасс для нод HOTCUT: тёмная нода + оранжевый акцент (#ff6b35),
// лого в заголовке и превью стоимости в огнях. Без рескина чрома ComfyUI —
// только стабильные хуки registerExtension, чтобы не ломаться на апдейтах.
import { app } from "../../scripts/app.js";

const ACCENT = "#ff6b35"; // бренд HOTCUT (огонь)
const TITLE_BG = "#1a1412"; // тёмный тёплый заголовок
const BODY_BG = "#0e0e10"; // near-black тело

const HOTCUT_NODES = new Set(["HotcutConfig", "HotcutGptImage2", "HotcutGptImage2Edit"]);
const GEN_NODES = new Set(["HotcutGptImage2", "HotcutGptImage2Edit"]);

// Огни по resolution — синхронно с lib/economics.ts (GPT_IMAGE_2)
const FLAMES_BY_RES = { "1K": 39, "2K": 65, "4K": 103 };

// Предзагрузка лого (лежит рядом с этим файлом в web/)
const logo = new Image();
logo.src = new URL("./hotcut_logo.png", import.meta.url).href;
let logoReady = false;
logo.onload = () => {
  logoReady = true;
};

app.registerExtension({
  name: "HOTCUT.branding",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    const className = nodeData?.name;
    if (!HOTCUT_NODES.has(className)) return;

    // 1. Фирменные цвета
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
      this.color = TITLE_BG;
      this.bgcolor = BODY_BG;
      return r;
    };

    // 2. Лого в заголовке + превью стоимости в огнях
    const onDrawForeground = nodeType.prototype.onDrawForeground;
    nodeType.prototype.onDrawForeground = function (ctx) {
      onDrawForeground?.apply(this, arguments);
      if (this.flags?.collapsed) return;

      const titleH = (window.LiteGraph && window.LiteGraph.NODE_TITLE_HEIGHT) || 20;
      const w = this.size[0];

      // Лого в правом верхнем углу заголовка
      let logoLeft = w - 8;
      if (logoReady) {
        const s = 14;
        logoLeft = w - s - 8;
        ctx.drawImage(logo, logoLeft, -titleH + (titleH - s) / 2, s, s);
      }

      // «≈ N 🔥» для генерационных нод — слева от лого
      if (GEN_NODES.has(className)) {
        const resW = this.widgets?.find((wd) => wd.name === "resolution");
        const res = (resW && resW.value) || "1K";
        const flames = FLAMES_BY_RES[res] || FLAMES_BY_RES["1K"];
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
