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
    <Card className="w-full max-w-lg">
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
            "flex min-h-48 cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border bg-muted/30 px-4 py-8 text-center transition-colors",
            isDragging && "border-primary bg-primary/5",
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
              className="max-h-56 max-w-full rounded-md object-contain"
            />
          ) : (
            <>
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
