import { AuditSheet } from "@/export/AuditSheet";
import { SheetBar } from "@/export/SheetBar";

/** 12 · Audit sheet (O5), two A4 pages. Opened by Export; print to PDF from the browser. */
export default async function SheetPage({ searchParams }: { searchParams: Promise<Record<string, string | undefined>> }) {
  const q = await searchParams;
  const lang: "id" | "en" | "both" = q.lang === "en" ? "en" : q.lang === "both" ? "both" : "id";
  const pub = q.version === "public";
  return (
    <div className="min-h-full bg-subtle pb-10 print:bg-white print:p-0">
      <SheetBar />
      <div className="flex flex-col gap-8 print:gap-0">
        {(lang === "both" ? (["id", "en"] as const) : [lang as "id" | "en"]).map((l) => (
          <AuditSheet key={l} lang={l} pub={pub} />
        ))}
      </div>
    </div>
  );
}
