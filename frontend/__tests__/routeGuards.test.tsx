import { expect, test } from "vitest";
import { allowed } from "@/lib/AuthContext";

test("each role only reaches its own screens", () => {
  expect(allowed("/pharmacist", "patient")).toBe(false);
  expect(allowed("/district", "pharmacist")).toBe(false);
  expect(allowed("/patient", "asha")).toBe(false);
  expect(allowed("/district/transfers/t1", "district_officer")).toBe(true);
});

test("the report and case screens are shared by patients and their ASHA", () => {
  expect(allowed("/patient/report", "asha")).toBe(true);
  expect(allowed("/patient/cases/case-1", "asha")).toBe(true);
  expect(allowed("/patient/report", "pharmacist")).toBe(false);
});
