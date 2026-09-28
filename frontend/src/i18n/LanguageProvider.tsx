"use client";

import React, { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react";

export type Language = "en" | "hi";

interface LanguageContextType {
  /** Which language leads. Both languages are always shown (Saathi rule); this only decides the order. */
  lang: Language;
  setLang: (lang: Language) => void;
  /** For attributes that can hold one string (aria-label, placeholder): "lead · second". */
  both: (hi: string, en: string) => string;
  /** The leading-language string alone, for places with no room for two. */
  pick: (hi: string, en: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);
const KEY = "saathi_lang";

function readStoredLang(): Language | null {
  try {
    const v = localStorage.getItem(KEY);
    return v === "en" || v === "hi" ? v : null;
  } catch {
    return null;
  }
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Language>("hi");

  useEffect(() => {
    const stored = readStoredLang();
    if (stored) setLangState(stored); // eslint-disable-line react-hooks/set-state-in-effect -- sync from localStorage once on mount
  }, []);

  useEffect(() => {
    document.documentElement.dataset.lang = lang;
    document.documentElement.lang = lang;
  }, [lang]);

  const setLang = useCallback((l: Language) => {
    setLangState(l);
    try {
      localStorage.setItem(KEY, l);
    } catch {
      /* private mode: language just won't persist */
    }
  }, []);

  const both = useCallback((hi: string, en: string) => (lang === "hi" ? `${hi} · ${en}` : `${en} · ${hi}`), [lang]);
  const pick = useCallback((hi: string, en: string) => (lang === "hi" ? hi : en), [lang]);

  return <LanguageContext.Provider value={{ lang, setLang, both, pick }}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) throw new Error("useLanguage must be used within a LanguageProvider");
  return context;
}
