# Local MapLibre renderer

## Purpose

The renderer turns a declared MapLibre scene into a PNG and a JSON provenance
manifest. It runs MapLibre GL JS in a real headless Chromium WebGL2 context,
controlled by a dependency-light Node CLI. This preserves the DOM, worker,
fetch, CORS, and browser GPU contracts that plain Node and `headless-gl` do not
fully provide.

The renderer is a visualization tool. A convincing perspective view does not
raise the evidence grade of an archaeological candidate. Preserve the source
raster, point cloud, vector data, CRS, processing decisions, and conservative
source visualizations alongside it.

## Current capability and proof boundary

| Capability | Implementation | Current proof |
| --- | --- | --- |
| Local or remote MapLibre style | `maplibre-style` render job | Local style proven |
| GeoJSON and fill extrusion | Native MapLibre layers | Proven in deterministic fixture |
| Custom WebGL layer | Async module adapter | Proven with shared-context fixture |
| Raster-DEM terrain | Native MapLibre `raster-dem` + `terrain` style | Proven with deterministic Terrain RGB fixture |
| OGC/Cesium 3D Tiles | Three.js + `3d-tiles-renderer` custom-layer adapter | Boundary designed; adapter and real tileset not yet bundled or proven |
| Imported screenshot fallback | Explicit import or job fallback | Proven, with distinct manifest status |
| macOS headless WebGL2 | Chromium + SwiftShader on the current host | Proven |
| macOS native GPU | Normal Chromium launch | Environment-blocked on the current host |
| Windows | Chrome/Edge discovery and platform-neutral CDP | Implemented but not run on Windows |

Do not describe the current package as a proven 3D Tiles renderer. It is a
proven MapLibre GL JS renderer for styles, 3D extrusions, and custom WebGL
modules. The official MapLibre 3D Tiles path is a custom layer using Three.js
and NASA AMMOS `3d-tiles-renderer`; that exact adapter still needs a licensed,
local test tileset and a real Windows run.

Primary references:

