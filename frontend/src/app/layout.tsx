import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CodeBase AI",
  description: "Ask questions about GitHub repositories with source-grounded AI.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
