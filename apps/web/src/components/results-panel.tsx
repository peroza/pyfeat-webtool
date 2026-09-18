import { ActionUnitTable } from "@/components/action-unit-table";
import { EmotionBars } from "@/components/emotion-bars";
import { OverlayPreview } from "@/components/overlay-preview";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { AnalysisResult } from "@/lib/types";

interface ResultsPanelProps {
  result: AnalysisResult;
  onReset: () => void;
}

function formatCoordinate(pair: number[]): string {
  if (pair.length < 2) {
    return pair.join(", ");
  }
  return `(${pair[0].toFixed(1)}, ${pair[1].toFixed(1)})`;
}

export function ResultsPanel({ result, onReset }: ResultsPanelProps) {
  const landmarkCount = result.landmarks.length;

  return (
    <div className="animate-fade-up flex w-full max-w-lg flex-col gap-6">
      {result.face_count > 1 ? (
        <Alert>
          <AlertTitle>Multiple faces detected</AlertTitle>
          <AlertDescription>
            Showing results for the largest face only ({result.face_count} faces
            in image).
          </AlertDescription>
        </Alert>
      ) : null}

      <Card className="w-full">
        <CardHeader>
          <CardTitle>Landmark overlay</CardTitle>
          <CardDescription>
            Cyan box is the detected face; green points are facial landmarks.
            Large phone photos are downscaled before analysis so the detector
            sees the whole face.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <OverlayPreview overlayImageBase64={result.overlay_image_base64} />
        </CardContent>
      </Card>

      <Card className="w-full">
        <CardHeader>
          <CardTitle>Emotions</CardTitle>
          <CardDescription>Sorted by score (highest first).</CardDescription>
        </CardHeader>
        <CardContent>
          <EmotionBars emotions={result.emotions} />
        </CardContent>
      </Card>

      <Card className="w-full">
        <CardHeader>
          <CardTitle>Action units</CardTitle>
          <CardDescription>FACS action unit intensities.</CardDescription>
        </CardHeader>
        <CardContent>
          <ActionUnitTable actionUnits={result.action_units} />
        </CardContent>
      </Card>

      <Card className="w-full">
        <CardHeader>
          <CardTitle>Landmarks</CardTitle>
          <CardDescription>
            {landmarkCount} point{landmarkCount === 1 ? "" : "s"} for the
            primary face.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {landmarkCount > 0 ? (
            <details className="text-sm">
              <summary className="cursor-pointer font-medium text-foreground hover:underline">
                View coordinates
              </summary>
              <ul className="mt-3 max-h-48 space-y-1 overflow-y-auto font-mono text-xs text-muted-foreground">
                {result.landmarks.map((point, index) => (
                  <li key={index}>
                    {index + 1}. {formatCoordinate(point)}
                  </li>
                ))}
              </ul>
            </details>
          ) : (
            <p className="text-sm text-muted-foreground">No landmark data.</p>
          )}
        </CardContent>
      </Card>

      <Button type="button" variant="outline" className="self-center" onClick={onReset}>
        Analyze another image
      </Button>
    </div>
  );
}
