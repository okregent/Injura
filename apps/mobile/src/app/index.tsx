import { useEffect, useRef, useState, type ElementRef } from 'react';
import { ActivityIndicator, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as DocumentPicker from 'expo-document-picker';
import { useVideoPlayer, VideoView, type VideoPlayer } from 'expo-video';

import { analyze, connect, normalizeBase, sourceTime, type Analysis, type Capabilities, type PickedVideo, type Side } from '../lib/api';

function Action({ title, onPress, disabled = false }: { title: string; onPress: () => void; disabled?: boolean }) {
  return <Pressable accessibilityRole="button" accessibilityState={{ disabled }} onPress={onPress} disabled={disabled}
    style={[styles.button, disabled && styles.disabled]}><Text style={styles.buttonText}>{title}</Text></Pressable>;
}

function seekPlayer(player: VideoPlayer, seconds: number) {
  // Expo's native player is an imperative SDK object, not immutable React state.
  player.pause();
  player.currentTime = seconds;
}

export default function AnalysisScreen() {
  const [address, setAddress] = useState(process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000');
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
  const [connectedAddress, setConnectedAddress] = useState('');
  const [video, setVideo] = useState<PickedVideo | null>(null);
  const [side, setSide] = useState<Side | null>(null), [facing, setFacing] = useState<Side | null>(null);
  const [result, setResult] = useState<Analysis | null>(null), [selected, setSelected] = useState<number | null>(null);
  const [busy, setBusy] = useState(false), [message, setMessage] = useState('Connect to your trusted analysis API. No video is sent until you press Analyze.');
  const active = useRef<AbortController | null>(null);
  const generation = useRef(0);
  const pickerAttempt = useRef(0);
  const scroll = useRef<ElementRef<typeof ScrollView> | null>(null);
  const videoOffset = useRef(0);
  const player = useVideoPlayer(video?.uri ?? null, instance => { instance.loop = false; instance.muted = true; });
  useEffect(() => () => { generation.current += 1; pickerAttempt.current += 1; active.current?.abort(); }, []);
  useEffect(() => () => {
    if (Platform.OS === 'web' && video?.uri.startsWith('blob:')) URL.revokeObjectURL(video.uri);
  }, [video]);

  function invalidate() { generation.current += 1; active.current?.abort(); setResult(null); setSelected(null); }
  async function checkConnection() {
    if (active.current) return;
    invalidate(); const revision = generation.current;
    setCapabilities(null); setBusy(true); setMessage('Checking server capabilities…');
    const controller = new AbortController(); active.current = controller;
    try {
      const base = normalizeBase(address), data = await connect(base, controller.signal);
      if (revision !== generation.current) return;
      setConnectedAddress(base); setCapabilities(data); setMessage('Connected. Choose a video and explicitly select body side and facing.');
    } catch (error) { if (revision === generation.current) setMessage(error instanceof Error ? error.message : 'Connection failed.'); }
    finally { if (active.current === controller) active.current = null; if (revision === generation.current) setBusy(false); }
  }
  async function pickVideo() {
    if (active.current) return;
    const attempt = ++pickerAttempt.current;
    try {
      const picked = await DocumentPicker.getDocumentAsync({ type: ['video/mp4', 'video/quicktime'], multiple: false, copyToCacheDirectory: true, base64: false });
      if (picked.canceled || attempt !== pickerAttempt.current) return;
      player.pause(); invalidate(); setVideo(picked.assets[0]); setSide(null); setFacing(null);
      setMessage('Video selected locally. Select body side and facing before uploading.');
    } catch (error) { if (attempt === pickerAttempt.current) setMessage(error instanceof Error ? error.message : 'Could not choose a video.'); }
  }
  async function upload() {
    if (active.current || !video || !side || !facing || !capabilities || !connectedAddress) return;
    invalidate(); const revision = generation.current;
    setBusy(true); setMessage(`Uploading to ${connectedAddress} and analyzing…`);
    const controller = new AbortController(); active.current = controller;
    try {
      const data = await analyze(connectedAddress, video, side, facing, Platform.OS === 'web' ? 'web' : 'native', capabilities.limits.file_bytes, controller.signal);
      if (revision !== generation.current) return;
      setResult(data); setMessage('Analysis complete. Capture conditions and coaching remain unapproved.');
    } catch (error) { if (revision === generation.current) setMessage(error instanceof Error ? error.message : 'Analysis failed.'); }
    finally { if (active.current === controller) active.current = null; if (revision === generation.current) setBusy(false); }
  }
  function seek(frame: number) {
    if (!result) return;
    const seconds = sourceTime(frame, result.source.fps, result.source.frame_count);
    if (seconds === null) { setMessage('Time navigation requires valid FPS/source-frame information.'); return; }
    if (player.status !== 'readyToPlay' || !Number.isFinite(player.duration) || seconds >= player.duration) {
      setMessage('Video metadata is not ready or the requested position exceeds its duration.'); return;
    }
    try { seekPlayer(player, seconds); setMessage(`Approximate source frame ${frame}; reported-FPS seeking is not frame-exact.`); }
    catch { setMessage('This player could not seek to the requested position.'); }
  }
  const cycle = selected !== null ? result?.repetitions[selected] : null;
  const cards = cycle ? result?.feedback.cards.filter(card => card.repetition === cycle.number) : [];
  function chooseCycle(index: number) {
    if (!result || index < 0 || index >= result.repetitions.length) return;
    setSelected(index); seek(result.repetitions[index].source_frames.start);
    const revision = generation.current;
    requestAnimationFrame(() => { if (revision === generation.current) scroll.current?.scrollTo({ y: Math.max(0, videoOffset.current - 12), animated: true }); });
  }

  return <SafeAreaView style={styles.safe}>
    <ScrollView ref={scroll} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Injura</Text><Text style={styles.muted}>Mobile development client · squat measurements, not a posture score</Text>
      <View style={styles.panel}>
        <Text style={styles.heading}>Your analysis server</Text>
        <TextInput accessibilityLabel="API address" style={styles.input} value={address} editable={!busy} autoCapitalize="none" autoCorrect={false}
          onChangeText={text => { invalidate(); setAddress(text); setCapabilities(null); setConnectedAddress(''); }} />
        <Text style={styles.muted}>On a phone, 127.0.0.1 refers to that phone. Use your trusted reachable API; this app does not expose or deploy a server.</Text>
        <Action title="Connect to API" onPress={checkConnection} disabled={busy} />
        {capabilities && <Text style={styles.text}>Limit: {Math.floor(capabilities.limits.file_bytes / 1024 / 1024)} MiB · {capabilities.limits.frames} frames</Text>}
      </View>
      <View style={styles.panel}>
        <Text style={styles.heading}>Recording</Text>
        <Action title="Choose video" onPress={pickVideo} disabled={busy} />
        <Text style={styles.text}>{video?.name || 'No video selected. Files are not uploaded automatically.'}</Text>
        <Text style={styles.text}>Body side to measure: {side || 'not selected'}</Text>
        <View style={styles.row}>{(['left', 'right'] as Side[]).map(value => <Action key={value} title={`Measure ${value}`} disabled={busy} onPress={() => { invalidate(); setSide(value); }} />)}</View>
        <Text style={styles.text}>Person faces: {facing || 'not selected'}</Text>
        <View style={styles.row}>{(['left', 'right'] as Side[]).map(value => <Action key={value} title={`Faces ${value}`} disabled={busy} onPress={() => { invalidate(); setFacing(value); }} />)}</View>
        <Action title="Analyze selected video" onPress={upload} disabled={busy || !video || !side || !facing || !capabilities} />
        <Text style={styles.muted}>This sends the chosen file to the connected API. Server uploads are temporary; your original and any device-picker cache remain under your control.</Text>
      </View>
      {busy && <ActivityIndicator accessibilityLabel="Request in progress" color="#a7e2ca" />}
      {busy && <Action title="Stop waiting on this device" onPress={() => {
        generation.current += 1; active.current?.abort(); active.current = null; setBusy(false);
        setMessage('Stopped waiting on this device. The server may still be processing; check before retrying.');
      }} />}
      <Text style={styles.message} accessibilityLiveRegion="polite">{message}</Text>
      {result && <View style={styles.panel}>
        <Text style={styles.heading}>Session result</Text>
        <Text style={styles.text}>{result.overview.primary_action}</Text>
        <Text style={styles.text}>Detected cycles: {result.overview.detected_cycles} · Excluded candidates: {result.overview.excluded_candidates}</Text>
        <Text style={styles.muted}>Accuracy not validated. Coaching pending validation. Differences and detector outputs are not technique judgments.</Text>
        <View style={styles.row}>{result.repetitions.map((item, index) => <Action key={item.number} title={`Cycle ${item.number}`} onPress={() => chooseCycle(index)} />)}</View>
        {!!result.candidates.length && <Text style={styles.heading}>Excluded review candidates</Text>}
        {result.candidates.map((item, index) => <Text key={index} style={styles.text}>Candidate {index + 1}: {item.reason} No measurements assigned.</Text>)}
        {result.feedback.notices.map((notice, index) => <Text key={index} style={styles.muted}>{notice.message}</Text>)}
      </View>}
      {video && <View style={styles.panel} onLayout={event => { videoOffset.current = event.nativeEvent.layout.y; }}>
        <Text style={styles.heading}>Video review</Text>
        <VideoView player={player} style={styles.video} contentFit="contain" nativeControls fullscreenOptions={{ enable: true }} />
        <Text style={styles.muted}>Reported-FPS time navigation is approximate, not frame-exact. The mobile client does not render the web joint overlay.</Text>
        {cycle && <View>
          <Text style={styles.heading}>Cycle {cycle.number}</Text>
          <Text style={styles.text}>Original source frames {cycle.source_frames.start}–{cycle.source_frames.end}</Text>
          <View style={styles.row}>
            <Action title="Previous cycle" disabled={selected === null || selected <= 0} onPress={() => chooseCycle((selected ?? 0) - 1)} />
            <Action title="Next cycle" disabled={!result || selected === null || selected >= result.repetitions.length - 1} onPress={() => chooseCycle((selected ?? 0) + 1)} />
          </View>
          <View style={styles.row}>
            <Action title="Start" onPress={() => seek(cycle.source_frames.start)} />
            <Action title="Bottom phase end" onPress={() => seek(cycle.source_frames.bottom_phase_end)} />
            <Action title="End" onPress={() => seek(cycle.source_frames.end)} />
          </View>
          <Text style={styles.muted}>BOTTOM-phase end is not necessarily the deepest posture.</Text>
          {cards?.map(card => <Text key={`${card.metric}:${card.field}`} style={styles.text}>
            {card.metric.replaceAll('_', ' ')}{card.field ? ` / ${card.field.replaceAll('_', ' ')}` : ''}: {card.observation === null ? 'not shown' : `${card.observation} ${card.unit}`} · {card.action}
          </Text>)}
        </View>}
      </View>}
    </ScrollView>
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#111820' }, content: { padding: 20, gap: 16, maxWidth: 850, width: '100%', alignSelf: 'center' },
  title: { fontSize: 34, fontWeight: '700', color: '#e5eaf1' }, heading: { fontSize: 20, fontWeight: '600', color: '#e5eaf1', marginVertical: 8 },
  text: { color: '#e5eaf1', marginVertical: 7, lineHeight: 22 }, muted: { color: '#afbdcd', lineHeight: 21, marginVertical: 5 },
  panel: { backgroundColor: '#1b2531', padding: 18, borderRadius: 14, borderColor: '#354658', borderWidth: 1 },
  input: { backgroundColor: '#111820', color: '#e5eaf1', borderColor: '#5c7184', borderWidth: 1, borderRadius: 7, padding: 12, marginVertical: 8 },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginVertical: 8 }, button: { backgroundColor: '#a7e2ca', padding: 12, borderRadius: 7, alignItems: 'center', marginVertical: 4 },
  buttonText: { color: '#10271f', fontWeight: '600' }, disabled: { opacity: .45 }, message: { color: '#d6e6f5', lineHeight: 23 },
  video: { width: '100%', height: 280, marginVertical: 14 },
});
