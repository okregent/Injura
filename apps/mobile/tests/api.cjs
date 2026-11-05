const { test } = require('node:test');
const assert = require('node:assert/strict');
const { normalizeBase, buildUpload, connect, analyze, sourceTime } = require('../.test-build/src/lib/api.js');

test('API addresses do not embed credentials or query data', () => {
  assert.equal(normalizeBase(' http://127.0.0.1:8000/ '), 'http://127.0.0.1:8000');
  for (const value of ['ftp://server', 'https://user:pass@server', 'https://server?token=x']) assert.throws(() => normalizeBase(value));
});

test('web upload retains the file and explicit selection without manual multipart headers', () => {
  const form = buildUpload({ uri: 'blob:fixture', name: 'test.mp4', size: 4, mimeType: 'video/mp4', file: new Blob(['test']) }, 'left', 'right', 'web', 10);
  assert.equal(form.get('side'), 'left'); assert.equal(form.get('facing'), 'right');
  assert.equal(form.get('video').size, 4);
  assert.throws(() => buildUpload({ uri: '', name: '', size: 11 }, 'left', 'right', 'web', 10), /limit/);
  assert.throws(() => buildUpload({ uri: '', name: '', size: 1 }, 'auto', 'right', 'web', 10), /explicitly/);
});

test('native upload uses a local URI file part and rejects remote file URIs', () => {
  const original = global.FormData;
  global.FormData = class { fields = []; append(key, value) { this.fields.push([key, value]); } };
  try {
    const form = buildUpload({ uri: 'file:///cache/video.mp4', name: 'video.mp4', size: 2 }, 'right', 'left', 'native', 10);
    assert.equal(form.fields[0][1].uri, 'file:///cache/video.mp4');
    assert.throws(() => buildUpload({ uri: 'https://private/file', name: 'x.mp4' }, 'left', 'right', 'native', 10), /local document/);
  } finally { global.FormData = original; }
});

test('capabilities require all limits and propagate busy errors', async () => {
  const original = global.fetch;
  try {
    global.fetch = async () => ({ ok: true, json: async () => ({ schema_version: 1, exercise: 'squat', limits: { file_bytes: 10 } }) });
    await assert.rejects(() => connect('http://localhost:8000'), /compatible/);
    global.fetch = async () => ({ ok: false, json: async () => ({ error: { code: 'analysis_busy', message: 'Retry later.' } }) });
    await assert.rejects(() => connect('http://localhost:8000'), error => error.code === 'analysis_busy');
  } finally { global.fetch = original; }
});

function response() {
  return { schema_version: 1, exercise: 'squat', selection: { side: 'left', facing: 'right' },
    source: { sha256: 'a'.repeat(64), frame_count: 10, fps: 24 },
    overview: { state: 'no_complete_cycles', primary_action: 'Review source.', detected_cycles: 0, excluded_candidates: 0, coaching_status: 'pending_validation', accuracy_status: 'not_validated' },
    feedback: { cards: [], notices: [], actions: [] }, repetitions: [], candidates: [] };
}

test('analysis forwards multipart data and preserves pending validation', async () => {
  const original = global.fetch;
  const asset = { uri: 'blob:x', name: 'x.mp4', size: 1, file: new Blob(['x']) };
  try {
    global.fetch = async (url, options) => {
      assert.equal(url, 'http://localhost:8000/v1/analyses');
      assert.equal(options.body.get('side'), 'left'); assert.equal(options.headers, undefined);
      return { ok: true, json: async () => response() };
    };
    assert.equal((await analyze('http://localhost:8000', asset, 'left', 'right', 'web', 10)).overview.coaching_status, 'pending_validation');
    global.fetch = async () => ({ ok: true, json: async () => ({ ...response(), selection: { side: 'right', facing: 'right' } }) });
    await assert.rejects(() => analyze('http://localhost:8000', asset, 'left', 'right', 'web', 10), /incompatible/);
  } finally { global.fetch = original; }
});

test('cancellation is explicit and source seeking never guesses unknown FPS', async () => {
  const original = global.fetch, controller = new AbortController(); controller.abort();
  try {
    global.fetch = async () => { throw Error('aborted'); };
    await assert.rejects(() => connect('http://localhost:8000', controller.signal), error => error.code === 'canceled');
  } finally { global.fetch = original; }
  assert.equal(sourceTime(24, 24, 100), 1);
  for (const fps of [null, 0, NaN]) assert.equal(sourceTime(24, fps, 100), null);
  assert.equal(sourceTime(100, 24, 100), null);
});

test('unapproved response claims and invalid source evidence fail closed', async () => {
  const original = global.fetch;
  const asset = { uri: 'blob:x', name: 'x.mp4', size: 1, file: new Blob(['x']) };
  try {
    for (const change of [data => { data.overview.coaching_status = 'approved'; },
      data => { data.source.fps = -1; }, data => { data.overview.primary_action = {}; }]) {
      const data = response(); change(data);
      global.fetch = async () => ({ ok: true, json: async () => data });
      await assert.rejects(() => analyze('http://localhost:8000', asset, 'left', 'right', 'web', 10), error => error.code === 'invalid_response');
    }
  } finally { global.fetch = original; }
});

test('non-JSON and timeout failures stay actionable without silent retries', async () => {
  const originalFetch = global.fetch, originalTimeout = global.setTimeout;
  try {
    global.fetch = async () => ({ ok: true, json: async () => { throw Error('not json'); } });
    await assert.rejects(() => connect('http://localhost:8000'), error => error.code === 'invalid_response');
    global.setTimeout = callback => { callback(); return 0; };
    global.fetch = async () => { throw Error('timeout'); };
    await assert.rejects(() => connect('http://localhost:8000'), error => error.code === 'timeout');
  } finally { global.fetch = originalFetch; global.setTimeout = originalTimeout; }
});
