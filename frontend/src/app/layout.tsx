import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NetWatch AI — Network Security Dashboard",
  description:
    "Self-hosted network security platform with live traffic monitoring, DNS firewall, device tracking, WireGuard VPN, and AI anomaly detection.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
