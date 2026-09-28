import { act, render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { LanguageProvider, useLanguage } from "@/i18n/LanguageProvider";
import { Bi } from "@/components/ui";

function Probe() {
  const { lang, setLang, both } = useLanguage();
  return (
    <div>
      <span data-testid="lang">{lang}</span>
      <span data-testid="both">{both("दवा", "Medicine")}</span>
      <Bi hi="दवा" en="Medicine" />
      <button onClick={() => setLang("en")}>en</button>
    </div>
  );
}

test("Hindi leads by default and both languages always render", () => {
  render(<LanguageProvider><Probe /></LanguageProvider>);
  expect(screen.getByTestId("lang").textContent).toBe("hi");
  expect(screen.getByTestId("both").textContent).toBe("दवा · Medicine");
  expect(screen.getByText("दवा", { selector: '[lang="hi"]' })).toBeTruthy();
  expect(screen.getByText("Medicine", { selector: '[lang="en"]' })).toBeTruthy();
  expect(document.documentElement.dataset.lang).toBe("hi");
});

test("switching to English changes the lead and is remembered", () => {
  render(<LanguageProvider><Probe /></LanguageProvider>);
  act(() => screen.getByText("en").click());
  expect(screen.getByTestId("both").textContent).toBe("Medicine · दवा");
  expect(document.documentElement.dataset.lang).toBe("en");
  expect(localStorage.getItem("saathi_lang")).toBe("en");
});
