import {readFile, stat} from 'node:fs/promises';
import {realpathSync} from 'node:fs';
import {dirname, resolve, sep} from 'node:path';

const DISCLOSURE_CLASSES = new Set([
  'public',
  'restricted',
  'heritage-authority-only',
]);
const SOURCE_ROLES = new Set([
  'analysis',
  'negative-control',
  'corroboration',
  'ground-truth',
  'manual-reference',
]);
const COORDINATE_PRECISIONS = new Set([
  'exact',
  '0.1-degree',
  'region-only',
]);
const SOURCE_KINDS = new Set([
  'primary-measurement',
  'authoritative-record',
  'contemporary-account',
  'secondary-summary',
  'lead-only',
]);

function isPlainObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function requireString(value, label) {
  if (typeof value !== 'string' || value.trim() === '') {
    throw new Error(`${label} must be a non-empty string`);
  }
  return value.trim();
}

function requireFiniteNumber(value, label, minimum, maximum) {
  if (!Number.isFinite(value) || value < minimum || value > maximum) {
    throw new Error(`${label} must be between ${minimum} and ${maximum}`);
  }
  return value;
}

function normalizeStyle(style) {
  if (!isPlainObject(style)) {
    throw new Error('style must be an object');
  }
  const keys = ['json', 'path', 'url'].filter((key) => style[key] !== undefined);
  if (keys.length !== 1) {
    throw new Error('style must define exactly one of json, path, or url');
  }
  if (style.json !== undefined && !isPlainObject(style.json)) {
    throw new Error('style.json must be a MapLibre style object');
  }
  if (style.path !== undefined) {
    return {path: requireString(style.path, 'style.path')};
  }
  if (style.url !== undefined) {
    const url = requireString(style.url, 'style.url');
    if (!/^https?:\/\//u.test(url)) {
      throw new Error('style.url must use http or https');
    }
    return {url};
  }
  return {json: style.json};
}

function normalizeCamera(camera = {}) {
  if (!isPlainObject(camera)) {
    throw new Error('camera must be an object');
  }
  const center = camera.center ?? [0, 0];
  if (
    !Array.isArray(center) ||
    center.length !== 2 ||
    !Number.isFinite(center[0]) ||
    !Number.isFinite(center[1])
  ) {
    throw new Error('camera.center must be [longitude, latitude]');
  }
  return {
    center: [
      requireFiniteNumber(center[0], 'camera.center[0]', -180, 180),
      requireFiniteNumber(center[1], 'camera.center[1]', -85.051129, 85.051129),
    ],
    zoom: requireFiniteNumber(camera.zoom ?? 0, 'camera.zoom', 0, 24),
    pitch: requireFiniteNumber(camera.pitch ?? 0, 'camera.pitch', 0, 85),
    bearing: requireFiniteNumber(camera.bearing ?? 0, 'camera.bearing', -360, 360),
  };
}

function normalizeViewport(viewport = {}) {
  if (!isPlainObject(viewport)) {
    throw new Error('viewport must be an object');
  }
  const result = {
    width: Math.round(
      requireFiniteNumber(viewport.width ?? 1024, 'viewport.width', 64, 8192),
    ),
    height: Math.round(
      requireFiniteNumber(viewport.height ?? 768, 'viewport.height', 64, 8192),
    ),
    pixelRatio: requireFiniteNumber(
      viewport.pixelRatio ?? 1,
      'viewport.pixelRatio',
      0.5,
      4,
    ),
  };
  const physicalPixels =
    result.width * result.height * result.pixelRatio * result.pixelRatio;
  if (physicalPixels > 16_777_216) {
    throw new Error(
      'viewport exceeds the 16,777,216 physical-pixel safety limit',
    );
  }
  return result;
}

function normalizeWait(wait = {}) {
  if (!isPlainObject(wait)) {
    throw new Error('wait must be an object');
  }
  return {
    timeoutMs: Math.round(
      requireFiniteNumber(wait.timeoutMs ?? 30_000, 'wait.timeoutMs', 1_000, 180_000),
    ),
    settleMs: Math.round(
      requireFiniteNumber(wait.settleMs ?? 100, 'wait.settleMs', 0, 10_000),
    ),
    failOnMapError: wait.failOnMapError !== false,
  };
}

