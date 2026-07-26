import type { MarketMatch } from "@/api/market";

type MapPoint = {
  id: string;
  nom: string;
  lat: number;
  lon: number;
  prix: number;
  securite: string;
  recommended: boolean;
};

export function buildMarketMapHtml(opts: {
  homeLat: number;
  homeLon: number;
  homeLabel: string;
  matches: MarketMatch[];
  recommendedId: string | null;
}): string {
  const points: MapPoint[] = opts.matches.map((m) => ({
    id: m.point_de_vente.id,
    nom: m.point_de_vente.nom,
    lat: m.point_de_vente.latitude,
    lon: m.point_de_vente.longitude,
    prix: m.prix,
    securite: m.itineraire?.niveau_securite ?? "inconnu",
    recommended: m.point_de_vente.id === opts.recommendedId,
  }));

  const payload = JSON.stringify({
    home: {
      lat: opts.homeLat,
      lon: opts.homeLon,
      label: opts.homeLabel,
    },
    points,
    focusedId: opts.recommendedId ?? points[0]?.id ?? null,
  });

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    html, body, #map { height: 100%; margin: 0; background: #e8f0ea; }
    .leaflet-control-attribution { font-size: 9px; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    const data = ${payload};
    const map = L.map('map', { zoomControl: false, attributionControl: true }).setView([data.home.lat, data.home.lon], 13);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 19
    }).addTo(map);

    function colorFor(sec) {
      if (sec === 'sur') return '#2F6B45';
      if (sec === 'prudence') return '#C45C26';
      if (sec === 'a_eviter') return '#A33B2B';
      return '#5E6A62';
    }

    const homeMarker = L.circleMarker([data.home.lat, data.home.lon], {
      radius: 11,
      color: '#fff',
      weight: 2,
      fillColor: '#1F3D2B',
      fillOpacity: 1
    }).addTo(map).bindPopup(${JSON.stringify(opts.homeLabel)});

    let route = null;
    let focusedId = data.focusedId;
    let hidden = {};
    const markersById = {};

    function post(msg) {
      if (window.ReactNativeWebView) {
        window.ReactNativeWebView.postMessage(JSON.stringify(msg));
      }
    }

    function drawRoute(point) {
      if (route) { map.removeLayer(route); route = null; }
      if (!point) return;
      route = L.polyline([[data.home.lat, data.home.lon], [point.lat, point.lon]], {
        color: colorFor(point.securite),
        weight: 4,
        opacity: 0.8,
        dashArray: '8 8'
      }).addTo(map);
    }

    function restyleMarkers() {
      data.points.forEach(function (p) {
        const marker = markersById[p.id];
        if (!marker) return;
        const focused = p.id === focusedId;
        marker.setStyle({
          radius: focused ? 15 : (p.recommended ? 12 : 9),
          weight: focused ? 3 : 2,
          color: focused ? '#1F3D2B' : '#fff'
        });
      });
    }

    window.focusPoint = function (id) {
      const point = data.points.find(function (p) { return p.id === id; });
      if (!point) return;
      focusedId = id;
      drawRoute(point);
      restyleMarkers();
      map.panTo([point.lat, point.lon]);
    };

    window.recenterHome = function () {
      const bounds = [[data.home.lat, data.home.lon]];
      data.points.forEach(function (p) { if (!hidden[p.securite]) bounds.push([p.lat, p.lon]); });
      map.fitBounds(bounds, { padding: [40, 60] });
    };

    window.setHiddenSecurities = function (list) {
      hidden = {};
      (list || []).forEach(function (s) { hidden[s] = true; });
      data.points.forEach(function (p) {
        const marker = markersById[p.id];
        if (!marker) return;
        if (hidden[p.securite]) {
          if (map.hasLayer(marker)) map.removeLayer(marker);
        } else if (!map.hasLayer(marker)) {
          marker.addTo(map);
        }
      });
    };

    const bounds = [[data.home.lat, data.home.lon]];
    data.points.forEach(function (p) {
      const c = colorFor(p.securite);
      const marker = L.circleMarker([p.lat, p.lon], {
        radius: p.recommended ? 12 : 9,
        color: '#fff',
        weight: 2,
        fillColor: c,
        fillOpacity: 0.95
      }).addTo(map);
      const html = '<b>' + p.nom + '</b><br/>' + Math.round(p.prix) + ' Ar<br/>' + p.securite
        + (p.recommended ? '<br/><b>Recommande (plus safe)</b>' : '');
      marker.bindPopup(html);
      marker.on('click', function () {
        post({ type: 'select', id: p.id });
        window.focusPoint(p.id);
      });
      markersById[p.id] = marker;
      bounds.push([p.lat, p.lon]);
    });

    if (data.focusedId) {
      window.focusPoint(data.focusedId);
    }
    if (bounds.length > 1) map.fitBounds(bounds, { padding: [40, 60] });
  </script>
</body>
</html>`;
}
