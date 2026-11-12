import { ButtonLink } from "../components/ui/Button";

const FEATURES = [
  { title: "Timestamped chords", body: "Upload a song and get a chord timeline you can click to seek." },
  { title: "Piano voicings", body: "See suggested left- and right-hand voicings on a keyboard, labelled as suggestions." },
  { title: "Key and transpose", body: "Detect the key with alternatives, then transpose without touching the original analysis." },
];
const STEPS = [
  { n: "1", title: "Upload", body: "Drop in an MP3, WAV, M4A or FLAC up to 50 MB." },
  { n: "2", title: "Analyze", body: "KeyChord estimates the key and timestamps each chord change." },
  { n: "3", title: "Play", body: "Click the timeline to seek, then follow the voicings on the keys." },
];

const WHITE_COUNT = 14;
const LIT = [0, 2, 4, 6]; // C E G B → Cmaj7
const BLACK_AFTER = [0, 1, 3, 4, 5, 7, 8, 10, 11, 12]; // white-key index each black key follows

function PanelKeyboard() {
  const w = 100 / WHITE_COUNT;
  return (
    <div aria-hidden className="rise origin-center" style={{ width: 1000, transform: "perspective(1700px) rotateX(56deg) rotateZ(-30deg)" }}>
      <div className="border border-[#E6E1D6] bg-[#CFCBC2] p-8 text-bg">
        <div className="mb-6 flex items-end justify-between">
          <span className="text-sm font-medium uppercase tracking-[0.25em]">KeyChord AI</span>
          <span className="text-5xl font-medium tracking-tight" style={{ fontStretch: "125%" }}>Cmaj7</span>
        </div>
        <div className="relative flex h-56 border border-bg bg-[#F1EDE4]">
          {Array.from({ length: WHITE_COUNT }, (_, i) => (
            <div key={i} className={`flex-1 border-r border-[#BDB8AD] last:border-r-0 ${LIT.includes(i) ? "bg-accent" : ""}`} />
          ))}
          {BLACK_AFTER.map((i) => (
            <div key={i} className="absolute top-0 h-[62%] bg-bg" style={{ left: `${(i + 1) * w - w * 0.3}%`, width: `${w * 0.6}%` }} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function Landing() {
  return (
    <>
      <section className="relative flex min-h-[100svh] flex-col justify-end overflow-hidden px-6 pb-12 md:px-[4.5vw]">
        <div className="pointer-events-none absolute left-[14%] top-[16%] origin-top-left scale-[.5] sm:scale-[.7] lg:left-[24%] lg:scale-100">
          <PanelKeyboard />
        </div>
        <div className="relative z-10">
          <p className="label mb-6">KeyChord AI</p>
          <h1 className="max-w-[12ch] text-[clamp(2.75rem,6.4vw,6rem)] leading-[0.95]">
            Hear the song.<br />See the chords.<br /><span className="text-accent">Play them.</span>
          </h1>
          <p className="mt-6 max-w-xl text-lg text-accent md:text-xl">
            Chord timelines and piano voicings, built for worship teams and working keyboardists.
          </p>
          <div className="mt-8 flex flex-wrap gap-4">
            <ButtonLink to="/upload">Upload a song</ButtonLink>
            <ButtonLink to="/dashboard" variant="secondary">Open dashboard</ButtonLink>
          </div>
          <p className="label mt-12">Scroll</p>
        </div>
      </section>

      <section className="px-6 py-24 md:px-[4.5vw] md:py-32">
        <h2 className="mb-14 max-w-3xl text-4xl md:text-6xl">Everything you need to learn a song by ear.</h2>
        <div className="grid border-t border-line md:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="border-b border-line py-8 md:border-b-0 md:border-r md:px-8 md:py-10 md:first:pl-0 md:last:border-r-0">
              <h3 className="mb-3 text-2xl">{f.title}</h3>
              <p className="max-w-sm text-lg text-mutedfg">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-line px-6 py-24 md:px-[4.5vw] md:py-32">
        <h2 className="mb-14 text-4xl md:text-6xl">From file to keys in three steps.</h2>
        <ol className="grid gap-12 md:grid-cols-3">
          {STEPS.map((s) => (
            <li key={s.n}>
              <span className="mb-5 grid h-10 w-10 place-items-center border border-accent text-accent">{s.n}</span>
              <h3 className="mb-3 text-2xl">{s.title}</h3>
              <p className="max-w-sm text-lg text-mutedfg">{s.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="border-t border-line px-6 py-24 md:px-[4.5vw] md:py-32">
        <h2 className="mb-8 text-[clamp(2.75rem,6vw,5.5rem)] leading-none">Start with one song.</h2>
        <ButtonLink to="/upload" size="lg">Upload a song</ButtonLink>
      </section>
    </>
  );
}
