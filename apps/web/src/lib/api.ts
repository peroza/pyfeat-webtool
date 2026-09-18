import type { JobResponse } from "./types";

function apiBase(): string {
  const base = process.env.NEXT_PUBLIC_API_URL;
  if (!base) {
    throw new Error("NEXT_PUBLIC_API_URL is not set");
  }
  return base.replace(/\/$/, "");
}

export async function submitAnalyze(file: File): Promise<string> {
  const body = new FormData();
  body.append("image", file);
  const response = await fetch(`${apiBase()}/v1/analyze`, {
    method: "POST",
    body,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Upload failed");
  }
  const json = (await response.json()) as { job_id: string };
  return json.job_id;
}

export async function getJob(jobId: string): Promise<JobResponse> {
  const response = await fetch(`${apiBase()}/v1/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch job status");
  }
  return (await response.json()) as JobResponse;
}
