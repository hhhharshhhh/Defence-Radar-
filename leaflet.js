// Load Leaflet dynamically if not already loaded
if (typeof L === "undefined") {
  const leafletCSS = document.createElement("link");
  leafletCSS.rel = "stylesheet";
  leafletCSS.href = "https://unpkg.com/leaflet/dist/leaflet.css";
  document.head.appendChild(leafletCSS);

  const leafletScript = document.createElement("script");
  leafletScript.src = "https://unpkg.com/leaflet/dist/leaflet.js";
  document.head.appendChild(leafletScript);
}
