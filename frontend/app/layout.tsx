import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Frying-PAN",
  description: "Panorama configuration merge and migration workbench scaffold",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
