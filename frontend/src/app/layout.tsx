import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aquafin",
  description: "Personal finance tracker – track, categorize, analyze.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
