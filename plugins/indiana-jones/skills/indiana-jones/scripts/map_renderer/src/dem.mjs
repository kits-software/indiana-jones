import {deflateSync} from 'node:zlib';

const PNG_SIGNATURE = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
let crcTable;

function buildCrcTable() {
  const table = new Uint32Array(256);
  for (let index = 0; index < table.length; index += 1) {
    let value = index;
    for (let bit = 0; bit < 8; bit += 1) {
      value = value & 1 ? 0xedb88320 ^ (value >>> 1) : value >>> 1;
    }
    table[index] = value >>> 0;
  }
  return table;
}

function crc32(buffer) {
  if (!crcTable) {
    crcTable = buildCrcTable();
  }
  let value = 0xffffffff;
  for (const byte of buffer) {
    value = crcTable[(value ^ byte) & 0xff] ^ (value >>> 8);
  }
  return (value ^ 0xffffffff) >>> 0;
}

function pngChunk(type, data) {
  const typeBuffer = Buffer.from(type, 'ascii');
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length);
  const checksum = Buffer.alloc(4);
  checksum.writeUInt32BE(crc32(Buffer.concat([typeBuffer, data])));
  return Buffer.concat([length, typeBuffer, data, checksum]);
}

function encodeMapboxHeight(heightM) {
  const encoded = Math.max(0, Math.min(0xffffff, Math.round((heightM + 10_000) * 10)));
  return [(encoded >>> 16) & 0xff, (encoded >>> 8) & 0xff, encoded & 0xff];
}

export function syntheticDemPng(configuration = {}) {
  /*
   * Produce a deterministic Mapbox Terrain RGB hill for offline regression.
   * Radial and directional components make terrain displacement, lighting,
   * and tile orientation observable without any external elevation source.
   */

  const {
    size = 256,
    hillHeightM = 720,
    hillFalloff = 4.2,
    ridgeHeightM = 120,
    ridgeFrequency = 3,
    ridgeFalloff = 3,
  } = configuration;
  const stride = 1 + size * 3;
  const rows = Buffer.alloc(stride * size);
  for (let y = 0; y < size; y += 1) {
    const rowOffset = y * stride;
    rows[rowOffset] = 0;
    for (let x = 0; x < size; x += 1) {
      const normalizedX = (x + 0.5) / size * 2 - 1;
      const normalizedY = (y + 0.5) / size * 2 - 1;
      const radiusSquared =
        normalizedX * normalizedX + normalizedY * normalizedY;
      const hill = hillHeightM * Math.exp(-hillFalloff * radiusSquared);
      const ridge =
        ridgeHeightM *
        Math.sin(normalizedX * Math.PI * ridgeFrequency) *
        Math.exp(-ridgeFalloff * normalizedY * normalizedY);
      const [red, green, blue] = encodeMapboxHeight(hill + ridge);
      const offset = rowOffset + 1 + x * 3;
      rows[offset] = red;
      rows[offset + 1] = green;
      rows[offset + 2] = blue;
    }
  }
  const header = Buffer.alloc(13);
  header.writeUInt32BE(size, 0);
  header.writeUInt32BE(size, 4);
  header[8] = 8;
  header[9] = 2;
  return Buffer.concat([
    PNG_SIGNATURE,
    pngChunk('IHDR', header),
    pngChunk('IDAT', deflateSync(rows, {level: 9})),
    pngChunk('IEND', Buffer.alloc(0)),
  ]);
}
