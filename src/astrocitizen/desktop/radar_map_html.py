"""HTML Leaflet + RainViewer centrado no observatorio (uso pessoal/educacional)."""

from __future__ import annotations

import html
import json
from pathlib import Path


def build_radar_map_html(
    *,
    latitude_deg: float,
    longitude_deg: float,
    zoom: int = 6,
    site_name: str = "",
) -> str:
    """Gera pagina autocontida (CDN Leaflet + tiles RainViewer animados)."""
    lat = float(latitude_deg)
    lon = float(longitude_deg)
    z = max(1, min(int(zoom), 12))
    label = (site_name or "Observatorio").strip() or "Observatorio"
    lat_js = json.dumps(lat)
    lon_js = json.dumps(lon)
    zoom_js = json.dumps(z)
    label_js = json.dumps(label)
    label_html = html.escape(label)
    return f"""<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Radar — {label_html}</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    html, body {{ margin: 0; height: 100%; background: #0b1220; color: #e8eef8;
      font-family: system-ui, sans-serif; }}
    .bar {{
      position: absolute; top: 0; left: 0; right: 0; height: 44px; z-index: 1000;
      display: flex; align-items: center; justify-content: space-between;
      gap: 8px; padding: 0 10px; box-sizing: border-box;
      background: rgba(11, 18, 32, 0.92); border-bottom: 1px solid #243049;
    }}
    .bar .title {{ font-size: 13px; opacity: 0.9; white-space: nowrap;
      overflow: hidden; text-overflow: ellipsis; }}
    #timestamp {{ font-weight: 600; font-size: 14px; min-width: 4.5em; text-align: center; }}
    .buttons {{ display: flex; gap: 6px; }}
    .buttons button {{
      width: 34px; height: 30px; border: 1px solid #3a4a66; border-radius: 4px;
      background: #162033; color: #e8eef8; cursor: pointer;
    }}
    .buttons button:hover {{ background: #1e2c45; }}
    #map {{ position: absolute; top: 44px; left: 0; right: 0; bottom: 0; }}
    .leaflet-control-attribution {{ font-size: 10px; }}
  </style>
</head>
<body>
  <div class="bar">
    <div class="title">{label_html}</div>
    <div id="timestamp">…</div>
    <div class="buttons">
      <button type="button" id="prevBtn" title="Anterior">‹</button>
      <button type="button" id="playBtn" title="Play/Pause">▶</button>
      <button type="button" id="nextBtn" title="Seguinte">›</button>
    </div>
  </div>
  <div id="map"></div>
  <script>
(function () {{
  var TILE_SIZE = window.devicePixelRatio >= 2 ? 512 : 256;
  var RADAR_OPACITY = 0.75;
  var ANIMATION_DELAY_MS = 500;
  var API_URL = "https://api.rainviewer.com/public/weather-maps.json";
  var CENTER_LAT = {lat_js};
  var CENTER_LON = {lon_js};
  var START_ZOOM = {zoom_js};
  var SITE_LABEL = {label_js};

  var apiData = {{}};
  var mapFrames = [];
  var animationPosition = 0;
  var animationTimer = false;
  var currentLayer = null;
  var isLoading = false;
  var layerCache = {{}};

  var map = L.map("map", {{ maxZoom: 12 }}).setView([CENTER_LAT, CENTER_LON], START_ZOOM);
  L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
    attribution: "&copy; OpenStreetMap"
  }}).addTo(map);
  L.marker([CENTER_LAT, CENTER_LON]).addTo(map).bindPopup(SITE_LABEL);

  function wrapPosition(position) {{
    if (!mapFrames.length) return 0;
    while (position >= mapFrames.length) position -= mapFrames.length;
    while (position < 0) position += mapFrames.length;
    return position;
  }}
  function formatTime(timestamp) {{
    return new Date(timestamp * 1000).toLocaleTimeString([], {{
      hour: "2-digit", minute: "2-digit"
    }});
  }}
  function createRadarLayer(frame) {{
    return new L.TileLayer(
      apiData.host + frame.path + "/" + TILE_SIZE + "/{{z}}/{{x}}/{{y}}/2/1_1.png",
      {{ tileSize: 256, opacity: 0.001, maxNativeZoom: 7, maxZoom: 12 }}
    );
  }}
  function clearLayerCache() {{
    stop();
    for (var pos in layerCache) {{
      if (parseInt(pos, 10) !== animationPosition) {{
        map.removeLayer(layerCache[pos]);
        delete layerCache[pos];
      }}
    }}
  }}
  function stop() {{
    if (animationTimer) {{
      clearTimeout(animationTimer);
      animationTimer = false;
      document.getElementById("playBtn").innerHTML = "▶";
      return true;
    }}
    return false;
  }}
  function play() {{
    animationTimer = true;
    document.getElementById("playBtn").innerHTML = "⏸";
    showFrame(animationPosition + 1);
  }}
  function playStop() {{
    if (!stop()) play();
  }}
  function showFrame(position) {{
    if (isLoading || !mapFrames.length) return;
    position = wrapPosition(position);
    var frame = mapFrames[position];
    document.getElementById("timestamp").innerHTML = formatTime(frame.time);
    var oldLayer = currentLayer;
    if (layerCache[position]) {{
      if (oldLayer) oldLayer.setOpacity(0);
      layerCache[position].setOpacity(RADAR_OPACITY);
      currentLayer = layerCache[position];
      animationPosition = position;
      if (animationTimer) animationTimer = setTimeout(play, ANIMATION_DELAY_MS);
      return;
    }}
    isLoading = true;
    var newLayer = createRadarLayer(frame);
    newLayer.on("load", function () {{
      newLayer.setOpacity(RADAR_OPACITY);
      if (oldLayer) oldLayer.setOpacity(0);
      layerCache[position] = newLayer;
      currentLayer = newLayer;
      animationPosition = position;
      isLoading = false;
      if (animationTimer) animationTimer = setTimeout(play, ANIMATION_DELAY_MS);
    }});
    newLayer.addTo(map);
  }}
  function initialize(api) {{
    clearLayerCache();
    currentLayer = null;
    mapFrames = [];
    animationPosition = 0;
    if (!api || !api.radar || !api.radar.past) {{
      document.getElementById("timestamp").innerHTML = "sem dados";
      return;
    }}
    mapFrames = api.radar.past;
    showFrame(mapFrames.length - 1);
  }}
  function loadApiData() {{
    var req = new XMLHttpRequest();
    req.open("GET", API_URL, true);
    req.onload = function () {{
      try {{
        apiData = JSON.parse(req.response);
        initialize(apiData);
      }} catch (e) {{
        document.getElementById("timestamp").innerHTML = "erro API";
      }}
    }};
    req.onerror = function () {{
      document.getElementById("timestamp").innerHTML = "offline";
    }};
    req.send();
  }}
  document.getElementById("prevBtn").onclick = function () {{
    stop(); showFrame(animationPosition - 1);
  }};
  document.getElementById("playBtn").onclick = playStop;
  document.getElementById("nextBtn").onclick = function () {{
    stop(); showFrame(animationPosition + 1);
  }};
  map.on("movestart", clearLayerCache);
  loadApiData();
}})();
  </script>
</body>
</html>
"""


def write_radar_map_html(
    path: Path,
    *,
    latitude_deg: float,
    longitude_deg: float,
    zoom: int = 6,
    site_name: str = "",
) -> Path:
    """Grava HTML e devolve o path absoluto."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        build_radar_map_html(
            latitude_deg=latitude_deg,
            longitude_deg=longitude_deg,
            zoom=zoom,
            site_name=site_name,
        ),
        encoding="utf-8",
    )
    return dest.resolve()
