import { AudioWaveform, KeyRound, Piano, Upload } from "lucide-react";
import { ButtonLink } from "../components/ui/Button";
import { Card } from "../components/ui/Card";

const FEATURES = [
  { icon: AudioWaveform, title: "Timestamped chords", body: "Upload a song and get a chord timeline you can click to seek." },
  { icon: Piano, title: "Piano voicings", body: "See suggested left- and right-hand voicings on a keyboard, labelled as suggestions." },
  { icon: KeyRound, title: "Key & transpose", body: "Detect the key with alternatives, then transpose without touching the original analysis." },
];

export default function Landing() {
  return (
    <>
      <section className="mx-auto max-w-6xl px-4 pb-16 pt-12 sm:px-6 sm:pt-20">
        <p className="label mb-4">For keyboard players</p>
        <h1 className="max-w-3xl text-display">Hear a song. See the chords. Play it on the keys.</h1>
        <p className="mt-5 max-w-xl text-lg text-slate-400">
          KeyChord AI turns song audio into timestamped chords and piano voicings, built for worship teams and
          working keyboardists.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <ButtonLink to="/upload"><Upload className="h-4 w-4" aria-hidden /> Upload a song</ButtonLink>
          <ButtonLink to="/dashboard" variant="secondary">Open dashboard</ButtonLink>
        </div>
      </section>
      <section className="mx-auto grid max-w-6xl gap-4 px-4 pb-20 sm:px-6 md:grid-cols-3">
        {FEATURES.map(({ icon: Icon, title, body }) => (
          <Card key={title} className="p-5">
            <Icon className="mb-3 h-5 w-5 text-accent-soft" aria-hidden />
            <h3 className="mb-1 text-base">{title}</h3>
            <p className="text-sm text-slate-400">{body}</p>
          </Card>
        ))}
      </section>
    </>
  );
}