function normalizeSources(sources) {
  if (!Array.isArray(sources) || sources.length === 0) {
    throw new Error('sources must contain at least one provenance record');
  }
  const normalized = sources.map((source, index) => {
    if (!isPlainObject(source)) {
      throw new Error(`sources[${index}] must be an object`);
    }
    const role = requireString(source.role, `sources[${index}].role`);
    if (!SOURCE_ROLES.has(role)) {
      throw new Error(`sources[${index}].role is unsupported: ${role}`);
    }
    const kind = requireString(source.kind, `sources[${index}].kind`);
    if (!SOURCE_KINDS.has(kind)) {
      throw new Error(`sources[${index}].kind is unsupported: ${kind}`);
    }
    const accessedAt = requireString(
      source.accessedAt,
      `sources[${index}].accessedAt`,
    );
    if (Number.isNaN(Date.parse(accessedAt))) {
      throw new Error(`sources[${index}].accessedAt must be an ISO-8601 date`);
    }
    const sourceId = requireString(source.sourceId, `sources[${index}].sourceId`);
    if (!/^[a-z][a-z0-9_-]{2,}$/u.test(sourceId)) {
      throw new Error(`sources[${index}].sourceId has an invalid format`);
    }
    const result = {
      sourceId,
      kind,
      role,
      locator: requireString(source.locator, `sources[${index}].locator`),
      accessBasis: requireString(
        source.accessBasis,
        `sources[${index}].accessBasis`,
      ),
      license: requireString(source.license, `sources[${index}].license`),
      crs: requireString(source.crs, `sources[${index}].crs`),
    };
    result.accessedAt = new Date(accessedAt).toISOString();
    for (const key of ['sensor', 'acquiredAt', 'resolution', 'notes']) {
      if (source[key] !== undefined) {
        result[key] = requireString(source[key], `sources[${index}].${key}`);
      }
    }
    if (source.sha256 !== undefined) {
      const digest = requireString(source.sha256, `sources[${index}].sha256`)
        .replace(/^sha256:/u, '')
        .toLowerCase();
      if (!/^[a-f0-9]{64}$/u.test(digest)) {
        throw new Error(`sources[${index}].sha256 must be a SHA-256 digest`);
      }
      result.sha256 = digest;
    }
    return result;
  });
  if (!normalized.some((source) => source.role === 'analysis')) {
    throw new Error('sources must include an analysis source used by the renderer');
  }
  return normalized;
}

function normalizeCustomLayerModules(modules = []) {
  if (!Array.isArray(modules)) {
    throw new Error('customLayerModules must be an array');
  }
  return modules.map((modulePath, index) =>
    requireString(modulePath, `customLayerModules[${index}]`),
  );
}

function normalizeNetworkPolicy(policy) {
  if (!isPlainObject(policy)) {
    throw new Error('networkPolicy must be an object');
  }
  const mode = requireString(policy.mode, 'networkPolicy.mode');
  if (mode !== 'local-only' && mode !== 'allowlist') {
    throw new Error('networkPolicy.mode must be "local-only" or "allowlist"');
  }
  const values = policy.allowedHosts ?? [];
  if (!Array.isArray(values)) {
    throw new Error('networkPolicy.allowedHosts must be an array');
  }
  const allowedHosts = [...new Set(values.map((value, index) => {
    const host = requireString(value, `networkPolicy.allowedHosts[${index}]`)
      .toLowerCase();
    if (
      host.includes('/') ||
      host.includes(':') ||
      host === 'localhost' ||
      host === '127.0.0.1'
    ) {
      throw new Error(
        `networkPolicy.allowedHosts[${index}] must be a remote hostname without scheme, port, or path`,
      );
    }
    return host;
  }))];
  if (mode === 'local-only' && allowedHosts.length > 0) {
    throw new Error('local-only networkPolicy cannot declare allowedHosts');
  }
  if (mode === 'allowlist' && allowedHosts.length === 0) {
    throw new Error('allowlist networkPolicy requires at least one allowedHost');
  }
  return {mode, allowedHosts};
}

function assertUrlAllowed(url, policy, label) {
  const host = new URL(url).hostname.toLowerCase();
  if (policy.mode !== 'allowlist' || !policy.allowedHosts.includes(host)) {
    throw new Error(`${label} host is not authorized by networkPolicy: ${host}`);
  }
}

