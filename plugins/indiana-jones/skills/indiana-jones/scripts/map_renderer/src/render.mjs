import {createHash} from 'node:crypto';
import {mkdir, readFile, rename, stat, writeFile} from 'node:fs/promises';
import {basename, dirname, resolve} from 'node:path';
import {launchBrowser, createPage} from './cdp.mjs';
import {loadRenderJob, resolveJobAsset} from './job.mjs';
import {inspectPngBuffer, readPng} from './png.mjs';
import {startRenderServer} from './server.mjs';

function sha256Buffer(buffer) {
  return createHash('sha256').update(buffer).digest('hex');
}

async function sha256File(path) {
  return sha256Buffer(await readFile(path));
}

async function atomicWrite(path, buffer) {
  /*
   * Keep an interrupted capture from replacing the last known-good artefact.
   * The temporary file lives beside the target so rename remains atomic on
   * both macOS and Windows filesystems.
   */

  await mkdir(dirname(path), {recursive: true});
  const temporary = `${path}.${process.pid}.${Date.now()}.tmp`;
  await writeFile(temporary, buffer);
  await rename(temporary, path);
}

async function maybeHashLocalSource(source, jobRoot) {
  if (/^[a-z][a-z0-9+.-]*:/iu.test(source.locator)) {
    return {
      ...source,
      sha256Verification: source.sha256
        ? 'declared-unverified'
        : 'not-provided',
    };
  }
  try {
    const path = resolveJobAsset(jobRoot, source.locator, 'source.locator');
    const details = await stat(path);
    if (!details.isFile()) {
      return source;
    }
    const computedSha256 = await sha256File(path);
    if (source.sha256 && source.sha256 !== computedSha256) {
      throw new Error(`source hash mismatch for ${source.locator}`);
    }
    return {
      ...source,
      sha256: computedSha256,
      sha256Verification: 'computed',
    };
  } catch (error) {
    if (
      source.role === 'analysis' ||
      source.sha256 ||
      !/ENOENT/u.test(error.message)
    ) {
      throw error;
    }
    return source;
  }
}

async function buildInputManifest(loaded) {
  const {job, jobPath, jobRoot} = loaded;
  const sources = [];
  for (const source of job.sources) {
    sources.push(await maybeHashLocalSource(source, jobRoot));
  }
  const style =
    job.style.path !== undefined
      ? {
          kind: 'local',
          path: job.style.path,
          sha256: await sha256File(
            resolveJobAsset(jobRoot, job.style.path, 'style.path'),
          ),
        }
      : job.style.url !== undefined
        ? {kind: 'remote', url: job.style.url}
        : {
            kind: 'inline',
            sha256: sha256Buffer(Buffer.from(JSON.stringify(job.style.json))),
          };
  const customLayerModules = [];
  for (const modulePath of job.customLayerModules) {
    customLayerModules.push(
      /^https?:\/\//u.test(modulePath)
        ? {kind: 'remote', url: modulePath}
        : {
            kind: 'local',
            path: modulePath,
            sha256: await sha256File(
              resolveJobAsset(jobRoot, modulePath, 'customLayerModule'),
            ),
          },
    );
  }
  return {
    job: {
      file: basename(jobPath),
      sha256: await sha256File(jobPath),
      schemaVersion: job.schemaVersion,
    },
    disclosureClass: job.disclosureClass,
    coordinatePrecision: job.coordinatePrecision,
    networkPolicy: job.networkPolicy,
    attribution: job.attribution,
    style,
    customLayerModules,
    sources,
  };
}

function assertOutputDoesNotReplaceInput(loaded, outputPath, extraInputs = []) {
  /*
   * Atomic publication still destroys an existing target by design.
   * Fence every declared local input so a typo cannot replace the job, style,
   * adapter, source measurement, or imported fallback screenshot.
   */

  const target = resolve(outputPath);
  const candidates = [
    loaded.jobPath,
    ...extraInputs.map((inputPath) => resolve(inputPath)),
  ];
  const {job, jobRoot} = loaded;
  if (job.style.path) {
    candidates.push(resolveJobAsset(jobRoot, job.style.path, 'style.path'));
  }
  for (const modulePath of job.customLayerModules) {
    if (!/^https?:\/\//u.test(modulePath)) {
      candidates.push(
        resolveJobAsset(jobRoot, modulePath, 'customLayerModule'),
      );
    }
  }
  for (const source of job.sources) {
    if (!/^[a-z][a-z0-9+.-]*:/iu.test(source.locator)) {
      try {
        candidates.push(
          resolveJobAsset(jobRoot, source.locator, 'source.locator'),
        );
      } catch (error) {
        if (source.role === 'analysis') {
          throw error;
        }
      }
    }
  }
  if (job.fallbackScreenshot) {
    candidates.push(
      resolveJobAsset(jobRoot, job.fallbackScreenshot, 'fallbackScreenshot'),
    );
  }
  if (candidates.some((candidate) => resolve(candidate) === target)) {
    throw new Error('output path collides with a renderer input');
  }
}

