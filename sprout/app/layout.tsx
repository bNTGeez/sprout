import type { Metadata } from "next";
import "./globals.css";
import PageLayout from "./components/PageLayout";

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
    <html lang="en">
      <body>
        <PageLayout>{children}</PageLayout>
      </body>
    </html>
  );
}
