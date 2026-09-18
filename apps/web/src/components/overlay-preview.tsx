interface OverlayPreviewProps {
  overlayImageBase64: string;
}

export function OverlayPreview({ overlayImageBase64 }: OverlayPreviewProps) {
  const src = `data:image/png;base64,${overlayImageBase64}`;

  return (
    <img
      src={src}
      alt="Face landmarks overlay"
      className="max-h-80 w-full rounded-lg border border-border object-contain bg-muted/30"
    />
  );
}