- [MapLibre GL JS examples](https://maplibre.org/maplibre-gl-js/docs/examples/)
- [MapLibre 3D Tiles example](https://maplibre.org/maplibre-gl-js/docs/examples/add-3d-tiles-using-threejs/)
- [MapLibre custom-layer contract](https://maplibre.org/maplibre-gl-js/docs/API/interfaces/CustomLayerInterface/)
- [MapLibre raster-DEM source](https://maplibre.org/maplibre-style-spec/sources/#raster-dem)
- [NASA AMMOS 3DTilesRendererJS](https://github.com/NASA-AMMOS/3DTilesRendererJS)

## Install

From the renderer directory:

```bash
cd skills/indiana-jones/scripts/map_renderer
npm install
npm run probe
npm test
```

Requirements:

- Node 22 or newer;
- Chrome, Edge, Chromium, or `IJ_BROWSER_PATH` pointing to a compatible
  executable;
- WebGL2 through native GPU acceleration or an explicitly selected software
  implementation.

The default launch keeps the browser sandbox and normal process model enabled.
Restricted CI containers may require:

```bash
IJ_BROWSER_NO_SANDBOX=1 \
IJ_BROWSER_SINGLE_PROCESS=1 \
IJ_BROWSER_SOFTWARE_GL=1 \
npm test
```

These switches reduce browser isolation and force SwiftShader. Use them only
inside an already isolated worker. A SwiftShader result proves WebGL behavior,
not native GPU driver behavior or performance.

## Commands

Validate a job without launching a browser:

```bash
node src/cli.mjs validate --job fixtures/extrusion-job.json
```

Probe the selected browser and WebGL2:

```bash
node src/cli.mjs probe
```

Render a style:

```bash
node src/cli.mjs render \
  --job fixtures/extrusion-job.json \
  --output artifacts/extrusion.png
```

Import a screenshot supplied by another lawful source:

```bash
node src/cli.mjs import-screenshot \
  --job case/render-job.json \
  --input case/manual-reference.png \
  --output case/rendered/manual-reference.png \
  --source-id src_manual_view \
  --kind lead-only \
  --license "Viewer export licence" \
  --access-basis "Supplied by analyst" \
  --accessed-at 2026-07-24T00:00:00Z \
  --reason "Viewer export supplied by the analyst"
```

`import-screenshot` does not claim that MapLibre rendered the image. Its
sidecar uses `status: "screenshot-fallback"` and preserves the original PNG
hash.

## Render-job contract

```json
{
  "schemaVersion": "1.0",
  "mode": "maplibre-style",
  "disclosureClass": "restricted",
  "coordinatePrecision": "region-only",
  "networkPolicy": {
    "mode": "local-only",
    "allowedHosts": []
  },
  "attribution": "Dataset owner · product · licence",
  "style": {
    "path": "style.json"
  },
  "camera": {
    "center": [0, 0],
    "zoom": 15,
    "pitch": 60,
    "bearing": -20
  },
  "viewport": {
    "width": 1280,
    "height": 720,
    "pixelRatio": 1
  },
  "wait": {
    "timeoutMs": 30000,
    "settleMs": 100,
    "failOnMapError": true
  },
  "sources": [
    {
      "sourceId": "src_terrain",
      "kind": "primary-measurement",
      "role": "analysis",
      "locator": "terrain-or-style.json",
      "accessBasis": "public",
      "license": "Dataset-specific licence",
      "crs": "EPSG:3857",
      "accessedAt": "2026-07-24T00:00:00Z",
      "sensor": "product or instrument",
      "acquiredAt": "known date or unknown",
      "resolution": "declared ground sampling distance"
    }
  ],
  "customLayerModules": [
    "local-adapter.mjs"
  ],
  "fallbackScreenshot": "optional-existing-image.png"
}
```

The style must define exactly one transport:

- `style.json`: an inline style object;
- `style.path`: a style file relative to the job;
- `style.url`: an HTTP(S) style.

Local styles, modules, and automatic fallbacks are fenced to the job directory.
Remote styles and modules remain subject to their live availability, CORS,
licence, attribution, and automated-access terms. Prefer local, hash-bound
assets for repeatable evidence.

`coordinatePrecision` is mandatory:

- `exact`: retain the camera center in the manifest;
- `0.1-degree`: round the manifest camera center to a broad area;
- `region-only`: omit the manifest camera center.

This policy only controls the manifest. Labels, geometry, filenames, and the
view itself can still reveal a location, so public output needs a disclosure
review.

`networkPolicy` is also mandatory. `local-only` allows the loopback asset
server plus `data:` and `blob:` URLs. `allowlist` additionally requires one or
more exact remote hostnames:

```json
{
  "mode": "allowlist",
  "allowedHosts": ["tiles.example.org", "models.example.org"]
}
```

Chromium requests are intercepted before navigation. A style, tile loader, or
custom module cannot contact an undeclared hostname; any attempted request
fails the render. Treat local adapter modules as executable code and review
them before adding them to a job.

The manifest hashes the job, local style, local adapter modules, local source
records when their locators resolve to files, and output PNG. It also records
the exact MapLibre version, browser executable, camera, dimensions, WebGL
vendor/renderer, framebuffer hash, countable pixel metrics, network origins,
and SHA-256 hashes for the local runtime/job assets actually served. Remote
responses are not content-hashed; a remote run is not fully reproducible until
those inputs are lawfully cached and registered as local sources.

## Custom-layer readiness contract

A custom module exports:

```javascript
export async function install({map, maplibregl, job}) {
  const layer = createLayer();
  map.addLayer(layer);
  return {
    layerIds: [layer.id],
    ready: waitForExternalTilesToStabilize()
  };
}
```

MapLibre's `idle` event only covers MapLibre-owned sources and transitions.
Three.js or 3D Tiles adapters must return a `ready` promise that waits for the
root tileset, at least one renderable model, and a short stable-frame window.
Do not resolve readiness after downloading only `tileset.json`.

An OGC 3D Tiles adapter should:

1. share MapLibre's WebGL2 context through a `renderingMode: "3d"` custom layer;
2. use the MapLibre camera projection and a documented ECEF-to-Mercator
   transform;
3. configure GLTF, Draco, and KTX2 loaders locally where those extensions are
   permitted and expected;
4. report unsupported tileset extensions and failed model requests;
5. dispose Three.js, loader, and tile resources on removal;
6. use a licensed local fixture for deterministic regression;
7. retain a separate raw/source view because perspective, lighting, LOD, and
   camera choices affect interpretation.

## Screenshot and disclosure rules

- Keep attribution visible in the PNG and complete provenance in the sidecar.
- Never use the renderer to scrape or batch-capture Google Maps, Google Earth,
  or Street View.
- Do not place precise coordinates for a vulnerable candidate into a public
  style, screenshot, filename, console log, or manifest.
- A screenshot from a third-party viewer is `manual-reference` unless its
  licence and export contract authorize local computation.
- A missing or incomplete render means `not rendered under these conditions`;
  it is not evidence that a feature is absent.

## Deterministic fixture

`fixtures/extrusion-job.json` renders three synthetic extruded structures and
a diagnostic custom WebGL triangle without network access.
`fixtures/terrain-job.json` renders a procedurally declared Terrain RGB source
through MapLibre's real terrain displacement and hillshade path. The committed
proofs under `artifacts/` record software WebGL2 on macOS, exact output
dimensions, framebuffer and PNG hashes, and non-background pixel counts. The
fixtures are regression geometry only and contain no archaeological or
external map data.
