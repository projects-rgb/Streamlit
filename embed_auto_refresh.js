// frontend/embed_auto_refresh.js
// Not required — included inline by streamlit_app.py.
// Example usage shown only.

(async function embed(viewUrl, tokenEndpoint, containerId, height) {
  const moduleUrl = "https://prod-in-a.online.tableau.com/javascripts/api/tableau.embedding.3.latest.min.js";
  await import(moduleUrl);

  const container = document.getElementById(containerId);
  container.innerHTML = "";

  const vizEl = document.createElement("tableau-viz");
  vizEl.src = viewUrl;
  vizEl.style.width = "100%";
  vizEl.style.height = height + "px";
  vizEl.token = async () => {
    const r = await fetch(tokenEndpoint, {cache: "no-store"});
    const j = await r.json();
    if (j.error) throw new Error(j.error);
    return j.token;
  };
  container.appendChild(vizEl);
})()
