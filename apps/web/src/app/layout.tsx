import type { Metadata } from "next";
import { StoreProvider } from "@/state";
import "./globals.css";

export const metadata: Metadata = {
  title: "Groundtrace",
  description: "Trace land subsidence back to the groundwater pumping that causes it.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full">
        <StoreProvider>{children}</StoreProvider>
      </body>
    </html>
  );
}
