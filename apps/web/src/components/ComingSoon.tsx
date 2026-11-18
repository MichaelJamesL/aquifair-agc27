import Link from "next/link";

export function ComingSoon({ title }: { title: string }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-2 text-ink-2">
      <h1 className="text-lg font-semibold text-ink">{title}</h1>
      <p>This screen is designed in Figma and comes in the next phase.</p>
      <Link href="/" className="font-medium text-primary">
        Back to the map
      </Link>
    </div>
  );
}
