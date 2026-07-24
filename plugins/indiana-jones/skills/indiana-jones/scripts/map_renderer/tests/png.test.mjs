import assert from 'node:assert/strict';
import {test} from 'node:test';
import {inspectPngBuffer} from '../src/png.mjs';

test('reads PNG dimensions without decoding image pixels', () => {
  const header = Buffer.alloc(24);
  Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]).copy(header, 0);
  header.writeUInt32BE(13, 8);
  header.write('IHDR', 12, 'ascii');
  header.writeUInt32BE(640, 16);
  header.writeUInt32BE(480, 20);
  assert.deepEqual(inspectPngBuffer(header), {width: 640, height: 480});
});

test('rejects non-PNG input', () => {
  assert.throws(
    () => inspectPngBuffer(Buffer.alloc(24)),
    /file is not a PNG/u,
  );
});
