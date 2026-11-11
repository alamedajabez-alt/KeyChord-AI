/** Decode audio in the browser and reduce it to `buckets` normalized peak values (0..1) for drawing a waveform. */
export async function computePeaks(data: ArrayBuffer, buckets = 600): Promise<number[]> {
  const Ctx = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!Ctx) throw new Error("Web Audio is not supported");
  const ctx = new Ctx();
  try {
    const buffer = await ctx.decodeAudioData(data);
    const peaks = new Array<number>(buckets).fill(0);
    const perBucket = buffer.length / buckets;
    const stride = Math.max(1, Math.floor(perBucket / 256)); // sampling a subset per bucket is plenty for drawing
    for (let c = 0; c < buffer.numberOfChannels; c++) {
      const samples = buffer.getChannelData(c);
      for (let b = 0; b < buckets; b++) {
        const end = Math.min(samples.length, Math.floor((b + 1) * perBucket));
        let max = peaks[b];
        for (let i = Math.floor(b * perBucket); i < end; i += stride) {
          const v = Math.abs(samples[i]);
          if (v > max) max = v;
        }
        peaks[b] = max;
      }
    }
    const top = Math.max(...peaks, 1e-6);
    return peaks.map((p) => p / top);
  } finally {
    void ctx.close(); // release the decoded buffer's audio context
  }
}
