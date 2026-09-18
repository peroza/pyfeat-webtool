"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ACCEPTED_IMAGE_TYPES,
  MAX_UPLOAD_BYTES,
  POLL_TIMEOUT_MS,
} from "@/lib/constants";
import { pollJob } from "@/lib/poll-job";
import type { JobResponse } from "@/lib/types";

export type AnalysisStatus =
  | "idle"
  | "ready"
  | "submitting"
  | "polling"
  | "succeeded"
  | "failed";

export interface UseAnalysisDeps {
  submitAnalyze: (file: File) => Promise<string>;
  getJob: (jobId: string) => Promise<JobResponse>;
  validateFile: (file: File) => string | null;
  pollTimeoutMs?: number;
}

export function validateUploadFile(file: File): string | null {
  const accepted = ACCEPTED_IMAGE_TYPES as readonly string[];
  if (!accepted.includes(file.type)) {
    return "Please upload a JPEG, PNG, or WebP image.";
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return "Image must be 10 MB or smaller.";
  }
  return null;
}

function errorMessageFromUnknown(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong. Please try again.";
}

export function useAnalysis(deps: UseAnalysisDeps) {
  const [status, setStatus] = useState<AnalysisStatus>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [job, setJob] = useState<JobResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const previewUrlRef = useRef<string | null>(null);

  const revokePreview = useCallback(() => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      revokePreview();
    };
  }, [revokePreview]);

  const reset = useCallback(() => {
    revokePreview();
    setFile(null);
    setPreviewUrl(null);
    setJob(null);
    setErrorMessage(null);
    setStatus("idle");
  }, [revokePreview]);

  const selectFile = useCallback(
    (nextFile: File) => {
      const validationError = deps.validateFile(nextFile);
      if (validationError) {
        revokePreview();
        setFile(null);
        setPreviewUrl(null);
        setJob(null);
        setErrorMessage(validationError);
        setStatus("failed");
        return;
      }

      revokePreview();
      const url = URL.createObjectURL(nextFile);
      previewUrlRef.current = url;
      setFile(nextFile);
      setPreviewUrl(url);
      setJob(null);
      setErrorMessage(null);
      setStatus("ready");
    },
    [deps, revokePreview],
  );

  const analyze = useCallback(async () => {
    if (!file || status !== "ready") {
      return;
    }

    setErrorMessage(null);
    setJob(null);
    setStatus("submitting");

    try {
      const jobId = await deps.submitAnalyze(file);
      setStatus("polling");
      const finishedJob = await pollJob(jobId, {
        getJob: deps.getJob,
        timeoutMs: deps.pollTimeoutMs ?? POLL_TIMEOUT_MS,
      });
      setJob(finishedJob);

      if (finishedJob.status === "failed") {
        setErrorMessage(
          finishedJob.error?.message ?? "Analysis failed. Please try again.",
        );
        setStatus("failed");
        return;
      }

      setStatus("succeeded");
    } catch (error) {
      setErrorMessage(errorMessageFromUnknown(error));
      setStatus("failed");
    }
  }, [deps, file, status]);

  return {
    status,
    file,
    previewUrl,
    job,
    errorMessage,
    selectFile,
    analyze,
    reset,
  };
}
