import { TopBar } from "@/components/neraca/top-bar";

export default function AppLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="flex min-h-screen flex-col bg-bg">
      <TopBar />
      <main className="min-h-[calc(100vh-56px)]">{children}</main>
    </div>
  );
}
