import type { Metadata } from "next";
import { Syne, DM_Sans, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const syne = Syne({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["400", "700"],
  display: "swap",
});

const dmSans = DM_Sans({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Opti-Twin — AI-Powered Industrial Optimization",
  description: "Enterprise-grade industrial optimization SaaS platform. Monitor factories, run digital twins, and receive AI-powered recommendations to reduce energy costs and improve efficiency.",
  keywords: ["industrial optimization", "digital twin", "AI", "energy management", "factory monitoring", "SaaS"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      data-mode="dashboard"
      className={`${syne.variable} ${dmSans.variable} ${jetbrainsMono.variable} h-full`}
      suppressHydrationWarning
    >
      <body className="min-h-full bg-bg text-text-secondary antialiased">
        {children}
      </body>
    </html>
  );
}
