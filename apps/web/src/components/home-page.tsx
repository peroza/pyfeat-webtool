"use client";

import { AnalysisProgress } from "@/components/analysis-progress";
import { ImageUpload } from "@/components/image-upload";
import { ResultsPanel } from "@/components/results-panel";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  useAnalysis,
  validateUploadFile,
} from "@/hooks/use-analysis";
import { getJob, submitAnalyze } from "@/lib/api";
import { POLL_TIMEOUT_MS } from "@/lib/constants";

export function HomePage() {
  const {
    status,
    previewUrl,
    job,
    errorMessage,
    selectFile,
    analyze,
    reset,
  } = useAnalysis({
    submitAnalyze,
    getJob,
    validateFile: validateUploadFile,
    pollTimeoutMs: POLL_TIMEOUT_MS,
  });

  const uploadDisabled =
    status === "submitting" || status === "polling" || status === "succeeded";

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col items-center gap-10 px-6 py-16">
      <header className="flex flex-col items-center gap-3 text-center">
        <h1 className="font-heading text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
          Py-FEAT
        </h1>
        <p className="max-w-md text-base text-muted-foreground sm:text-lg">
          Upload a face photo to analyze emotions, action units, and landmarks.
        </p>
      </header>

      <div className="flex w-full flex-col items-center gap-6">
        <ImageUpload
          status={status}
          previewUrl={previewUrl}
          onSelectFile={selectFile}
          onAnalyze={() => void analyze()}
          disabled={uploadDisabled}
        />

        <AnalysisProgress status={status} />

        {status === "failed" && errorMessage ? (
          <Alert variant="destructive" className="max-w-lg">
            <AlertTitle>Analysis could not complete</AlertTitle>
            <AlertDescription>{errorMessage}</AlertDescription>
          </Alert>
        ) : null}

        {status === "succeeded" && job?.result ? (
          <ResultsPanel result={job.result} onReset={reset} />
        ) : null}

        {status === "succeeded" && job && !job.result ? (
          <Alert className="max-w-lg">
            <AlertTitle>Analysis complete</AlertTitle>
            <AlertDescription>
              No result payload was returned. Try analyzing again.
            </AlertDescription>
          </Alert>
        ) : null}

        {status === "failed" ? (
          <Button type="button" variant="outline" onClick={reset}>
            Try again
          </Button>
        ) : null}
      </div>
    </div>
  );
}
