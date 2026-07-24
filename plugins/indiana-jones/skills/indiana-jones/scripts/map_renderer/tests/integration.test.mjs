import assert from 'node:assert/strict';
import {
  copyFile,
  mkdir,
  mkdtemp,
  readFile,
  rm,
  writeFile,
} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {dirname, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {test} from 'node:test';
import {
  importScreenshot,
  probeWebGl,
  renderJob,
} from '../src/render.mjs';

const packageRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const fixtureJob = join(packageRoot, 'fixtures', 'extrusion-job.json');
const terrainJob = join(packageRoot, 'fixtures', 'terrain-job.json');
const flatTerrainJob = join(
  packageRoot,
  'fixtures',
  'terrain-flat-job.json',
);
const blockedNetworkJob = join(
  packageRoot,
  'fixtures',
  'blocked-network-job.json',
);
const blockedWorkerJob = join(
  packageRoot,
  'fixtures',
  'blocked-worker-job.json',
);

test('probes WebGL2 in a real headless browser', async () => {
  const result = await probeWebGl();
  assert.equal(result.ok, true);
  assert.equal(result.webgl2, true);
  assert.match(result.version, /WebGL 2/u);
});

test('renders local 3D extrusions and a custom WebGL layer', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'ij-render-test-'));
  try {
    const output = join(directory, 'extrusion.png');
    const manifest = await renderJob({jobPath: fixtureJob, outputPath: output});
    assert.equal(manifest.status, 'rendered');
    assert.equal(manifest.renderer.maplibreVersion, '5.23.0');
    assert.equal(manifest.renderer.webgl.webgl2, true);
    assert.ok(manifest.renderer.webgl.nonBackgroundPixels > 10_000);
    assert.ok(manifest.renderer.webgl.luminanceVariance > 10);
    assert.deepEqual(
      manifest.renderer.customModules[0].layerIds,
      ['fixture-custom-webgl-layer'],
    );
    assert.ok(
      manifest.input.servedAssets.some(
        (asset) =>
          asset.kind === 'job-asset' &&
          asset.route === '/assets/extrusion-style.json',
      ),
    );
    assert.deepEqual(
      [manifest.output.width, manifest.output.height],
      [640, 480],
    );
    assert.equal((await readFile(output)).subarray(1, 4).toString('ascii'), 'PNG');
    assert.equal(
      JSON.parse(await readFile(`${output}.render.json`, 'utf8')).output.sha256,
      manifest.output.sha256,
    );
  } finally {
    await rm(directory, {recursive: true, force: true});
  }
});

test('imports an existing screenshot with a distinct fallback manifest', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'ij-fallback-test-'));
  try {
    const rendered = join(directory, 'rendered.png');
    await renderJob({jobPath: fixtureJob, outputPath: rendered});
    const imported = join(directory, 'imported.png');
    const manifest = await importScreenshot({
      jobPath: fixtureJob,
      inputPath: rendered,
      outputPath: imported,
      sourceId: 'src_manual_fixture',
      kind: 'lead-only',
      license: 'CC0-1.0',
      accessBasis: 'local regression output',
      accessedAt: '2026-07-24T00:00:00Z',
      reason: 'manual reference supplied by analyst',
    });
    assert.equal(manifest.status, 'screenshot-fallback');
    assert.equal(manifest.renderer.engine, 'imported-screenshot');
    assert.equal(
      manifest.input.screenshot.sha256,
      manifest.output.sha256,
    );
    assert.deepEqual(
      [manifest.output.width, manifest.output.height],
      [640, 480],
    );
  } finally {
    await rm(directory, {recursive: true, force: true});
  }
});

