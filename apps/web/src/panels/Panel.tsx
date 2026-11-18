import type { ReactNode } from "react";

/** Right-hand panel shell, 400 px wide (screens 07–09). */
export function Panel({ children }: { children: ReactNode }) {
  return (
    <aside className="relative flex min-h-0 w-[400px] flex-none flex-col border-l border-line bg-surface">{children}</aside>
  );
}

/** Footer note pinned to the bottom of the panel. */
export function PanelNote({ children }: { children: ReactNode }) {
  return (
    <div className="absolute inset-x-0 bottom-0 h-[53px] border-t border-line bg-bg px-4 py-2.5 text-xs leading-4 text-ink-2">
      {children}
    </div>
  );
}

export function PanelFooter({ children }: { children: ReactNode }) {
  return (
    <div className="absolute inset-x-0 bottom-0 flex h-[53px] items-center gap-2 border-t border-line bg-bg px-4 py-3">
      {children}
    </div>
  );
}
