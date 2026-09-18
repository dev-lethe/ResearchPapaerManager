import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Research Paper Manager",
  description: "Personal paper management system",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ja">
      <body className="min-h-screen bg-bg text-textPrimary">{children}</body>
    </html>
  );
}
