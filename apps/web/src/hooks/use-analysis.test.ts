import { describe, it, expect, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useAnalysis } from "./use-analysis";

describe("useAnalysis", () => {
  it("moves from ready to succeeded", async () => {
    const file = new File([new Uint8Array([1, 2, 3])], "face.png", {
      type: "image/png",
    });
    const deps = {
      submitAnalyze: vi.fn().mockResolvedValue("job-1"),
      getJob: vi.fn().mockResolvedValue({
        job_id: "job-1",
        status: "succeeded",
        error: null,
        result: {
          face_count: 1,
          emotions: { happiness: 0.9 },
          action_units: { AU12: 0.8 },
          landmarks: [[1, 2]],
          overlay_image_base64: "aaa",
        },
      }),
      validateFile: () => null as string | null,
    };
    const { result } = renderHook(() => useAnalysis(deps));
    act(() => result.current.selectFile(file));
    expect(result.current.status).toBe("ready");
    await act(async () => {
      await result.current.analyze();
    });
    await waitFor(() => expect(result.current.status).toBe("succeeded"));
  });
});
