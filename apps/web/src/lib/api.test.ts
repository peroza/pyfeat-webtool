import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getJob, submitAnalyze } from "./api";
import type { JobResponse } from "./types";

describe("api", () => {
  beforeEach(() => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("submitAnalyze posts image and returns job_id", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ job_id: "job-42" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const file = new File(["pixels"], "face.png", { type: "image/png" });
    const jobId = await submitAnalyze(file);

    expect(jobId).toBe("job-42");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/v1/analyze",
      expect.objectContaining({ method: "POST" }),
    );
    const formData = fetchMock.mock.calls[0][1].body as FormData;
    expect(formData.get("image")).toBe(file);
  });

  it("strips trailing slash from API base URL", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://localhost:8000/");
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ job_id: "x" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await submitAnalyze(
      new File(["a"], "a.png", { type: "image/png" }),
    );

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/v1/analyze",
      expect.any(Object),
    );
  });

  it("getJob returns parsed job response", async () => {
    const job: JobResponse = {
      job_id: "job-1",
      status: "running",
      error: null,
      result: null,
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => job,
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getJob("job-1");

    expect(result).toEqual(job);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/v1/jobs/job-1",
    );
  });

  it("throws when NEXT_PUBLIC_API_URL is missing", async () => {
    vi.unstubAllEnvs();
    delete process.env.NEXT_PUBLIC_API_URL;

    await expect(
      submitAnalyze(new File(["a"], "a.png", { type: "image/png" })),
    ).rejects.toThrow("NEXT_PUBLIC_API_URL is not set");
  });
});
