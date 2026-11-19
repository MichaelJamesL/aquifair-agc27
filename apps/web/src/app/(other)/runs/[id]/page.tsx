import { notFound } from "next/navigation";
import { RunProgress } from "@/runs/RunProgress";

const LIVE_RUNS = ["R-0008", "R-0009"];

/** only the running and the stopped demo runs have a run page; published runs open on the map */
export const dynamicParams = false;

export function generateStaticParams() {
  return LIVE_RUNS.map((id) => ({ id }));
}

/** 05 · Run in progress, and 05b · Run stopped at Gate 2 */
export default async function RunPage({ params }: PageProps<"/runs/[id]">) {
  const { id } = await params;
  if (!LIVE_RUNS.includes(id)) notFound();
  return <RunProgress id={id} />;
}
