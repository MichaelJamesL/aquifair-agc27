import type { Metadata } from "next";
import "maplibre-gl/dist/maplibre-gl.css";
import { RoleProvider } from "@/components/neraca/role-context";
import { StoreProvider } from "@/state";
import "./globals.css";

export const metadata: Metadata = {
  title: "NERACA · Groundwater accounts",
  description:
    "Who pumps, who pays, and where pipes should replace pumps in sinking Central Java.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full">
        <RoleProvider>
          <StoreProvider>{children}</StoreProvider>
        </RoleProvider>
      </body>
    </html>
  );
}
