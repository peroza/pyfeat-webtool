import type { JobResponse } from "./types";

export interface PollOptions {
  getJob: (jobId: string) => Promise<JobResponse>;
  timeoutMs: number;
  initialDelayMs?: number;
  signal?: AbortSignal;
}

export async function pollJob(
  jobId: string,
  options: PollOptions,
): Promise<JobResponse> {
  const start = Date.now();
  let delay = options.initialDelayMs ?? 500;
  while (Date.now() - start < options.timeoutMs) {
    if (options.signal?.aborted) {
      throw new Error("Polling aborted");
    }
    const job = await options.getJob(jobId);
    if (job.status === "succeeded" || job.status === "failed") {
      return job;
    }
    await new Promise((r) => setTimeout(r, delay));
    delay = Math.min(delay * 2, 2000);
  }
  throw new Error("Analysis timed out. Please try again.");
}
