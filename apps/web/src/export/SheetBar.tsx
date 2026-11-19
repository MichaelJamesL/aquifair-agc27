"use client";

import { ArrowLeft, Printer } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui";

export function SheetBar() {
  return (
    <div className="no-print sticky top-0 z-10 mb-8 flex h-14 items-center gap-3 border-b border-line bg-surface px-5">
      <Link href="/audit" className="flex items-center gap-1.5 text-[13px] font-medium text-ink-2 hover:text-ink">
        <ArrowLeft size={16} strokeWidth={2} />
        Back to the map
      </Link>
      <span className="flex-1" />
      <span className="text-xs text-ink-3">Audit sheet · R-0007 · A4</span>
      <Button variant="primary" icon={<Printer size={14} strokeWidth={1.9} />} onClick={() => window.print()}>
        Print or save as PDF
      </Button>
    </div>
  );
}
