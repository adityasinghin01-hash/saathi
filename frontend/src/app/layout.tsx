import type { Metadata } from "next";
import { Baloo_2, IBM_Plex_Sans, IBM_Plex_Sans_Devanagari } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "@/i18n/LanguageProvider";
import { AuthProvider } from "@/lib/AuthContext";
import { OfflineQueueProvider } from "@/lib/OfflineQueueContext";
import { RootLayoutClient } from "./RootLayoutClient";

const plex = IBM_Plex_Sans({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--nf-plex" });
const plexDeva = IBM_Plex_Sans_Devanagari({ subsets: ["devanagari"], weight: ["400", "500", "600"], variable: "--nf-plex-deva" });
const baloo = Baloo_2({ subsets: ["latin", "devanagari"], weight: ["600", "700"], variable: "--nf-baloo" });

export const metadata: Metadata = {
  title: "Saathi · साथी",
  description: "Every refill, reaching home — medicine supply loop for diabetes and BP patients at government health centres (synthetic demo).",
  manifest: "/manifest.json",
  icons: { icon: "/art/logo.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="hi" data-lang="hi" className={`${plex.variable} ${plexDeva.variable} ${baloo.variable}`}>
      <body>
        <LanguageProvider>
          <AuthProvider>
            <OfflineQueueProvider>
              <RootLayoutClient>{children}</RootLayoutClient>
            </OfflineQueueProvider>
          </AuthProvider>
        </LanguageProvider>
      </body>
    </html>
  );
}
