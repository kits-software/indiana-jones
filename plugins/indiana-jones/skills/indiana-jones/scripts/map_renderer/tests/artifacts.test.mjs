import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readdir, readFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import {basename, dirname, join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {test} from 'node:test';
import {syntheticDemPng} from '../src/dem.mjs';

const require = createRequire(import.meta.url);
const packageRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const artifactRoot = join(packageRoot, 'artifacts');
const fixtureRoot = join(packageRoot, 'fixtures');
const webRoot = join(packageRoot, 'web');
const maplibreRoot = dirname(require.resolve('maplibre-gl/package.json'));

function sha256(buffer) {
  return createHash('sha256').update(buffer).digest('hex');
}

async function sha256File(path) {
  return sha256(await readFile(path));
}

async function expectedServedAssetHash(asset) {
  if (asset.kind === 'job-asset' || asset.kind === 'derived-input') {
    return await sha256File(join(fixtureRoot, asset.file));
  }
  if (asset.kind === 'derived-fixture') {
    const configuration = JSON.parse(
      await readFile(join(fixtureRoot, 'synthetic-dem.json'), 'utf8'),
    );
    return sha256(syntheticDemPng(configuration));
  }
  if (asset.route === '/renderer.html') {
    return await sha256File(join(webRoot, 'renderer.html'));
  }
  if (asset.route === '/renderer.mjs') {
    return await sha256File(join(webRoot, 'renderer.mjs'));
  }
  if (asset.route === '/vendor/maplibre-gl.js') {
    return await sha256File(join(maplibreRoot, 'dist', 'maplibre-gl.js'));
  }
  if (asset.route === '/vendor/maplibre-gl.css') {
    return await sha256File(join(maplibreRoot, 'dist', 'maplibre-gl.css'));
  }
  throw new Error(`unmapped served asset: ${asset.route}`);
}

test('committed render proofs match every referenced local byte source', async () => {
  const manifestFiles = (await readdir(artifactRoot))
    .filter((file) => file.endsWith('.png.render.json'))
    .sort();
  assert.deepEqual(manifestFiles, [
    'extrusion.png.render.json',
    'terrain.png.render.json',
  ]);
  for (const manifestFile of manifestFiles) {
    const manifest = JSON.parse(
      await readFile(join(artifactRoot, manifestFile), 'utf8'),
    );
    assert.equal(manifest.status, 'rendered');
    assert.notEqual(manifest.renderer.maplibreVersion, 'unknown');
    assert.equal(
      await sha256File(join(artifactRoot, manifest.output.file)),
      manifest.output.sha256,
    );
    assert.equal(
      await sha256File(join(fixtureRoot, manifest.input.job.file)),
      manifest.input.job.sha256,
    );
    if (manifest.input.style.kind === 'local') {
      assert.equal(
        await sha256File(join(fixtureRoot, manifest.input.style.path)),
        manifest.input.style.sha256,
      );
    }
    for (const moduleRecord of manifest.input.customLayerModules) {
      if (moduleRecord.kind === 'local') {
        assert.equal(
          await sha256File(join(fixtureRoot, moduleRecord.path)),
          moduleRecord.sha256,
        );
      }
    }
    for (const source of manifest.input.sources) {
      if (source.sha256Verification === 'computed') {
        assert.equal(
          await sha256File(join(fixtureRoot, basename(source.locator))),
          source.sha256,
        );
        assert.ok(
          manifest.input.servedAssets.some((asset) =>
            asset.sourceIds.includes(source.sourceId),
          ),
        );
      }
    }
    for (const asset of manifest.input.servedAssets) {
      assert.equal(await expectedServedAssetHash(asset), asset.sha256);
    }
  }
});
