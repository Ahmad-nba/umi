import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "UMI Feedback Watch Tower",
  description: "A clear path from feedback to verified resolution.",
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
