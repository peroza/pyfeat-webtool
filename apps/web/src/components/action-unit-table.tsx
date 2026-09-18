interface ActionUnitTableProps {
  actionUnits: Record<string, number>;
}

function formatScore(value: number): string {
  return value.toFixed(2);
}

export function ActionUnitTable({ actionUnits }: ActionUnitTableProps) {
  const entries = Object.entries(actionUnits).sort(([a], [b]) =>
    a.localeCompare(b),
  );

  if (entries.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No action unit scores.</p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/40 text-left">
            <th scope="col" className="px-3 py-2 font-medium text-foreground">
              Action unit
            </th>
            <th
              scope="col"
              className="px-3 py-2 font-medium text-foreground text-right"
            >
              Score
            </th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([code, score]) => (
            <tr key={code} className="border-b border-border last:border-0">
              <td className="px-3 py-2 font-mono text-foreground">{code}</td>
              <td className="px-3 py-2 text-right tabular-nums text-muted-foreground">
                {formatScore(score)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
