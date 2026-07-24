const state = {
  phase: 'starting',
  done: false,
  result: null,
  error: null,
};
window.__IJ_RENDERER__ = state;

function errorText(error) {
  return error instanceof Error ? error.stack ?? error.message : String(error);
}

function once(target, eventName) {
  return new Promise((resolvePromise) => target.once(eventName, resolvePromise));
}

async function sha256(bytes) {
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)]
    .map((value) => value.toString(16).padStart(2, '0'))
    .join('');
}

async function captureWebGlMetrics(map) {
  /*
   * Read the framebuffer immediately after a requested repaint.
   * preserveDrawingBuffer stays disabled for normal operation; synchronizing
   * the read to MapLibre's render event avoids its memory/performance cost.
   */

  return await new Promise((resolvePromise, reject) => {
    const timer = setTimeout(
      () => reject(new Error('timed out waiting for framebuffer repaint')),
      5_000,
    );
    map.once('render', async () => {
      try {
        clearTimeout(timer);
        const canvas = map.getCanvas();
        const gl = canvas.getContext('webgl2');
        if (!gl) {
          throw new Error('MapLibre canvas did not expose WebGL2');
        }
        const width = gl.drawingBufferWidth;
        const height = gl.drawingBufferHeight;
        const pixels = new Uint8Array(width * height * 4);
        gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
        const corner = pixels.subarray(0, 4);
        let nonBackgroundPixels = 0;
        let opaquePixels = 0;
        let luminanceSum = 0;
        let luminanceSquaredSum = 0;
        for (let offset = 0; offset < pixels.length; offset += 4) {
          const red = pixels[offset];
          const green = pixels[offset + 1];
          const blue = pixels[offset + 2];
          const alpha = pixels[offset + 3];
          const difference =
            Math.abs(red - corner[0]) +
            Math.abs(green - corner[1]) +
            Math.abs(blue - corner[2]);
          if (difference > 12) {
            nonBackgroundPixels += 1;
          }
          if (alpha > 0) {
            opaquePixels += 1;
          }
          const luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue;
          luminanceSum += luminance;
          luminanceSquaredSum += luminance * luminance;
        }
        const pixelCount = width * height;
        const mean = luminanceSum / pixelCount;
        const variance = luminanceSquaredSum / pixelCount - mean * mean;
        const debugExtension = gl.getExtension('WEBGL_debug_renderer_info');
        resolvePromise({
          webgl2: true,
          width,
          height,
          pixelCount,
          nonBackgroundPixels,
          opaquePixels,
          luminanceMean: mean,
          luminanceVariance: Math.max(0, variance),
          framebufferSha256: await sha256(pixels),
          vendor: gl.getParameter(gl.VENDOR),
          renderer: gl.getParameter(gl.RENDERER),
          unmaskedVendor: debugExtension
            ? gl.getParameter(debugExtension.UNMASKED_VENDOR_WEBGL)
            : null,
          unmaskedRenderer: debugExtension
            ? gl.getParameter(debugExtension.UNMASKED_RENDERER_WEBGL)
            : null,
          version: gl.getParameter(gl.VERSION),
          shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
        });
      } catch (error) {
        reject(error);
      }
    });
    map.triggerRepaint();
  });
}

async function installCustomModules(map, job) {
  /*
   * A module owns its readiness gate because MapLibre's idle event cannot see
   * third-party tile fetches. This is the seam used by Three.js and
   * 3d-tiles-renderer adapters without hard-coding one provider or tileset.
   *
   * Returns: IDs reported by successfully installed modules.
   */

  const installed = [];
  for (const moduleUrl of job.customLayerModules) {
    const loaded = await import(moduleUrl);
    if (typeof loaded.install !== 'function') {
      throw new Error(`${moduleUrl} must export async function install(context)`);
    }
    const result = await loaded.install({
      map,
      maplibregl: window.maplibregl,
      job,
    });
    if (result?.ready) {
      await result.ready;
    }
    installed.push({
      module: moduleUrl,
      layerIds: Array.isArray(result?.layerIds) ? result.layerIds : [],
    });
  }
  return installed;
}

async function run() {
  /*
   * Wait for both MapLibre-owned work and adapter-owned work before capture.
   * Errors remain part of the result so a caller may explicitly relax the
   * policy for incomplete remote styles without losing the evidence.
   */

  state.phase = 'loading-job';
  const job = await fetch('/job.json', {cache: 'no-store'}).then((response) => {
    if (!response.ok) {
      throw new Error(`job request failed with ${response.status}`);
    }
    return response.json();
  });
  document.querySelector('#attribution').textContent = job.attribution;
  const style = job.style.json ?? job.style.url;
  const mapErrors = [];
  state.phase = 'creating-map';
  const map = new window.maplibregl.Map({
    container: 'map',
    style,
    center: job.camera.center,
    zoom: job.camera.zoom,
    pitch: job.camera.pitch,
    bearing: job.camera.bearing,
    maxPitch: 85,
    maxZoom: 24,
    interactive: false,
    attributionControl: false,
    pixelRatio: job.viewport.pixelRatio,
    canvasContextAttributes: {
      antialias: true,
      contextType: 'webgl2',
      preserveDrawingBuffer: false,
    },
  });
  map.on('error', (event) => {
    mapErrors.push(errorText(event.error ?? event));
  });
  await once(map, 'style.load');
  state.phase = 'installing-custom-layers';
  const customModules = await installCustomModules(map, job);
  state.phase = 'waiting-for-idle';
  if (!map.loaded()) {
    await once(map, 'idle');
  }
  if (job.wait.settleMs > 0) {
    await new Promise((resolvePromise) =>
      setTimeout(resolvePromise, job.wait.settleMs),
    );
  }
  if (job.wait.failOnMapError && mapErrors.length > 0) {
    throw new Error(`MapLibre reported errors:\n${mapErrors.join('\n')}`);
  }
  state.phase = 'reading-framebuffer';
  const metrics = await captureWebGlMetrics(map);
  state.result = {
    maplibreVersion:
      window.maplibregl.getVersion?.() ??
      window.maplibregl.version ??
      'unknown',
    camera: {
      center: map.getCenter().toArray(),
      zoom: map.getZoom(),
      pitch: map.getPitch(),
      bearing: map.getBearing(),
    },
    customModules,
    mapErrors,
    terrainEnabled: Boolean(map.getTerrain?.()),
    metrics,
  };
  state.phase = 'ready';
  state.done = true;
}

run().catch((error) => {
  state.phase = 'failed';
  state.error = errorText(error);
  state.done = true;
});
