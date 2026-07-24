import {open, readFile, stat} from 'node:fs/promises';

const PNG_SIGNATURE = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
const MAX_PNG_BYTES = 100 * 1024 * 1024;
const MAX_PNG_PIXELS = 16_777_216;
let crcTable;

function crc32(buffer) {
  if (!crcTable) {
    crcTable = new Uint32Array(256);
    for (let index = 0; index < crcTable.length; index += 1) {
      let value = index;
      for (let bit = 0; bit < 8; bit += 1) {
        value = value & 1 ? 0xedb88320 ^ (value >>> 1) : value >>> 1;
      }
      crcTable[index] = value >>> 0;
    }
  }
  let value = 0xffffffff;
  for (const byte of buffer) {
    value = crcTable[(value ^ byte) & 0xff] ^ (value >>> 8);
  }
  return (value ^ 0xffffffff) >>> 0;
}

export function inspectPngBuffer(buffer) {
  if (!Buffer.isBuffer(buffer) || buffer.length < 24) {
    throw new Error('PNG is truncated');
  }
  if (!buffer.subarray(0, 8).equals(PNG_SIGNATURE)) {
    throw new Error('file is not a PNG');
  }
  if (buffer.toString('ascii', 12, 16) !== 'IHDR') {
    throw new Error('PNG does not start with an IHDR chunk');
  }
  const width = buffer.readUInt32BE(16);
  const height = buffer.readUInt32BE(20);
  if (width === 0 || height === 0) {
    throw new Error('PNG dimensions must be positive');
  }
  if (width * height > MAX_PNG_PIXELS) {
    throw new Error(`PNG exceeds the ${MAX_PNG_PIXELS} pixel safety limit`);
  }
  return {width, height};
}

export function validatePngBuffer(buffer) {
  const dimensions = inspectPngBuffer(buffer);
  let offset = 8;
  let sawHeader = false;
  let sawImageData = false;
  let sawEnd = false;
  while (offset < buffer.length) {
    if (offset + 12 > buffer.length) {
      throw new Error('PNG chunk is truncated');
    }
    const length = buffer.readUInt32BE(offset);
    const typeOffset = offset + 4;
    const dataOffset = typeOffset + 4;
    const crcOffset = dataOffset + length;
    const nextOffset = crcOffset + 4;
    if (nextOffset > buffer.length) {
      throw new Error('PNG chunk data is truncated');
    }
    const type = buffer.toString('ascii', typeOffset, dataOffset);
    const expectedCrc = buffer.readUInt32BE(crcOffset);
    const actualCrc = crc32(buffer.subarray(typeOffset, crcOffset));
    if (expectedCrc !== actualCrc) {
      throw new Error(`PNG ${type} chunk failed CRC validation`);
    }
    if (!sawHeader && type !== 'IHDR') {
      throw new Error('PNG IHDR must be the first chunk');
    }
    if (type === 'IHDR') {
      if (sawHeader || length !== 13) {
        throw new Error('PNG contains an invalid IHDR chunk');
      }
      sawHeader = true;
    } else if (type === 'IDAT') {
      sawImageData = true;
    } else if (type === 'IEND') {
      if (length !== 0 || nextOffset !== buffer.length) {
        throw new Error('PNG contains an invalid IEND chunk');
      }
      sawEnd = true;
    }
    offset = nextOffset;
  }
  if (!sawHeader || !sawImageData || !sawEnd) {
    throw new Error('PNG is missing required chunks');
  }
  return dimensions;
}

export async function inspectPng(path) {
  const handle = await open(path, 'r');
  try {
    const header = Buffer.alloc(24);
    const {bytesRead} = await handle.read(header, 0, header.length, 0);
    return inspectPngBuffer(header.subarray(0, bytesRead));
  } finally {
    await handle.close();
  }
}

export async function readPng(path) {
  const details = await stat(path);
  if (!details.isFile()) {
    throw new Error('screenshot input must be a regular file');
  }
  if (details.size > MAX_PNG_BYTES) {
    throw new Error(`PNG exceeds the ${MAX_PNG_BYTES} byte safety limit`);
  }
  const buffer = await readFile(path);
  return {buffer, ...validatePngBuffer(buffer)};
}
