import { Suspense } from "react";
import { HOT_SPOTS } from "@/data/run";
import { Evidence } from "@/panels/Evidence";

/** only the eight hot spots in the run exist; any other cell ID is a 404 */
export const dynamicParams = false;

export function generateStaticParams() {
  return HOT_SPOTS.map((h) => ({ id: h.id }));
}

/**
 * 08 · Hot-spot evidence (U3). The panel reads the cell ID from the URL on the client, so the
 * page itself never touches `params` and navigation between hot spots stays instant.
 */
export default function EvidencePage() {
  return (
    <Suspense fallback={null}>
      <Evidence />
    </Suspense>
  );
}
