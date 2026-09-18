import { Progress } from "@/components/ui/progress";

interface EmotionBarsProps {
  emotions: Record<string, number>;
}

function formatEmotionLabel(key: string): string {
  return key.charAt(0).toUpperCase() + key.slice(1);
}

function formatScore(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function EmotionBars({ emotions }: EmotionBarsProps) {
  const entries = Object.entries(emotions).sort(([, a], [, b]) => b - a);

  if (entries.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No emotion scores available.</p>
    );
  }

  return (
    <ul className="flex flex-col gap-3">
      {entries.map(([name, value]) => (
        <li key={name} className="flex flex-col gap-1.5">
          <div className="flex items-baseline justify-between gap-2 text-sm">
            <span className="font-medium text-foreground">
              {formatEmotionLabel(name)}
            </span>
            <span className="tabular-nums text-muted-foreground">
              {formatScore(value)}
            </span>
          </div>
          <Progress value={Math.min(100, Math.max(0, value * 100))} />
        </li>
      ))}
    </ul>
  );
}
