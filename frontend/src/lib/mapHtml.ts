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
  rayonKm: number;
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
    rayonM: Math.max(1, opts.rayonKm) * 1000,
    rayonKm: opts.rayonKm,
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

    const zoneCircle = L.circle([data.home.lat, data.home.lon], {
      radius: data.rayonM,
      color: '#1F3D2B',
      weight: 1.5,
      opacity: 0.45,
      fillColor: '#1F3D2B',
      fillOpacity: 0.06,
      dashArray: '6 8'
    }).addTo(map);

    const zoneLabel = L.marker([data.home.lat, data.home.lon], {
      icon: L.divIcon({
        className: 'zone-label',
        html: '<div style="background:#FFFCF7;border:1px solid #D8D2C4;border-radius:999px;padding:3px 10px;font-size:11px;font-weight:700;color:#5E6A62;white-space:nowrap;transform:translate(-50%,-34px);box-shadow:0 2px 6px rgba(0,0,0,0.12);">Zone de recherche : ' + data.rayonKm + ' km</div>',
        iconSize: [0, 0]
      }),
      interactive: false
    }).addTo(map);

    const homeMarker = L.circleMarker([data.home.lat, data.home.lon], {
      radius: 11,
      color: '#fff',
      weight: 2,
      fillColor: '#1F3D2B',
      fillOpacity: 1
    }).addTo(map).bindPopup(${JSON.stringify(opts.homeLabel)});

    let route = null;
    let routeRequestId = 0;
    let focusedId = data.focusedId;
    let hidden = {};
    const markersById = {};

    function post(msg) {
      if (window.ReactNativeWebView) {
        window.ReactNativeWebView.postMessage(JSON.stringify(msg));
      }
    }

    // Ligne droite affichée immédiatement (repère visuel + secours hors-ligne),
    // remplacée par le vrai trajet routier dès que le service de routage répond.
    function drawStraightFallback(point) {
      if (route) { map.removeLayer(route); }
      route = L.polyline([[data.home.lat, data.home.lon], [point.lat, point.lon]], {
        color: colorFor(point.securite),
        weight: 3,
        opacity: 0.5,
        dashArray: '2 10'
      }).addTo(map);
    }

    function drawRoadRoute(point, lonLatCoords) {
      if (route) { map.removeLayer(route); }
      const latlngs = lonLatCoords.map(function (c) { return [c[1], c[0]]; });
      route = L.polyline(latlngs, {
        color: colorFor(point.securite),
        weight: 5,
        opacity: 0.85
      }).addTo(map);
    }

    // OSRM (démo publique, sans clé) : calcule un vrai trajet suivant les routes
    // au lieu d'une ligne droite. Si indisponible (hors-ligne, quota), on garde le
    // trait pointillé déjà affiché — l'app reste utilisable sans connexion au service.
    function fetchRoadRoute(point) {
      const myRequest = ++routeRequestId;
      const url = 'https://router.project-osrm.org/route/v1/driving/'
        + data.home.lon + ',' + data.home.lat + ';' + point.lon + ',' + point.lat
        + '?overview=full&geometries=geojson';
      fetch(url)
        .then(function (res) { return res.json(); })
        .then(function (json) {
          if (myRequest !== routeRequestId) return;
          const r = json && json.routes && json.routes[0];
          const coords = r && r.geometry && r.geometry.coordinates;
          if (coords && coords.length > 1) {
            drawRoadRoute(point, coords);
            post({ type: 'route', id: point.id, distanceM: r.distance, durationS: r.duration });
          }
        })
        .catch(function () { /* on garde la ligne droite en secours */ });
    }

    function drawRoute(point) {
      if (!point) {
        if (route) { map.removeLayer(route); route = null; }
        return;
      }
      drawStraightFallback(point);
      fetchRoadRoute(point);
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
      map.fitBounds(zoneCircle.getBounds(), { padding: [30, 30] });
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
    const initialBounds = L.latLngBounds(bounds).extend(zoneCircle.getBounds());
    map.fitBounds(initialBounds, { padding: [30, 40] });
  </script>
</body>
</html>`;
}
