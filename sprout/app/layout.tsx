import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import PageLayout from "./components/PageLayout";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Sprout",
  description:
    "Sprout is a platform for managing your finances and investments.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={inter.className}>
        <PageLayout>{children}</PageLayout>
      </body>
    </html>
  );
}
