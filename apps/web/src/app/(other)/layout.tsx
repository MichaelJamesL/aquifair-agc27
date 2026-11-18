import { TopBar } from "@/components/TopBar";

export default function OtherLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="flex h-full flex-col">
      <TopBar />
      {children}
    </div>
  );
}
