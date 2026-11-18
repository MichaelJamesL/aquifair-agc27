import { LayersPanel } from "@/components/LayersPanel";
import { TopBar } from "@/components/TopBar";
import { MapView } from "@/map/MapView";

/**
 * Map workspace: top bar, layers panel and the map stay mounted while the right-hand
 * panel (the page) changes, so moving between screens 06, 07 and 08 animates the map
 * instead of reloading it.
 */
export default function WorkspaceLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="flex h-full flex-col">
      <TopBar />
      <div className="flex min-h-0 flex-1">
        <LayersPanel />
        <MapView />
        {children}
      </div>
    </div>
  );
}
