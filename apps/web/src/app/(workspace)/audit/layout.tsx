import { Panel } from "@/panels/Panel";

export default function AuditLayout({ children }: LayoutProps<"/audit">) {
  return <Panel>{children}</Panel>;
}
