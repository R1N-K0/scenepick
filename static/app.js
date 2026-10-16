async function setStatus(image_id, status) {
  const r = await fetch("/api/status", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image_id, status }),
  });
  if (!r.ok) throw new Error(`${r.status} ${image_id}`);
  return (await r.json()).status;
}

// "unjudged only" is the shots that were unjudged when it was switched on, kept in the browser
// so the grid and the shot page step through the same ones. Held still while judging, as the
// grid is: a shot judged a moment ago can still be stepped back to and un-clicked.
function readOnly() {
  return localStorage.only ? new Set(JSON.parse(localStorage.only)) : null;
}

function writeOnly(ids) {
  if (ids) localStorage.only = JSON.stringify(ids);
  else delete localStorage.only;
}

function mountHeader(current) {
  const root = document.documentElement;

  // Measured, not written into the stylesheet: the glyph buttons set the header's height, which
  // follows the fonts of the machine (50px in Chrome on Windows), and a narrow window wraps it
  // onto two lines. What sits below the header is placed from --bar.
  const header = document.querySelector("header");
  new ResizeObserver(() => {
    root.style.setProperty("--bar", `${header.getBoundingClientRect().height}px`);
  }).observe(header);

  document.getElementById("theme").onclick = () => {
    root.dataset.theme = localStorage.theme = root.dataset.theme === "light" ? "dark" : "light";
  };

  const open = document.getElementById("menu-open");
  const menu = document.getElementById("menu");
  const list = document.getElementById("menu-list");
  let loaded = false;

  open.onclick = async () => {
    menu.hidden = !menu.hidden;
    if (menu.hidden) return;
    if (!loaded) {
      const images = await (await fetch("/api/images")).json();
      list.innerHTML = images.map(i => `<li>
        <a href="/shot/${i.image_id}" data-status="${i.status}"${i.image_id === current ? ' class="here"' : ""}>
          ${i.image_id}<span>${i.status}</span></a></li>`).join("");
      loaded = true;
    }
    list.querySelector(".here")?.scrollIntoView({ block: "center" });
  };

  addEventListener("keydown", (e) => {
    if (e.code === "Escape") menu.hidden = true;
  });
}
