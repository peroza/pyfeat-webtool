import { describe, it, expect, vi } from "vitest";
import { pollJob } from "./poll-job";
import type { JobResponse } from "./types";

describe("pollJob", () => {
  it("resolves when job succeeds", async () => {
    const getJob = vi
      .fn<(id: string) => Promise<JobResponse>>()
      .mockResolvedValueOnce({
        job_id: "1",
        status: "running",
        error: null,
        result: null,
      })
      .mockResolvedValueOnce({
        job_id: "1",
        status: "succeeded",
        error: null,
        result: {
          face_count: 1,
          emotions: { happiness: 1 },
          action_units: {},
          landmarks: [],
          overlay_image_base64: "abc",
        },
      });

    const result = await pollJob("1", {
      getJob,
      timeoutMs: 5000,
      initialDelayMs: 1,
    });
    expect(result.status).toBe("succeeded");
    expect(getJob).toHaveBeenCalledTimes(2);
  });
});