async function waitForRender(page, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  let lastPhase = 'not-started';
  while (Date.now() < deadline) {
    const status = await page.evaluate(
      'window.__IJ_RENDERER__ ? ({phase: window.__IJ_RENDERER__.phase, done: window.__IJ_RENDERER__.done, error: window.__IJ_RENDERER__.error, result: window.__IJ_RENDERER__.result}) : null',
    );
    if (status) {
      lastPhase = status.phase;
      if (status.done) {
        if (status.error) {
          throw new Error(status.error);
        }
        return status.result;
      }
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 50));
  }
  throw new Error(`render timed out in phase "${lastPhase}" after ${timeoutMs} ms`);
}

function manifestPath(outputPath) {
  return `${outputPath}.render.json`;
}

function manualReferenceSource(options, inputPath) {
  const sourceId = options.sourceId;
  if (typeof sourceId !== 'string' || !/^[a-z][a-z0-9_-]{2,}$/u.test(sourceId)) {
    throw new Error('screenshot sourceId has an invalid format');
  }
  const kind = options.kind;
  if (
    ![
      'primary-measurement',
      'authoritative-record',
      'contemporary-account',
      'secondary-summary',
      'lead-only',
    ].includes(kind)
  ) {
    throw new Error('screenshot kind is unsupported');
  }
  if (
    typeof options.accessBasis !== 'string' ||
    options.accessBasis.trim() === ''
  ) {
    throw new Error('screenshot accessBasis is required');
  }
  if (typeof options.license !== 'string' || options.license.trim() === '') {
    throw new Error('screenshot license is required');
  }
  if (
    typeof options.accessedAt !== 'string' ||
    Number.isNaN(Date.parse(options.accessedAt))
  ) {
    throw new Error('screenshot accessedAt must be an ISO-8601 date');
  }
  return {
    sourceId,
    kind,
    role: 'manual-reference',
    locator: basename(inputPath),
    accessBasis: options.accessBasis.trim(),
    license: options.license.trim(),
    accessedAt: new Date(options.accessedAt).toISOString(),
  };
}

async function writeManifest(outputPath, manifest) {
  const body = Buffer.from(`${JSON.stringify(manifest, null, 2)}\n`);
  await atomicWrite(manifestPath(outputPath), body);
}

function publicCamera(camera, coordinatePrecision) {
  if (coordinatePrecision === 'region-only') {
    return {
      center: null,
      zoom: camera.zoom,
      pitch: camera.pitch,
      bearing: camera.bearing,
    };
  }
  if (coordinatePrecision === '0.1-degree') {
    return {
      ...camera,
      center: camera.center.map((value) => Math.round(value * 10) / 10),
    };
  }
  return camera;
}

function attachRuntimeOutputPath(manifest, outputPath) {
  Object.defineProperty(manifest, 'runtimeOutputPath', {
    value: outputPath,
    enumerable: false,
  });
  return manifest;
}

async function importFallback(
  loaded,
  inputPath,
  outputPath,
  {reason = null, primaryError = null, screenshotSource} = {},
) {
  /*
   * Preserve the screenshot as evidence without presenting it as a local
   * MapLibre render. The sidecar records the original hash and the failure
   * that caused an automatic fallback.
   */

  const source = resolve(inputPath);
  const target = resolve(outputPath);
  const {buffer, width, height} = await readPng(source);
  const screenshotSha256 = sha256Buffer(buffer);
  if (
    screenshotSource.sha256 &&
    screenshotSource.sha256 !== screenshotSha256
  ) {
    throw new Error(`screenshot hash mismatch for ${screenshotSource.locator}`);
  }
  const input = await buildInputManifest(loaded);
  const manifest = {
    schemaVersion: '1.0',
    createdAt: new Date().toISOString(),
    status: 'screenshot-fallback',
    renderer: {
      engine: 'imported-screenshot',
      reason,
      primaryError,
    },
    input: {
      ...input,
      screenshot: {
        ...screenshotSource,
        file: basename(source),
        sha256: screenshotSha256,
        sha256Verification: 'computed',
      },
    },
    output: {
      file: basename(target),
      width,
      height,
      sha256: sha256Buffer(buffer),
    },
  };
  await atomicWrite(target, buffer);
  await writeManifest(target, manifest);
  return attachRuntimeOutputPath(manifest, target);
}

export async function importScreenshot(options) {
  const loaded = await loadRenderJob(options.jobPath);
  assertOutputDoesNotReplaceInput(loaded, options.outputPath, [
    options.inputPath,
  ]);
  const screenshotSource = manualReferenceSource(options, options.inputPath);
  return await importFallback(
    loaded,
    options.inputPath,
    options.outputPath,
    {reason: options.reason ?? null, screenshotSource},
  );
}

