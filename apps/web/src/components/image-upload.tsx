"use client";

import { useCallback, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ACCEPTED_IMAGE_TYPES } from "@/lib/constants";
import type { AnalysisStatus } from "@/hooks/use-analysis";
import { cn } from "cn";

const ACCEPT_ATTR = ACCEPTED_IMAGE_TYPES.join(",");

interface ImageUploadProps {
  status: AnalysisStatus;
  previewUrl: string | null;
  onSelectFile: (file: File) => void;
  onAnalyze: () => void;
  disabled?: boolean;
}

export function ImageUpload({
  status,
  previewUrl,
  onSelectFile,
  onAnalyze,
  disabled = false,
}: ImageUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const pickFile = useCallback(
    (file: File | undefined) => {
      if (!file || disabled) {
        return;
      }
      onSelectFile(file);
    },
    [disabled, onSelectFile],
  );

  const onInputChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      pickFile(event.target.files?.[0]);
      event.target.value = "";
    },
    [pickFile],
  );

  const onDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setIsDragging(false);
      if (disabled) {
        return;
      }
      pickFile(event.dataTransfer.files[0]);
    },
    [disabled, pickFile],
  );

  const onDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const busy =
    status === "submitting" || status === "polling" || status === "succeeded";
  const canAnalyze = status === "ready" && !disabled;

  return (
    <Card className="w-full max-w-lg shadow-sm shadow-primary/5 backdrop-blur-sm">
      <CardContent className="flex flex-col gap-4 pt-4">
        <div
          role="button"
          tabIndex={disabled ? -1 : 0}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              inputRef.current?.click();
            }
          }}
          onClick={() => !disabled && inputRef.current?.click()}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          className={cn(
            "flex min-h-52 cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border/80 bg-gradient-to-b from-muted/40 to-muted/10 px-4 py-8 text-center transition-all duration-200",
            isDragging &&
              "scale-[1.01] border-primary bg-primary/8 ring-2 ring-primary/20",
            !disabled && !isDragging && "hover:border-primary/40 hover:bg-muted/40",
            disabled && "pointer-events-none opacity-60",
          )}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT_ATTR}
            className="sr-only"
            disabled={disabled || busy}
            onChange={onInputChange}
          />
          {previewUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={previewUrl}
              alt="Selected face preview"
              className="max-h-56 max-w-full rounded-lg object-contain shadow-sm"
            />
          ) : (
            <>
              <span
                aria-hidden
                className="flex size-10 items-center justify-center rounded-full bg-primary/10 text-primary"
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.75"
                  className="size-5"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 16V8m0 0 3.5 3.5M12 8 8.5 11.5M4 16.5V18a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-1.5"
                  />
                </svg>
              </span>
              <p className="text-sm font-medium text-foreground">
                Drop an image here or click to browse
              </p>
              <p className="text-xs text-muted-foreground">
                JPEG, PNG, or WebP up to 10 MB
              </p>
            </>
          )}
        </div>
        <Button
          type="button"
          size="lg"
          className="w-full"
          disabled={!canAnalyze}
          onClick={onAnalyze}
        >
          Analyze
        </Button>
      </CardContent>
    </Card>
  );
}
