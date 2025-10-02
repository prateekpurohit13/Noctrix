import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AuthProvider } from "@/contexts/AuthContext";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Toaster } from "@/components/Toaster";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Noctrix AI",
  description: "Leverage the power of AI to automatically cleanse, analyze, and assess your sensitive documents for security risks, all within a secure, privacy-preserving environment.",
  keywords: ["AI", "document analysis", "security", "privacy", "document cleansing", "risk assessment"],
  authors: [{ name: "Noctrix AI" }],
  creator: "Noctrix AI",
  publisher: "Noctrix AI",
  robots: "index, follow",
  openGraph: {
    title: "Noctrix AI",
    description: "AI-powered document analysis and security risk assessment platform",
    type: "website",
    locale: "en_US",
    siteName: "Noctrix AI",
  },
  twitter: {
    card: "summary_large_image",
    title: "Noctrix AI",
    description: "AI-powered document analysis and security risk assessment platform",
  },
  icons: {
    icon: [
      { url: "/logo.jpg", sizes: "32x32", type: "image/jpeg" },
      { url: "/logo.jpg", sizes: "16x16", type: "image/jpeg" },
    ],
    apple: "/logo.jpg",
    shortcut: "/logo.jpg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthProvider>
            {children}
            <Toaster />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}