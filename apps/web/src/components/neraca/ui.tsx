import type { ButtonHTMLAttributes, ReactNode } from "react";
import type { ProvenanceLabel } from "@/lib/api";

export const cn = (...values: (string | false | null | undefined)[]) =>
  values.filter(Boolean).join(" ");

const BADGE_TONE: Record<string, string> = {
  blue: "bg-blue-50 text-blue-700",
  amber: "bg-amber-100 text-amber-800",
  green: "bg-green-100 text-green-700",
  red: "bg-red-100 text-red-700",
  purple: "bg-purple-100 text-purple-700",
  gray: "bg-subtle text-ink-2",
  dark: "bg-navy-900 text-white",
};

export type BadgeTone = keyof typeof BADGE_TONE;

export function Badge({
  children,
  tone = "gray",
  dot = false,
  className,
}: {
  children: ReactNode;
  tone?: BadgeTone;
  dot?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-[22px] items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 text-[11px] font-medium leading-4",
        BADGE_TONE[tone],
        className,
      )}
    >
      {dot && <span className="size-1.5 rounded-full bg-current opacity-70" />}
      {children}
    </span>
  );
}

const LABEL_TONE: Record<ProvenanceLabel, BadgeTone> = {
  OFFICIAL: "green",
  MEASURED: "blue",
  TESTED: "blue",
  CALCULATED: "gray",
  WEAK: "amber",
  SCENARIO: "purple",
  MISSING: "red",
};

const LABEL_TEXT: Record<ProvenanceLabel, string> = {
  OFFICIAL: "Official",
  MEASURED: "Measured",
  TESTED: "Validated",
  CALCULATED: "Calculated",
  WEAK: "Weak source",
  SCENARIO: "Scenario",
  MISSING: "Missing",
};

export function LabelBadge({
  label,
  className,
  dot = true,
}: {
  label: ProvenanceLabel;
  className?: string;
  dot?: boolean;
}) {
  return (
    <Badge tone={LABEL_TONE[label]} dot={dot} className={className}>
      {LABEL_TEXT[label]}
    </Badge>
  );
}

export function CodeTag({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex h-[18px] items-center rounded-[3px] border border-line-strong px-[5px] font-mono text-[10px] leading-[14px] text-ink-2">
      {children}
    </span>
  );
}

export function Card({
  children,
  className,
  padded = true,
}: {
  children: ReactNode;
  className?: string;
  padded?: boolean;
}) {
  return (
    <section
      className={cn(
        "rounded-xl border border-line bg-surface",
        padded && "p-5",
        className,
      )}
    >
      {children}
    </section>
  );
}

export function SectionTitle({
  children,
  right,
  className,
}: {
  children: ReactNode;
  right?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <h2 className="font-sans text-[18px] font-semibold leading-6 text-ink">{children}</h2>
      <div className="h-px flex-1 bg-line" />
      {right}
    </div>
  );
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "dark";
  size?: "sm" | "md";
  icon?: ReactNode;
};

const BUTTON_VARIANT = {
  primary: "bg-blue-700 text-white hover:bg-primary-hover border border-blue-700",
  secondary: "bg-surface text-ink border border-line-strong hover:bg-bg",
  ghost: "bg-transparent text-ink-2 hover:bg-subtle border border-transparent",
  dark: "bg-navy-900 text-white hover:bg-navy-800 border border-navy-900",
};

const BUTTON_SIZE = {
  sm: "h-8 px-3 text-[12px]",
  md: "h-9 px-4 text-[13px]",
};

export function Button({
  variant = "secondary",
  size = "sm",
  icon,
  children,
  className,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-md font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        BUTTON_VARIANT[variant],
        BUTTON_SIZE[size],
        className,
      )}
      {...rest}
    >
      {icon}
      {children}
    </button>
  );
}

export function RangeBar({
  low,
  high,
  ceiling,
  tone = "amber",
  className,
}: {
  low: number | null;
  high: number | null;
  ceiling: number;
  tone?: "amber" | "blue" | "green";
  className?: string;
}) {
  const safeCeiling = ceiling > 0 ? ceiling : 1;
  const left = Math.max(0, Math.min(100, ((low ?? 0) / safeCeiling) * 100));
  const right = Math.max(0, Math.min(100, ((high ?? 0) / safeCeiling) * 100));
  const width = Math.max(1.5, right - left);
  const colour =
    tone === "blue" ? "bg-blue-500" : tone === "green" ? "bg-green-700" : "bg-amber-500";
  return (
    <div className={cn("h-1.5 overflow-hidden rounded-full bg-subtle", className)}>
      <div
        className={cn("h-full rounded-full", colour)}
        style={{ marginLeft: `${left}%`, width: `${width}%` }}
      />
    </div>
  );
}

export function Stat({
  label,
  value,
  unit,
  sub,
  badge,
  className,
}: {
  label: string;
  value: ReactNode;
  unit?: string;
  sub?: ReactNode;
  badge?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("rounded-xl border border-line bg-surface p-4", className)}>
      <p className="text-[12px] font-medium leading-4 text-ink-2">{label}</p>
      <div className="mt-3 flex items-baseline gap-2">
        <p className="font-display text-[30px] leading-8 tracking-[-0.6px] text-ink">{value}</p>
        {unit && <p className="text-[12px] text-ink-3">{unit}</p>}
      </div>
      {sub && <div className="mt-2 text-[12px] leading-4 text-ink-3">{sub}</div>}
      {badge && <div className="mt-3">{badge}</div>}
    </div>
  );
}

export function InfoNote({
  children,
  tone = "blue",
  icon,
  className,
}: {
  children: ReactNode;
  tone?: "blue" | "amber" | "green" | "gray";
  icon?: ReactNode;
  className?: string;
}) {
  const palette = {
    blue: "border-blue-200 bg-blue-50 text-blue-700",
    amber: "border-amber-200 bg-amber-50 text-amber-800",
    green: "border-green-100 bg-green-100 text-green-700",
    gray: "border-line bg-bg text-ink-2",
  };
  return (
    <div
      className={cn(
        "flex gap-2 rounded-lg border px-3 py-2.5 text-[12px] leading-[17px]",
        palette[tone],
        className,
      )}
    >
      {icon && <div className="mt-0.5 shrink-0">{icon}</div>}
      <div>{children}</div>
    </div>
  );
}

export function EmptyState({
  title,
  children,
  icon,
  action,
}: {
  title: string;
  children: ReactNode;
  icon?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-line-strong bg-bg/60 px-8 py-10 text-center">
      {icon && <div className="mb-3 text-ink-3">{icon}</div>}
      <h3 className="text-[14px] font-semibold text-ink">{title}</h3>
      <div className="mt-2 max-w-[460px] text-[12px] leading-[18px] text-ink-2">{children}</div>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function LoadingBlock({ label = "Loading data" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 rounded-xl border border-line bg-surface px-6 py-10 text-[12px] text-ink-3">
      <span className="size-4 animate-spin rounded-full border-2 border-line-strong border-t-blue-700" />
      {label}
    </div>
  );
}

export function ErrorBlock({ message, retry }: { message: string; retry?: () => void }) {
  return (
    <div className="rounded-xl border border-red-100 bg-red-100/50 px-4 py-3 text-[12px] leading-[18px] text-red-700">
      <p className="font-medium">The backend did not answer.</p>
      <p className="mt-1">{message}</p>
      {retry && (
        <button className="mt-2 underline" onClick={retry}>
          Try again
        </button>
      )}
    </div>
  );
}
