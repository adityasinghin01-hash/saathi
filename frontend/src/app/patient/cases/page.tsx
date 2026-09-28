"use client";

import Link from "next/link";
import { api } from "@/lib/api";
import { useLoad, useRefData } from "@/lib/hooks";
import { PhoneShell } from "@/components/shells";
import { Bi, CaseStatusChip, DrugName, Empty, ErrorBox, Loading, when } from "@/components/ui";

export default function MyReports() {
  const ref = useRefData();
  const cases = useLoad(() => api.cases(), "my-cases");
  return (
    <PhoneShell title={{ hi: "शिकायतें", en: "Reports" }}>
      {cases.loading && !cases.data && <Loading />}
      {cases.error ? <ErrorBox error={cases.error} onRetry={cases.reload} /> : null}
      {cases.data?.length === 0 && <Empty hi="अभी कोई शिकायत नहीं" en="No reports yet" />}
      <div className="sa-rows">
        {cases.data?.map((c) => {
          const w = when(c.created_at);
          return (
            <Link key={c.id} className="sa-row" href={`/patient/cases/${c.id}`} style={{ minHeight: 76 }}>
              <span className="sa-row-main" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                <span style={{ font: "600 16px/22px var(--font-sans)" }}><DrugName d={ref.drug(c.drug_id)} id={c.drug_id} /></span>
                <span className="m-caption"><Bi inline hi={w.hi} en={w.en} /></span>
              </span>
              <CaseStatusChip status={c.status} />
            </Link>
          );
        })}
      </div>
    </PhoneShell>
  );
}
