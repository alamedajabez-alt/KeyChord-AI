import { ButtonLink } from "../components/ui/Button";

export default function NotFound() {
  return (
    <main className="grid min-h-screen place-items-center px-4 text-center">
      <div className="space-y-3">
        <p className="label">404</p>
        <h1 className="text-2xl">Page not found</h1>
        <ButtonLink to="/dashboard" variant="secondary">Back to dashboard</ButtonLink>
      </div>
    </main>
  );
}
