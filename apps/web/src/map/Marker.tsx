import { cn } from "@/components/ui";

export type MarkerState = "default" | "selected" | "low" | "muted";

// map/source marker variants from the Figma design system
const DOT: Record<MarkerState, string> = {
  default: "bg-white text-ink shadow-[inset_0_0_0_1.5px_var(--color-ink)] group-hover:bg-ink group-hover:text-on-primary",
  low: "bg-white/85 text-ink-3 outline-[1.5px] outline-dashed -outline-offset-[1.5px] outline-ink-3 group-hover:bg-ink group-hover:text-on-primary",
  muted: "bg-white/70 text-ink-3 shadow-[inset_0_0_0_1px_var(--color-line-strong)] group-hover:bg-ink group-hover:text-on-primary",
  selected: "bg-ink text-on-primary shadow-[0_0_0_2px_#fff]",
};

export function Marker({
  rank,
  state,
  x,
  y,
  label,
  animate,
  onClick,
  onHover,
}: {
  rank: number;
  state: MarkerState;
  x: number;
  y: number;
  label: string;
  animate: boolean;
  onClick?: () => void;
  onHover?: (on: boolean) => void;
}) {
  return (
    <button
      className={cn(
        "group absolute left-0 top-0 grid size-11 cursor-pointer place-items-center",
        animate && "transition-transform duration-300 ease-map",
      )}
      style={{ transform: `translate(${x - 22}px, ${y - 22}px)` }}
      onClick={(e) => {
        e.stopPropagation();
        onClick?.();
      }}
      onPointerDown={(e) => e.stopPropagation()}
      onMouseEnter={() => onHover?.(true)}
      onMouseLeave={() => onHover?.(false)}
      aria-label={label}
      title={label}
    >
      {state === "selected" && (
        <span className="absolute inset-0 rounded-full bg-primary/16 shadow-[inset_0_0_0_2px_var(--color-primary)]" />
      )}
      <span
        className={cn(
          "relative grid size-[26px] place-items-center rounded-full font-mono text-xs font-medium leading-[14px] transition-colors",
          DOT[state],
        )}
      >
        {rank}
      </span>
    </button>
  );
}
