import type { NumberValue, RangeValue } from "@/lib/api";

export function num(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);
}

export function compact(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `${num(value / 1_000_000_000, digits)} bn`;
  if (abs >= 1_000_000) return `${num(value / 1_000_000, digits)} M`;
  if (abs >= 1_000) return `${num(value / 1_000, digits)}k`;
  return num(value, digits);
}

export function mm3(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${num(value / 1_000_000, digits)}`;
}

export function m3(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${num(value, digits)} m³`;
}

export function rupiah(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `Rp ${num(value, digits)}`;
}

export function billionRupiah(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${num(value / 1_000_000_000, digits)} bn`;
}

export function percent(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${num(value, digits)}%`;
}

export function mid(range: RangeValue | null | undefined): number | null {
  if (!range || range.label === "MISSING") return null;
  if (range.central !== null && range.central !== undefined) return range.central;
  if (range.low !== null && range.high !== null) return (range.low + range.high) / 2;
  return range.low ?? range.high ?? null;
}

export function valueOf(number: NumberValue | null | undefined): number | null {
  if (!number || number.label === "MISSING") return null;
  return number.value;
}

export function rangeText(range: RangeValue | null | undefined, digits = 1, suffix = ""): string {
  if (!range || range.label === "MISSING") return "not estimated";
  const low = range.low;
  const high = range.high;
  if (low === null || high === null) return "not estimated";
  return `${num(low, digits)}–${num(high, digits)}${suffix}`;
}

export function rangeMm3(range: RangeValue | null | undefined, digits = 1): string {
  if (!range || range.label === "MISSING") return "not estimated";
  const low = range.low;
  const high = range.high;
  if (low === null || high === null) return "not estimated";
  return `${num(low / 1_000_000, digits)}–${num(high / 1_000_000, digits)}`;
}

export function rangeWidth(
  range: RangeValue | null | undefined,
  ceiling: number | null | undefined,
): { left: number; width: number } | null {
  if (!range || range.low === null || range.high === null || !ceiling || ceiling <= 0) {
    return null;
  }
  const left = Math.max(0, Math.min(100, (range.low / ceiling) * 100));
  const right = Math.max(0, Math.min(100, (range.high / ceiling) * 100));
  return { left, width: Math.max(1.5, right - left) };
}

export function initials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}
