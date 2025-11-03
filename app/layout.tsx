import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sprout",
  description: "Sprout is a platform for managing your finances and investments.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
