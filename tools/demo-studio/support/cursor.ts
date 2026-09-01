/** Visible pointer for Playwright video (the real mouse is not drawn). */
export const cursorInitScript = `(() => {
  if (window.__demoStudioCursor) return;
  window.__demoStudioCursor = true;
  const el = document.createElement("div");
  el.id = "demo-studio-cursor";
  el.setAttribute("aria-hidden", "true");
  el.style.cssText = [
    "position:fixed",
    "left:0",
    "top:0",
    "width:18px",
    "height:18px",
    "margin:0",
    "border-radius:50%",
    "border:2px solid #67e8f9",
    "background:rgba(56,189,248,0.35)",
    "box-shadow:0 0 12px rgba(34,211,238,0.45)",
    "pointer-events:none",
    "z-index:2147483647",
    "transform:translate(-50%,-50%)",
    "transition:width 80ms, height 80ms",
  ].join(";");
  const mount = () => {
    if (!document.documentElement.contains(el)) {
      document.documentElement.appendChild(el);
    }
  };
  mount();
  window.addEventListener("mousemove", (e) => {
    mount();
    el.style.left = e.clientX + "px";
    el.style.top = e.clientY + "px";
  });
  window.addEventListener("mousedown", () => {
    el.style.width = "12px";
    el.style.height = "12px";
  });
  window.addEventListener("mouseup", () => {
    el.style.width = "18px";
    el.style.height = "18px";
  });
})();`;