export async function renderJob(options) {
  const loaded = await loadRenderJob(options.jobPath);
  const {job, jobRoot} = loaded;
  const outputPath = resolve(options.outputPath);
  assertOutputDoesNotReplaceInput(loaded, outputPath);
  let server;
  let browser;
  const startedAt = Date.now();
  try {
    server = await startRenderServer(job, jobRoot);
    browser = await launchBrowser({
      executablePath: options.browserPath,
      timeoutMs: Math.min(job.wait.timeoutMs, 30_000),
    });
    const page = await createPage(browser, job.viewport);
    await page.setNetworkPolicy(job.networkPolicy, server.url);
    await page.navigate(server.url);
    const result = await waitForRender(page, job.wait.timeoutMs);
    const network = page.networkSummary();
    if (network.blockedRequestCount > 0) {
      throw new Error(
        `${network.blockedRequestCount} request(s) violated networkPolicy`,
      );
    }
    const screenshot = await page.screenshot();
    const dimensions = inspectPngBuffer(screenshot);
    const input = await buildInputManifest(loaded);
    input.servedAssets = server.assets().map((asset) => ({
      ...asset,
      sourceIds: asset.file
        ? input.sources
            .filter((source) => basename(source.locator) === asset.file)
            .map((source) => source.sourceId)
        : [],
    }));
    const manifest = {
      schemaVersion: '1.0',
      createdAt: new Date().toISOString(),
      status: 'rendered',
      durationMs: Date.now() - startedAt,
      renderer: {
        engine: 'maplibre-gl-js',
        host: 'chromium-cdp',
        browserExecutable: basename(browser.executable),
        maplibreVersion: result.maplibreVersion,
        webgl: result.metrics,
        customModules: result.customModules,
        mapErrors: result.mapErrors,
        terrainEnabled: result.terrainEnabled,
        network,
      },
      input,
      camera: publicCamera(result.camera, job.coordinatePrecision),
      viewport: job.viewport,
      output: {
        file: basename(outputPath),
        width: dimensions.width,
        height: dimensions.height,
        sha256: sha256Buffer(screenshot),
      },
    };
    await atomicWrite(outputPath, screenshot);
    await writeManifest(outputPath, manifest);
    return attachRuntimeOutputPath(manifest, outputPath);
  } catch (error) {
    if (job.fallbackScreenshot) {
      const fallback = resolveJobAsset(
        jobRoot,
        job.fallbackScreenshot,
        'fallbackScreenshot',
      );
      const screenshotSource = job.sources.find(
        (source) =>
          source.role === 'manual-reference' &&
          source.locator === job.fallbackScreenshot,
      );
      return await importFallback(loaded, fallback, outputPath, {
        primaryError: error.message,
        screenshotSource,
      });
    }
    throw error;
  } finally {
    const cleanup = [];
    if (browser) {
      cleanup.push(browser.close());
    }
    if (server) {
      cleanup.push(server.close());
    }
    await Promise.allSettled(cleanup);
  }
}

export async function probeWebGl(options = {}) {
  const browser = await launchBrowser({
    executablePath: options.browserPath,
    timeoutMs: options.timeoutMs ?? 10_000,
  });
  try {
    const page = await createPage(browser, {
      width: 64,
      height: 64,
      pixelRatio: 1,
    });
    const html =
      '<canvas id="c" width="64" height="64"></canvas><script>const gl=c.getContext("webgl2");window.probe=gl?{webgl2:true,vendor:gl.getParameter(gl.VENDOR),renderer:gl.getParameter(gl.RENDERER),version:gl.getParameter(gl.VERSION)}:{webgl2:false};</script>';
    await page.navigate(`data:text/html,${encodeURIComponent(html)}`);
    let result = null;
    for (let attempt = 0; attempt < 100 && !result; attempt += 1) {
      result = await page.evaluate('window.probe ?? null');
      if (!result) {
        await new Promise((resolvePromise) => setTimeout(resolvePromise, 20));
      }
    }
    if (!result?.webgl2) {
      throw new Error('browser launched but WebGL2 is unavailable');
    }
    return {
      ok: true,
      browserExecutable: browser.executable,
      platform: process.platform,
      arch: process.arch,
      node: process.version,
      ...result,
    };
  } finally {
    await browser.close();
  }
}

export function renderSummary(manifest) {
  const outputPath = manifest.runtimeOutputPath ?? manifest.output.file;
  return {
    status: manifest.status,
    output: outputPath,
    manifest: manifestPath(outputPath),
    dimensions: [manifest.output.width, manifest.output.height],
    sha256: manifest.output.sha256,
    engine: manifest.renderer.engine,
    webgl2: manifest.renderer.webgl?.webgl2 ?? null,
    nonBackgroundPixels:
      manifest.renderer.webgl?.nonBackgroundPixels ?? null,
    file: manifest.output.file,
  };
}
