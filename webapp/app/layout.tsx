import type { Metadata, Viewport } from "next";
import { Hind_Siliguri, Outfit } from "next/font/google";
import "./globals.css";
import BottomNav from "./components/BottomNav";

const hindSiliguri = Hind_Siliguri({
  subsets: ["bengali", "latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-hind-siliguri",
  display: "swap",
});

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-outfit",
  display: "swap",
});

export const metadata: Metadata = {
  title: "বাংলা ব্রেইল — Bangla Braille Tutor",
  description: "Bangla Braille learning and testing device — web app",
  icons: {
    icon: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%230f1115'/%3E%3Cg fill='%234f9cf9'%3E%3Ccircle cx='11' cy='8' r='3.5'/%3E%3Ccircle cx='11' cy='16' r='3.5'/%3E%3Ccircle cx='21' cy='16' r='3.5'/%3E%3C/g%3E%3Cg fill='%23262b35'%3E%3Ccircle cx='21' cy='8' r='3.5'/%3E%3Ccircle cx='11' cy='24' r='3.5'/%3E%3Ccircle cx='21' cy='24' r='3.5'/%3E%3C/g%3E%3C/svg%3E",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#090d16",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="bn" className={`${hindSiliguri.variable} ${outfit.variable}`}>
      <body>
        {children}
        <BottomNav />
      </body>
    </html>
  );
}