test('renders local raster-dem terrain without network access', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'ij-terrain-test-'));
  try {
    const output = join(directory, 'terrain.png');
    const manifest = await renderJob({jobPath: terrainJob, outputPath: output});
    const flatManifest = await renderJob({
      jobPath: flatTerrainJob,
      outputPath: join(directory, 'terrain-flat.png'),
    });
    assert.equal(manifest.status, 'rendered');
    assert.equal(manifest.renderer.terrainEnabled, true);
    assert.equal(manifest.renderer.webgl.webgl2, true);
    assert.ok(manifest.renderer.webgl.nonBackgroundPixels > 30_000);
    assert.ok(manifest.renderer.webgl.luminanceVariance > 10);
    assert.equal(manifest.camera.pitch, 60);
    assert.notEqual(
      manifest.renderer.webgl.framebufferSha256,
      flatManifest.renderer.webgl.framebufferSha256,
    );
    assert.ok(
      Math.abs(
        manifest.renderer.webgl.nonBackgroundPixels -
          flatManifest.renderer.webgl.nonBackgroundPixels,
      ) > 1_000,
    );
    assert.ok(
      manifest.input.servedAssets.some(
        (asset) => asset.kind === 'derived-fixture',
      ),
    );
  } finally {
    await rm(directory, {recursive: true, force: true});
  }
});

test('blocks undeclared network access from a local adapter', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'ij-network-test-'));
  try {
    await assert.rejects(
      () =>
        renderJob({
          jobPath: blockedNetworkJob,
          outputPath: join(directory, 'blocked.png'),
        }),
      /violated networkPolicy/u,
    );
  } finally {
    await rm(directory, {recursive: true, force: true});
  }
});

test('blocks undeclared network access from a dedicated worker', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'ij-worker-network-test-'));
  try {
    await assert.rejects(
      () =>
        renderJob({
          jobPath: blockedWorkerJob,
          outputPath: join(directory, 'blocked-worker.png'),
        }),
      /violated networkPolicy/u,
    );
  } finally {
    await rm(directory, {recursive: true, force: true});
  }
});

test('refuses to overwrite a declared renderer input', async () => {
  await assert.rejects(
    () =>
      renderJob({
        jobPath: fixtureJob,
        outputPath: fixtureJob,
      }),
    /output path collides/u,
  );
});

test('uses a declared screenshot when browser startup fails', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'ij-auto-fallback-test-'));
  try {
    const rendered = join(directory, 'source.png');
    await renderJob({jobPath: fixtureJob, outputPath: rendered});
    const jobRoot = join(directory, 'job');
    await mkdir(jobRoot);
    await copyFile(
      join(packageRoot, 'fixtures', 'extrusion-style.json'),
      join(jobRoot, 'style.json'),
    );
    await copyFile(rendered, join(jobRoot, 'fallback.png'));
    const jobPath = join(jobRoot, 'job.json');
    await writeFile(
      jobPath,
      `${JSON.stringify({
        schemaVersion: '1.0',
        mode: 'maplibre-style',
        disclosureClass: 'restricted',
        coordinatePrecision: 'region-only',
        networkPolicy: {mode: 'local-only', allowedHosts: []},
        attribution: 'Synthetic automatic fallback fixture',
        style: {path: 'style.json'},
        sources: [
          {
            sourceId: 'src_fallback_analysis',
            kind: 'primary-measurement',
            role: 'analysis',
            locator: 'style.json',
            accessBasis: 'local test',
            license: 'CC0-1.0',
            crs: 'EPSG:4326',
            accessedAt: '2026-07-24T00:00:00Z',
          },
          {
            sourceId: 'src_fallback_screenshot',
            kind: 'lead-only',
            role: 'manual-reference',
            locator: 'fallback.png',
            accessBasis: 'local test',
            license: 'CC0-1.0',
            crs: 'unknown',
            accessedAt: '2026-07-24T00:00:00Z',
          },
        ],
        customLayerModules: [],
        fallbackScreenshot: 'fallback.png',
      }, null, 2)}\n`,
    );
    const manifest = await renderJob({
      jobPath,
      outputPath: join(directory, 'fallback-output.png'),
      browserPath: join(directory, 'missing-browser'),
    });
    assert.equal(manifest.status, 'screenshot-fallback');
    assert.match(manifest.renderer.primaryError, /does not exist/u);
    assert.equal(
      manifest.input.screenshot.sourceId,
      'src_fallback_screenshot',
    );
  } finally {
    await rm(directory, {recursive: true, force: true});
  }
});
