/** Local-development transport. No caller-provided posture/capture approval. */
export type Side = 'left' | 'right';
export type PickedVideo = { uri: string; name: string; size?: number; mimeType?: string; file?: Blob };
export type Capabilities = {
  schema_version: 1;
  exercise: 'squat';
  limits: { file_bytes: number; frames: number; width: number; height: number };
};
export type Card = {
  repetition: number; metric: string; field: string | null;
  status: string; observation: number | null; unit: string; reason: string; action: string;
};
export type Cycle = { number: number; source_frames: { start: number; bottom_phase_end: number; end: number } };
export type Candidate = { source_frames: { start: number; end: number }; observed_bottom: number; reason: string };
export type Analysis = {
  schema_version: 1; exercise: 'squat';
  source: { sha256: string; frame_count: number; fps: number | null };
  selection: { side: Side; facing: Side };
  overview: { state: string; primary_action: string; detected_cycles: number; excluded_candidates: number;
    accuracy_status: 'not_validated'; coaching_status: 'pending_validation' };
  feedback: { cards: Card[]; notices: { message: string }[]; actions: { action: string; repetitions: number[] }[] };
  repetitions: Cycle[]; candidates: Candidate[];
};

export class ApiError extends Error {
  constructor(message: string, public code: string) { super(message); }
}

export function normalizeBase(input: string): string {
  const url = new URL(input.trim());
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash) {
    throw new ApiError('Use your trusted API address without credentials or query parameters.', 'invalid_address');
  }
  return url.toString().replace(/\/$/, '');
}

async function requestJson(url: string, options: RequestInit, timeoutMs: number, signal?: AbortSignal): Promise<unknown> {
  const controller = new AbortController();
  let timedOut = false;
  const abort = () => controller.abort();
  signal?.addEventListener('abort', abort, { once: true });
  if (signal?.aborted) controller.abort();
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    let data;
    try { data = await response.json(); }
    catch { throw new ApiError('The server did not return JSON. Check the API address.', 'invalid_response'); }
    if (!response.ok) throw new ApiError(data?.error?.message || `Request failed (${response.status}).`, data?.error?.code || 'request_failed');
    return data;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (timedOut) throw new ApiError('Request timed out. The server may still be processing; check before retrying.', 'timeout');
    if (signal?.aborted) throw new ApiError('Canceled on this device. Server work may still finish.', 'canceled');
    throw new ApiError('Could not reach the API. Check the address, connection and platform network policy.', 'network');
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', abort);
  }
}

export async function connect(base: string, signal?: AbortSignal): Promise<Capabilities> {
  const data = await requestJson(`${normalizeBase(base)}/v1/capabilities`, {}, 10000, signal) as Capabilities;
  if (data?.schema_version !== 1 || data.exercise !== 'squat' || !data.limits ||
      !(['file_bytes', 'frames', 'width', 'height'] as const).every(key => Number.isInteger(data.limits[key]) && data.limits[key] > 0)) {
    throw new ApiError('This API does not expose compatible analysis limits.', 'incompatible_api');
  }
  return data;
}

export function buildUpload(video: PickedVideo, side: Side, facing: Side, platform: 'web' | 'native', limit: number): FormData {
  if (![side, facing].every(value => value === 'left' || value === 'right')) throw new ApiError('Select body side and facing explicitly.', 'selection_required');
  if (video.size !== undefined && (!Number.isFinite(video.size) || video.size <= 0 || video.size > limit)) {
    throw new ApiError('The selected video is empty or exceeds the API file size limit.', 'file_size');
  }
  const type = video.mimeType || 'application/octet-stream';
  if (!['video/mp4', 'video/quicktime', 'application/octet-stream'].includes(type)) throw new ApiError('Select an MP4 or MOV video.', 'file_type');
  const form = new FormData();
  if (platform === 'web') {
    if (!video.file) throw new ApiError('The browser did not provide the selected file. Choose it again.', 'file_missing');
    form.append('video', video.file, video.name);
  } else {
    if (!/^(file|content):\/\//.test(video.uri)) throw new ApiError('A local document URI is required.', 'file_uri');
    // React Native supports URI parts, which DOM FormData typings do not model.
    form.append('video', { uri: video.uri, name: video.name, type } as unknown as Blob);
  }
  form.append('side', side); form.append('facing', facing);
  return form;
}

export async function analyze(base: string, video: PickedVideo, side: Side, facing: Side,
  platform: 'web' | 'native', limit: number, signal?: AbortSignal): Promise<Analysis> {
  const body = buildUpload(video, side, facing, platform, limit);
  const data = await requestJson(`${normalizeBase(base)}/v1/analyses`, { method: 'POST', body }, 180000, signal) as Analysis;
  if (data?.schema_version !== 1 || data.exercise !== 'squat' || data.selection?.side !== side || data.selection?.facing !== facing ||
      data.overview?.coaching_status !== 'pending_validation' || data.overview?.accuracy_status !== 'not_validated' ||
      !Array.isArray(data.repetitions) || !Array.isArray(data.candidates) || !Array.isArray(data.feedback?.cards) ||
      !Array.isArray(data.feedback.notices) || !Array.isArray(data.feedback.actions) || !data.source ||
      typeof data.overview.primary_action !== 'string' ||
      !['retake', 'capture_review', 'measurement_review', 'observation', 'no_complete_cycles'].includes(data.overview.state) ||
      !/^[a-f0-9]{64}$/.test(data.source.sha256) || !Number.isInteger(data.source.frame_count) || data.source.frame_count < 0 ||
      !(data.source.fps === null || (Number.isFinite(data.source.fps) && data.source.fps > 0)) ||
      data.overview.detected_cycles !== data.repetitions.length || data.overview.excluded_candidates !== data.candidates.length) {
    throw new ApiError('The server returned an incompatible or unapproved result contract.', 'invalid_response');
  }
  const frame = (value: number) => Number.isInteger(value) && value >= 0 && value < data.source.frame_count;
  if (data.repetitions.some((item, index) => item.number !== index + 1 || !item.source_frames ||
      !frame(item.source_frames.start) || !frame(item.source_frames.bottom_phase_end) || !frame(item.source_frames.end) ||
      !(item.source_frames.start <= item.source_frames.bottom_phase_end && item.source_frames.bottom_phase_end <= item.source_frames.end)) ||
      data.feedback.cards.some(card => !Number.isInteger(card.repetition) || card.repetition < 1 || card.repetition > data.repetitions.length ||
      typeof card.metric !== 'string' || !(card.field === null || typeof card.field === 'string') || typeof card.action !== 'string' ||
      !(card.observation === null || Number.isFinite(card.observation)))) {
    throw new ApiError('The result contains inconsistent cycle evidence.', 'invalid_response');
  }
  if (data.candidates.some(item => !item.source_frames || !frame(item.source_frames.start) || !frame(item.source_frames.end) ||
      item.source_frames.start > item.source_frames.end || !frame(item.observed_bottom) || typeof item.reason !== 'string') ||
      data.feedback.notices.some(item => typeof item.message !== 'string')) {
    throw new ApiError('The result contains inconsistent candidate evidence.', 'invalid_response');
  }
  return data;
}

export function sourceTime(frame: number, fps: number | null, sourceCount: number): number | null {
  return Number.isInteger(sourceCount) && sourceCount > 0 && Number.isInteger(frame) && frame >= 0 && frame < sourceCount && fps !== null && Number.isFinite(fps) && fps > 0 ? frame / fps : null;
}