export function validateRenderJob(value) {
  if (!isPlainObject(value)) {
    throw new Error('render job must be a JSON object');
  }
  if (value.schemaVersion !== '1.0') {
    throw new Error('schemaVersion must be "1.0"');
  }
  if (value.mode !== 'maplibre-style') {
    throw new Error('mode must be "maplibre-style"');
  }
  const disclosureClass = requireString(value.disclosureClass, 'disclosureClass');
  if (!DISCLOSURE_CLASSES.has(disclosureClass)) {
    throw new Error(`unsupported disclosureClass: ${disclosureClass}`);
  }
  const coordinatePrecision = requireString(
    value.coordinatePrecision,
    'coordinatePrecision',
  );
  if (!COORDINATE_PRECISIONS.has(coordinatePrecision)) {
    throw new Error(`unsupported coordinatePrecision: ${coordinatePrecision}`);
  }
  const networkPolicy = normalizeNetworkPolicy(value.networkPolicy);
  const style = normalizeStyle(value.style);
  const customLayerModules = normalizeCustomLayerModules(
    value.customLayerModules,
  );
  if (style.url) {
    assertUrlAllowed(style.url, networkPolicy, 'style.url');
  }
  for (const [index, modulePath] of customLayerModules.entries()) {
    if (/^https?:\/\//u.test(modulePath)) {
      assertUrlAllowed(
        modulePath,
        networkPolicy,
        `customLayerModules[${index}]`,
      );
    }
  }
  const sources = normalizeSources(value.sources);
  const fallbackScreenshot =
    value.fallbackScreenshot === undefined
      ? null
      : requireString(value.fallbackScreenshot, 'fallbackScreenshot');
  if (
    fallbackScreenshot &&
    !sources.some(
      (source) =>
        source.role === 'manual-reference' &&
        source.locator === fallbackScreenshot,
    )
  ) {
    throw new Error(
      'fallbackScreenshot requires a matching manual-reference source record',
    );
  }
  return {
    schemaVersion: '1.0',
    mode: 'maplibre-style',
    disclosureClass,
    coordinatePrecision,
    networkPolicy,
    attribution: requireString(value.attribution, 'attribution'),
    style,
    camera: normalizeCamera(value.camera),
    viewport: normalizeViewport(value.viewport),
    wait: normalizeWait(value.wait),
    sources,
    customLayerModules,
    fallbackScreenshot,
  };
}

export function resolveJobAsset(jobRoot, relativePath, label) {
  /*
   * Keep browser-served assets inside the job directory.
   * This makes the local HTTP boundary auditable and prevents a render job
   * from turning the asset server into an arbitrary filesystem reader.
   */

  if (/^(?:[a-z]+:)?\/\//iu.test(relativePath)) {
    throw new Error(`${label} must be a local path relative to the job file`);
  }
  const absolute = resolve(jobRoot, relativePath);
  const canonicalRoot = realpathSync(jobRoot);
  const canonical = realpathSync(absolute);
  const rootPrefix = canonicalRoot.endsWith(sep)
    ? canonicalRoot
    : `${canonicalRoot}${sep}`;
  if (canonical !== canonicalRoot && !canonical.startsWith(rootPrefix)) {
    throw new Error(`${label} escapes the job directory`);
  }
  return canonical;
}

export async function loadRenderJob(jobPath) {
  const absolutePath = resolve(jobPath);
  const raw = JSON.parse(await readFile(absolutePath, 'utf8'));
  const job = validateRenderJob(raw);
  const jobRoot = dirname(absolutePath);
  if (job.style.path) {
    resolveJobAsset(jobRoot, job.style.path, 'style.path');
  }
  for (const [index, modulePath] of job.customLayerModules.entries()) {
    if (!/^https?:\/\//u.test(modulePath)) {
      resolveJobAsset(jobRoot, modulePath, `customLayerModules[${index}]`);
    }
  }
  if (job.fallbackScreenshot) {
    resolveJobAsset(jobRoot, job.fallbackScreenshot, 'fallbackScreenshot');
  }
  for (const [index, source] of job.sources.entries()) {
    if (
      source.role === 'analysis' &&
      !/^[a-z][a-z0-9+.-]*:/iu.test(source.locator)
    ) {
      const path = resolveJobAsset(
        jobRoot,
        source.locator,
        `sources[${index}].locator`,
      );
      if (!(await stat(path)).isFile()) {
        throw new Error(`sources[${index}].locator must be a regular file`);
      }
    }
  }
  return {job, jobPath: absolutePath, jobRoot};
}
