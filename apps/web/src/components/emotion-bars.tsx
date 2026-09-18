import type { CSSProperties } from "react";
import { Progress } from "@/components/ui/progress";

interface EmotionBarsProps {
  emotions: Record<string, number>;
}

const EMOTION_BAR_COLORS: Record<string, string> = {
  happiness: "oklch(0.72 0.14 85)",
  happy: "oklch(0.72 0.14 85)",
  sadness: "oklch(0.58 0.1 250)",
  sad: "oklch(0.58 0.1 250)",
  anger: "oklch(0.58 0.18 25)",
  angry: "oklch(0.58 0.18 25)",
  fear: "oklch(0.55 0.1 300)",
  disgust: "oklch(0.58 0.12 140)",
  surprise: "oklch(0.68 0.12 195)",
  neutral: "oklch(0.55 0.02 230)",
};

const DEFAULT_BAR_COLOR = "oklch(0.5 0.08 210)";

function formatEmotionLabel(key: string): string {
  return key.charAt(0).toUpperCase() + key.slice(1);
}

function formatScore(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function barColorForEmotion(name: string): string {
  return EMOTION_BAR_COLORS[name.toLowerCase()] ?? DEFAULT_BAR_COLOR;
}

export function EmotionBars({ emotions }: EmotionBarsProps) {
  const entries = Object.entries(emotions).sort(([, a], [, b]) => b - a);

  if (entries.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No emotion scores available.</p>
    );
  }

  return (
    <ul className="flex flex-col gap-3.5">
      {entries.map(([name, value], index) => (
        <li
          key={name}
          className="animate-fade-up flex flex-col gap-1.5"
          style={{ animationDelay: `${index * 60}ms` }}
        >
          <div className="flex items-baseline justify-between gap-2 text-sm">
            <span className="font-medium text-foreground">
              {formatEmotionLabel(name)}
            </span>
            <span className="tabular-nums text-muted-foreground">
              {formatScore(value)}
            </span>
          </div>
          <Progress
            value={Math.min(100, Math.max(0, value * 100))}
            className="h-1.5"
            style={
              {
                "--emotion-bar": barColorForEmotion(name),
              } as CSSProperties
            }
            indicatorClassName="bg-[var(--emotion-bar)]"
          />
        </li>
      ))}
    </ul>
  );
}
