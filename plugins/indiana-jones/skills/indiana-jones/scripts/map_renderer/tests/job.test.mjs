import assert from 'node:assert/strict';
import {mkdir, mkdtemp, rm, symlink, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {test} from 'node:test';
import {resolveJobAsset, validateRenderJob} from '../src/job.mjs';

function validJob() {
  return {
    schemaVersion: '1.0',
    mode: 'maplibre-style',
    disclosureClass: 'restricted',
    coordinatePrecision: 'exact',
    networkPolicy: {mode: 'local-only', allowedHosts: []},
    attribution: 'Local test source',
    style: {json: {version: 8, sources: {}, layers: []}},
    sources: [
      {
        sourceId: 'src_fixture',
        kind: 'primary-measurement',
        role: 'analysis',
        locator: 'fixture.json',
        accessBasis: 'local',
        license: 'CC0-1.0',
        crs: 'EPSG:4326',
        accessedAt: '2026-07-24T00:00:00Z',
      },
    ],
  };
}

test('normalizes deterministic render defaults', () => {
  const result = validateRenderJob(validJob());
  assert.deepEqual(result.camera, {
    center: [0, 0],
    zoom: 0,
    pitch: 0,
    bearing: 0,
  });
  assert.deepEqual(result.viewport, {
    width: 1024,
    height: 768,
    pixelRatio: 1,
  });
  assert.equal(result.wait.failOnMapError, true);
});

test('rejects source records that cannot support local computation', () => {
  const job = validJob();
  job.sources[0].role = 'manual-reference';
  assert.throws(
    () => validateRenderJob(job),
    /must include an analysis source/u,
  );
});

test('requires exactly one style transport', () => {
  const job = validJob();
  job.style.url = 'https://example.test/style.json';
  assert.throws(
    () => validateRenderJob(job),
    /exactly one of json, path, or url/u,
  );
});

test('rejects viewport sizes that can accidentally exhaust GPU memory', () => {
  const job = validJob();
  job.viewport = {width: 20_000, height: 100};
  assert.throws(() => validateRenderJob(job), /viewport.width/u);
});

test('requires an explicit public-coordinate policy', () => {
  const job = validJob();
  delete job.coordinatePrecision;
  assert.throws(() => validateRenderJob(job), /coordinatePrecision/u);
});

test('caps combined viewport size and pixel ratio', () => {
  const job = validJob();
  job.viewport = {width: 4096, height: 4096, pixelRatio: 2};
  assert.throws(() => validateRenderJob(job), /physical-pixel safety limit/u);
});

test('rejects assets that escape through a symlink', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'ij-job-fence-'));
  const jobRoot = join(directory, 'job');
  const outside = join(directory, 'outside.json');
  await mkdir(jobRoot);
  await writeFile(outside, '{}');
  await symlink(outside, join(jobRoot, 'linked.json'));
  try {
    assert.throws(
      () => resolveJobAsset(jobRoot, 'linked.json', 'fixture'),
      /escapes the job directory/u,
    );
  } finally {
    await rm(directory, {recursive: true, force: true});
  }
});

test('requires remote styles to use an explicit hostname allowlist', () => {
  const job = validJob();
  job.style = {url: 'https://tiles.example.test/style.json'};
  assert.throws(() => validateRenderJob(job), /not authorized/u);
  job.networkPolicy = {
    mode: 'allowlist',
    allowedHosts: ['tiles.example.test'],
  };
  assert.equal(validateRenderJob(job).style.url, job.style.url);
});
