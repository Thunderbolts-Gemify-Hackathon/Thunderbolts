import type { MarketMatch } from "@/api/market";

export type MapPoint = {
  id: string;
  nom: string;
  lat: number;
  lon: number;
  prix: number;
  securite: string;
  recommended: boolean;
};

export function matchesToMapPoints(
  matches: MarketMatch[],
  recommendedId: string | null
): MapPoint[] {
  return matches.map((m) => ({
    id: m.point_de_vente.id,
    nom: m.point_de_vente.nom,
    lat: m.point_de_vente.latitude,
    lon: m.point_de_vente.longitude,
    prix: m.prix,
    securite: m.itineraire?.niveau_securite ?? "inconnu",
    recommended: m.point_de_vente.id === recommendedId,
  }));
}

/**
 * HTML de base : chargé une seule fois (Leaflet + tuiles).
 * Les points / rayon / focus sont mis à jour via injectJavaScript —
 * évite de tout recharger à chaque recherche (cause principale du
 * « la carte a du mal à s'afficher »).
 */
export function buildMarketMapShellHtml(opts: {
  homeLat: number;
  homeLon: number;
  homeLabel: string;
  rayonKm: number;
}): string {
  const boot = JSON.stringify({
    home: {
      lat: opts.homeLat,
      lon: opts.homeLon,
      label: opts.homeLabel,
    },
    rayonKm: opts.rayonKm,
    rayonM: Math.max(1, opts.rayonKm) * 1000,
  });

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    html, body, #map { height: 100%; margin: 0; background: #e8f0ea; }
    .leaflet-control-attribution { font-size: 9px; max-width: 55%; }
    .leaflet-tile-pane { opacity: 1; }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    const boot = ${boot};
    const map = L.map('map', {
      zoomControl: false,
      attributionControl: true,
      preferCanvas: true
    }).setView([boot.home.lat, boot.home.lon], 13);

    // Tuiles légères + moins de requêtes pendant le zoom/pan
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OSM &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 18,
      keepBuffer: 1,
      updateWhenIdle: true,
      updateWhenZooming: false
    }).addTo(map);

    function colorFor(sec) {
      if (sec === 'sur') return '#2F6B45';
      if (sec === 'prudence') return '#C45C26';
      if (sec === 'a_eviter') return '#A33B2B';
      return '#5E6A62';
    }

    function post(msg) {
      if (window.ReactNativeWebView) {
        window.ReactNativeWebView.postMessage(JSON.stringify(msg));
      }
    }

    let zoneCircle = L.circle([boot.home.lat, boot.home.lon], {
      radius: boot.rayonM,
      color: '#1F3D2B',
      weight: 1.5,
      opacity: 0.45,
      fillColor: '#1F3D2B',
      fillOpacity: 0.06,
      dashArray: '6 8'
    }).addTo(map);

    const homeMarker = L.circleMarker([boot.home.lat, boot.home.lon], {
      radius: 11,
      color: '#fff',
      weight: 2,
      fillColor: '#1F3D2B',
      fillOpacity: 1
    }).addTo(map).bindPopup(${JSON.stringify(opts.homeLabel)});

    let points = [];
    let focusedId = null;
    let hidden = {};
    const markersById = {};
    let route = null;
    let routeRequestId = 0;
    let mapReadyPosted = false;

    function clearMarkers() {
      Object.keys(markersById).forEach(function (id) {
        map.removeLayer(markersById[id]);
        delete markersById[id];
      });
    }

    function drawStraightFallback(point) {
      if (route) map.removeLayer(route);
      route = L.polyline(
        [[boot.home.lat, boot.home.lon], [point.lat, point.lon]],
        { color: colorFor(point.securite), weight: 3, opacity: 0.5, dashArray: '2 10' }
      ).addTo(map);
    }

    function drawRoadRoute(point, lonLatCoords) {
      if (route) map.removeLayer(route);
      const latlngs = lonLatCoords.map(function (c) { return [c[1], c[0]]; });
      route = L.polyline(latlngs, {
        color: colorFor(point.securite),
        weight: 5,
        opacity: 0.85
      }).addTo(map);
    }

    let routeTimer = null;

    function fetchRoadRoute(point) {
      // Debounce : évite de spammer OSRM quand on swipe vite le carousel,
      // tout en restaurant le vrai trajet routier (pas une ligne à vol d'oiseau).
      if (routeTimer) clearTimeout(routeTimer);
      routeTimer = setTimeout(function () {
        const myRequest = ++routeRequestId;
        const url = 'https://router.project-osrm.org/route/v1/driving/'
          + boot.home.lon + ',' + boot.home.lat + ';' + point.lon + ',' + point.lat
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
          .catch(function () { /* garde la ligne pointillée en secours */ });
      }, 280);
    }

    function restyleMarkers() {
      points.forEach(function (p) {
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

    function fitAll() {
      const bounds = [[boot.home.lat, boot.home.lon]];
      points.forEach(function (p) {
        if (!hidden[p.securite]) bounds.push([p.lat, p.lon]);
      });
      const latLngBounds = L.latLngBounds(bounds).extend(zoneCircle.getBounds());
      map.fitBounds(latLngBounds, { padding: [30, 40], maxZoom: 15 });
    }

    window.setPoints = function (nextPoints, focusId) {
      points = nextPoints || [];
      clearMarkers();
      if (route) { map.removeLayer(route); route = null; }
      focusedId = focusId || (points[0] && points[0].id) || null;

      points.forEach(function (p) {
        const marker = L.circleMarker([p.lat, p.lon], {
          radius: p.recommended ? 12 : 9,
          color: '#fff',
          weight: 2,
          fillColor: colorFor(p.securite),
          fillOpacity: 0.95
        });
        marker.bindPopup(
          '<b>' + p.nom + '</b><br/>' + Math.round(p.prix) + ' Ar<br/>' + p.securite
          + (p.recommended ? '<br/><b>Recommande</b>' : '')
        );
        marker.on('click', function () {
          post({ type: 'select', id: p.id });
          window.focusPoint(p.id);
        });
        markersById[p.id] = marker;
        if (!hidden[p.securite]) marker.addTo(map);
      });

      restyleMarkers();
      fitAll();
      if (focusedId) {
        const point = points.find(function (p) { return p.id === focusedId; });
        if (point) {
          drawStraightFallback(point); // immédiat
          fetchRoadRoute(point);       // puis vrai trajet OSRM
        }
      }
    };

    window.setRayon = function (km) {
      const rayonM = Math.max(1, Number(km) || 15) * 1000;
      map.removeLayer(zoneCircle);
      zoneCircle = L.circle([boot.home.lat, boot.home.lon], {
        radius: rayonM,
        color: '#1F3D2B',
        weight: 1.5,
        opacity: 0.45,
        fillColor: '#1F3D2B',
        fillOpacity: 0.06,
        dashArray: '6 8'
      }).addTo(map);
      fitAll();
    };

    window.focusPoint = function (id) {
      const point = points.find(function (p) { return p.id === id; });
      if (!point) return;
      focusedId = id;
      restyleMarkers();
      map.panTo([point.lat, point.lon], { animate: true, duration: 0.25 });
      // Ligne pointillée tout de suite, remplacée par le trajet routier OSRM
      drawStraightFallback(point);
      fetchRoadRoute(point);
    };

    window.recenterHome = function () {
      map.fitBounds(zoneCircle.getBounds(), { padding: [30, 30], maxZoom: 15 });
    };

    /**
     * Mode sortie multi-arrêts : markers numérotés + trajet OSRM home→stop1→stop2…
     * stops: [{ id, nom, lat, lon, order, label? }]
     */
    window.setTripStops = function (stops) {
      const list = stops || [];
      clearMarkers();
      if (route) { map.removeLayer(route); route = null; }
      points = list.map(function (s) {
        return {
          id: s.id,
          nom: s.nom,
          lat: s.lat,
          lon: s.lon,
          prix: 0,
          securite: 'sur',
          recommended: s.order === 1,
          order: s.order,
          label: s.label || ''
        };
      });
      focusedId = points[0] && points[0].id || null;

      points.forEach(function (p) {
        const marker = L.circleMarker([p.lat, p.lon], {
          radius: 14,
          color: '#1F3D2B',
          weight: 3,
          fillColor: '#C45C26',
          fillOpacity: 0.95
        });
        marker.bindPopup(
          '<b>#' + (p.order || '') + ' ' + p.nom + '</b>'
          + (p.label ? '<br/>' + p.label : '')
        );
        marker.on('click', function () {
          post({ type: 'select', id: p.id });
          focusedId = p.id;
          restyleMarkers();
        });
        markersById[p.id] = marker;
        marker.addTo(map);
      });

      const bounds = [[boot.home.lat, boot.home.lon]];
      points.forEach(function (p) { bounds.push([p.lat, p.lon]); });
      if (bounds.length > 1) {
        map.fitBounds(L.latLngBounds(bounds), { padding: [40, 50], maxZoom: 14 });
      }

      // Ligne immédiate (droite), puis OSRM multi-waypoints
      const straight = [[boot.home.lat, boot.home.lon]].concat(
        points.map(function (p) { return [p.lat, p.lon]; })
      );
      route = L.polyline(straight, {
        color: '#C45C26', weight: 3, opacity: 0.45, dashArray: '4 8'
      }).addTo(map);

      if (!points.length) return;
      const myRequest = ++routeRequestId;
      const coordsPath = [boot.home.lon + ',' + boot.home.lat]
        .concat(points.map(function (p) { return p.lon + ',' + p.lat; }))
        .join(';');
      const url = 'https://router.project-osrm.org/route/v1/driving/'
        + coordsPath + '?overview=full&geometries=geojson';
      fetch(url)
        .then(function (res) { return res.json(); })
        .then(function (json) {
          if (myRequest !== routeRequestId) return;
          const r = json && json.routes && json.routes[0];
          const coords = r && r.geometry && r.geometry.coordinates;
          if (coords && coords.length > 1) {
            if (route) map.removeLayer(route);
            const latlngs = coords.map(function (c) { return [c[1], c[0]]; });
            route = L.polyline(latlngs, {
              color: '#C45C26', weight: 5, opacity: 0.9
            }).addTo(map);
            post({
              type: 'route',
              id: 'trip',
              distanceM: r.distance,
              durationS: r.duration
            });
          }
        })
        .catch(function () { /* garde la ligne pointillée */ });
    };

    window.setHiddenSecurities = function (list) {
      hidden = {};
      (list || []).forEach(function (s) { hidden[s] = true; });
      points.forEach(function (p) {
        const marker = markersById[p.id];
        if (!marker) return;
        if (hidden[p.securite]) {
          if (map.hasLayer(marker)) map.removeLayer(marker);
        } else if (!map.hasLayer(marker)) {
          marker.addTo(map);
        }
      });
    };

    map.whenReady(function () {
      if (!mapReadyPosted) {
        mapReadyPosted = true;
        post({ type: 'ready' });
      }
      map.fitBounds(zoneCircle.getBounds(), { padding: [30, 30], maxZoom: 15 });
    });
  </script>
</body>
</html>`;
}

/** @deprecated Utiliser buildMarketMapShellHtml + setPoints — gardé si un import traîne. */
export function buildMarketMapHtml(opts: {
  homeLat: number;
  homeLon: number;
  homeLabel: string;
  matches: MarketMatch[];
  recommendedId: string | null;
  rayonKm: number;
}): string {
  return buildMarketMapShellHtml({
    homeLat: opts.homeLat,
    homeLon: opts.homeLon,
    homeLabel: opts.homeLabel,
    rayonKm: opts.rayonKm,
  });
}
