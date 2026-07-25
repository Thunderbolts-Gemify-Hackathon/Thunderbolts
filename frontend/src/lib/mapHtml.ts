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
    .legend {
      position: absolute; z-index: 1000; left: 10px; bottom: 14px;
      background: rgba(255,252,247,0.95); padding: 8px 10px; border-radius: 10px;
      font: 12px/1.35 system-ui, sans-serif; color: #1A1F1C;
      box-shadow: 0 2px 10px rgba(0,0,0,0.12);
    }
    .dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; }
  </style>
</head>
<body>
  <div id="map"></div>
  <div class="legend">
    <div><span class="dot" style="background:#2F6B45"></span>Trajet sur</div>
    <div><span class="dot" style="background:#C45C26"></span>Prudence</div>
    <div><span class="dot" style="background:#A33B2B"></span>A eviter</div>
    <div><span class="dot" style="background:#1F3D2B"></span>Chez toi</div>
  </div>
  <script>
    const data = ${payload};
    const map = L.map('map', { zoomControl: true }).setView([data.home.lat, data.home.lon], 13);
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

    L.circleMarker([data.home.lat, data.home.lon], {
      radius: 11,
      color: '#fff',
      weight: 2,
      fillColor: '#1F3D2B',
      fillOpacity: 1
    }).addTo(map).bindPopup(${JSON.stringify(opts.homeLabel)});

    const bounds = [[data.home.lat, data.home.lon]];
    data.points.forEach(function (p) {
      const c = colorFor(p.securite);
      const marker = L.circleMarker([p.lat, p.lon], {
        radius: p.recommended ? 14 : 10,
        color: p.recommended ? '#1F3D2B' : '#fff',
        weight: p.recommended ? 3 : 2,
        fillColor: c,
        fillOpacity: 0.95
      }).addTo(map);
      const html = '<b>' + p.nom + '</b><br/>' + Math.round(p.prix) + ' Ar<br/>' + p.securite
        + (p.recommended ? '<br/><b>Recommande (plus safe)</b>' : '');
      marker.bindPopup(html);
      marker.on('click', function () {
        if (window.ReactNativeWebView) {
          window.ReactNativeWebView.postMessage(JSON.stringify({ type: 'select', id: p.id }));
        }
      });
      bounds.push([p.lat, p.lon]);
      if (p.recommended) {
        L.polyline([[data.home.lat, data.home.lon], [p.lat, p.lon]], {
          color: '#1F3D2B',
          weight: 4,
          opacity: 0.75,
          dashArray: '8 8'
        }).addTo(map);
      }
    });
    if (bounds.length > 1) map.fitBounds(bounds, { padding: [36, 36] });
  </script>
</body>
</html>`;
}
