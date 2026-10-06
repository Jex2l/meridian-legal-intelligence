import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Meridian Legal Intelligence — Client Portal",
  description: "Grounded legal research and drafting, verified before delivery.",
};

export default function PortalLayout({ children }: LayoutProps<"/portal">) {
  return <div className="min-h-screen bg-white">{children}</div>;
}
