import {createServer} from 'node:http';
import {createHash} from 'node:crypto';
import {createReadStream, realpathSync} from 'node:fs';
import {readFile, stat} from 'node:fs/promises';
import {createRequire} from 'node:module';
import {dirname, extname, join, resolve, sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {pipeline} from 'node:stream/promises';
import {syntheticDemPng} from './dem.mjs';

const require = createRequire(import.meta.url);
const sourceRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const webRoot = join(sourceRoot, 'web');

function contentType(path) {
  const extension = extname(path).toLowerCase();
  return (
    {
      '.css': 'text/css; charset=utf-8',
      '.glb': 'model/gltf-binary',
      '.gltf': 'model/gltf+json',
      '.html': 'text/html; charset=utf-8',
      '.jpeg': 'image/jpeg',
      '.jpg': 'image/jpeg',
      '.js': 'text/javascript; charset=utf-8',
      '.json': 'application/json; charset=utf-8',
      '.mjs': 'text/javascript; charset=utf-8',
      '.pbf': 'application/x-protobuf',
      '.png': 'image/png',
      '.webp': 'image/webp',
    }[extension] ?? 'application/octet-stream'
  );
}

function resolveInside(root, requestPath) {
  /*
   * Decode once and fence every browser-visible path to the job directory.
   * The renderer may serve source tiles and models, but it must not expose
   * unrelated files from the user's machine.
   */

  const relative = decodeURIComponent(requestPath).replace(/^\/+/u, '');
  const absolute = resolve(root, relative);
  let canonical;
  try {
    canonical = realpathSync(absolute);
  } catch {
    return null;
  }
  const canonicalRoot = realpathSync(root);
  const rootPrefix = canonicalRoot.endsWith(sep)
    ? canonicalRoot
    : `${canonicalRoot}${sep}`;
  if (canonical !== canonicalRoot && !canonical.startsWith(rootPrefix)) {
    return null;
  }
  return canonical;
}

function sha256(buffer) {
  return createHash('sha256').update(buffer).digest('hex');
}

function parseRange(value, size) {
  if (!value) {
    return null;
  }
  const match = /^bytes=(\d*)-(\d*)$/u.exec(value);
  if (!match) {
    throw new Error('unsupported range');
  }
  let start = match[1] ? Number.parseInt(match[1], 10) : null;
  let end = match[2] ? Number.parseInt(match[2], 10) : null;
  if (start === null && end !== null) {
    start = Math.max(0, size - end);
    end = size - 1;
  } else {
    start ??= 0;
    end ??= size - 1;
  }
  if (start < 0 || end < start || start >= size || end >= size) {
    throw new Error('range is outside the file');
  }
  return {start, end};
}

async function sendFile(request, response, path, digestFile, record = null) {
  try {
    const details = await stat(path);
    if (!details.isFile()) {
      throw new Error('not a regular file');
    }
    const digest = await digestFile(path);
    record?.({bytes: details.size, sha256: digest});
    const range = parseRange(request.headers.range, details.size);
    const headers = {
      'Content-Type': contentType(path),
      'Cache-Control': 'no-store',
      'Accept-Ranges': 'bytes',
    };
    if (range) {
      headers['Content-Range'] =
        `bytes ${range.start}-${range.end}/${details.size}`;
      headers['Content-Length'] = String(range.end - range.start + 1);
      response.writeHead(206, headers);
    } else {
      headers['Content-Length'] = String(details.size);
      response.writeHead(200, headers);
    }
    await pipeline(createReadStream(path, range ?? undefined), response);
  } catch {
    if (response.headersSent) {
      response.destroy();
      return;
    }
    if (request.headers.range) {
      response.writeHead(416, {'Content-Type': 'text/plain; charset=utf-8'});
      response.end('range not satisfiable');
      return;
    }
    response.writeHead(404, {'Content-Type': 'text/plain; charset=utf-8'});
    response.end('not found');
  }
}

function browserJob(job) {
  const style = job.style.path
    ? {url: `/assets/${job.style.path.split(sep).join('/')}`}
    : job.style;
  const customLayerModules = job.customLayerModules.map((modulePath) =>
    /^https?:\/\//u.test(modulePath)
      ? modulePath
      : `/assets/${modulePath.split(sep).join('/')}`,
  );
  return {...job, style, customLayerModules};
}

export async function startRenderServer(job, jobRoot) {
  const maplibrePackage = require.resolve('maplibre-gl/package.json');
  const maplibreDist = join(dirname(maplibrePackage), 'dist');
  const serializedJob = JSON.stringify(browserJob(job));
  const fileHashes = new Map();
  const digestFile = async (path) => {
    if (!fileHashes.has(path)) {
      fileHashes.set(
        path,
        (async () => {
          const digest = createHash('sha256');
          for await (const chunk of createReadStream(path)) {
            digest.update(chunk);
          }
          return digest.digest('hex');
        })(),
      );
    }
    return await fileHashes.get(path);
  };
  const syntheticSource = job.sources.find(
    (source) =>
      source.role === 'analysis' &&
      source.locator.endsWith('synthetic-dem.json'),
  );
  let syntheticDem = null;
  let syntheticConfiguration = null;
  if (syntheticSource) {
    const configurationPath = resolveInside(jobRoot, syntheticSource.locator);
    if (!configurationPath) {
      throw new Error('synthetic DEM configuration escapes the job directory');
    }
    syntheticConfiguration = await readFile(configurationPath);
    syntheticDem = syntheticDemPng(JSON.parse(syntheticConfiguration));
  }
  const servedAssets = new Map();
  const recordAsset = (route, kind, file = null) => (details) => {
    const publicRoute =
      job.coordinatePrecision === 'exact'
        ? route
        : route.startsWith('/synthetic-dem/')
          ? '/synthetic-dem/[redacted]'
          : route.startsWith('/assets/')
            ? `/assets/${route.split('/').at(-1)}`
            : route;
    servedAssets.set(`${kind}:${publicRoute}`, {
      route: publicRoute,
      kind,
      file,
      bytes: details.bytes,
      sha256: details.sha256,
    });
  };
  const server = createServer(async (request, response) => {
    const url = new URL(request.url ?? '/', 'http://127.0.0.1');
    if (url.pathname === '/' || url.pathname === '/renderer.html') {
      await sendFile(
        request,
        response,
        join(webRoot, 'renderer.html'),
        digestFile,
        recordAsset('/renderer.html', 'runtime'),
      );
      return;
    }
    if (url.pathname === '/renderer.mjs') {
      await sendFile(
        request,
        response,
        join(webRoot, 'renderer.mjs'),
        digestFile,
        recordAsset('/renderer.mjs', 'runtime'),
      );
      return;
    }
    if (url.pathname === '/vendor/maplibre-gl.js') {
      await sendFile(
        request,
        response,
        join(maplibreDist, 'maplibre-gl.js'),
        digestFile,
        recordAsset('/vendor/maplibre-gl.js', 'runtime'),
      );
      return;
    }
    if (url.pathname === '/vendor/maplibre-gl.css') {
      await sendFile(
        request,
        response,
        join(maplibreDist, 'maplibre-gl.css'),
        digestFile,
        recordAsset('/vendor/maplibre-gl.css', 'runtime'),
      );
      return;
    }
    if (url.pathname === '/job.json') {
      response.writeHead(200, {
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'no-store',
      });
      response.end(serializedJob);
      return;
    }
    if (url.pathname.startsWith('/synthetic-dem/')) {
      if (!syntheticDem || !syntheticConfiguration) {
        response.writeHead(404, {'Content-Type': 'text/plain; charset=utf-8'});
        response.end('synthetic DEM is not configured for this job');
        return;
      }
      recordAsset(
        '/assets/synthetic-dem.json',
        'derived-input',
        'synthetic-dem.json',
      )({
        bytes: syntheticConfiguration.length,
        sha256: sha256(syntheticConfiguration),
      });
      recordAsset(url.pathname, 'derived-fixture')({
        bytes: syntheticDem.length,
        sha256: sha256(syntheticDem),
      });
      response.writeHead(200, {
        'Content-Type': 'image/png',
        'Cache-Control': 'public, max-age=3600, immutable',
      });
      response.end(syntheticDem);
      return;
    }
    if (url.pathname.startsWith('/assets/')) {
      let path;
      try {
        path = resolveInside(jobRoot, url.pathname.slice('/assets/'.length));
      } catch {
        response.writeHead(400, {'Content-Type': 'text/plain; charset=utf-8'});
        response.end('malformed asset path');
        return;
      }
      if (!path) {
        response.writeHead(403, {'Content-Type': 'text/plain; charset=utf-8'});
        response.end('forbidden');
        return;
      }
      await sendFile(
        request,
        response,
        path,
        digestFile,
        recordAsset(url.pathname, 'job-asset', url.pathname.split('/').at(-1)),
      );
      return;
    }
    response.writeHead(404, {'Content-Type': 'text/plain; charset=utf-8'});
    response.end('not found');
  });
  await new Promise((resolvePromise, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolvePromise);
  });
  const address = server.address();
  if (!address || typeof address === 'string') {
    throw new Error('renderer server did not bind a TCP port');
  }
  return {
    url: `http://127.0.0.1:${address.port}/renderer.html`,
    assets() {
      return [...servedAssets.values()].sort((left, right) =>
        left.route.localeCompare(right.route),
      );
    },
    async close() {
      await new Promise((resolvePromise, reject) =>
        server.close((error) => (error ? reject(error) : resolvePromise())),
      );
    },
  };
}
