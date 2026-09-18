"use client";

import { Progress } from "@/components/ui/progress";
import type { AnalysisStatus } from "@/hooks/use-analysis";

interface AnalysisProgressProps {
  status: AnalysisStatus;
}

const STATUS_COPY: Partial<Record<AnalysisStatus, string>> = {
  submitting: "Uploading image…",
  polling: "Analyzing facial expression…",
};

export function AnalysisProgress({ status }: AnalysisProgressProps) {
  if (status !== "submitting" && status !== "polling") {
    return null;
  }

  const label = STATUS_COPY[status] ?? "Working…";

  return (
    <div
      className="animate-fade-in flex w-full max-w-lg flex-col gap-2"
      role="status"
      aria-live="polite"
    >
      <p className="text-sm text-muted-foreground">{label}</p>
      <Progress
        value={status === "submitting" ? 35 : 70}
        className="h-1.5"
        indicatorClassName="bg-primary/90"
      />
    </div>
  );
}
