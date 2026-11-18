import type { ButtonHTMLAttributes, ReactNode } from "react";

export const cn = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(" ");

/** Trace tag: links a UI element to a need (U), output (O), method (M), data (D) or check (V) in the document. */
export function TraceTag({ code, size = 10 }: { code: string; size?: 10 | 11 }) {
  return (
    <span
      title={`Traceability: ${code}`}
      className={cn(
        "inline-flex h-[18px] flex-none items-center whitespace-nowrap rounded-sm border border-line-strong px-[5px] leading-[14px] text-ink-2",
        size === 10 ? "text-[10px]" : "text-[11px]",
      )}
    >
      {code}
    </span>
  );
}

export function TraceTags({ codes }: { codes: string[] }) {
  return (
    <span className="inline-flex gap-1">
      {codes.map((c) => (
        <TraceTag key={c} code={c} />
      ))}
    </span>
  );
}

type BtnProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md";
  icon?: ReactNode;
};

const VARIANT = {
  primary: "bg-primary text-on-primary hover:bg-primary-hover",
  secondary: "border border-line-strong bg-surface text-ink hover:bg-bg",
  ghost: "text-ink hover:bg-subtle",
};

const SIZE = {
  sm: "h-7 px-2.5 text-xs leading-4",
  md: "h-9 px-3.5 text-[13px] leading-4",
};

export function Button({ variant = "secondary", size = "sm", icon, children, className, ...rest }: BtnProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-1.5 whitespace-nowrap rounded-md font-medium transition-colors",
        VARIANT[variant],
        SIZE[size],
        className,
      )}
      {...rest}
    >
      {icon}
      <span>{children}</span>
    </button>
  );
}

const TONE = {
  pass: "bg-pass-tint text-pass",
  restricted: "bg-ink text-on-primary",
  neutral: "bg-subtle text-ink-2",
  warn: "bg-warn-tint text-warn",
};

export function Badge({
  tone,
  icon,
  children,
}: {
  tone: keyof typeof TONE;
  icon?: ReactNode;
  children: ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-[22px] items-center gap-1.5 whitespace-nowrap rounded-full pl-2 pr-[9px] text-xs font-medium leading-4",
        TONE[tone],
      )}
    >
      {tone === "pass" && <span className="size-1.5 rounded-full bg-pass" />}
      {icon}
      {children}
    </span>
  );
}
