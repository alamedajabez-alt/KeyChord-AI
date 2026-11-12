import { ButtonLink } from "../components/ui/Button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-start justify-center gap-8 px-4 md:px-8">
      <h1 className="text-[clamp(6rem,30vw,28rem)] leading-[0.8] text-accent">404</h1>
      <p className="text-2xl font-medium tracking-tight md:text-4xl">That page doesn't exist.</p>
      <ButtonLink to="/">Back to home</ButtonLink>
    </div>
  );
}
