import { useParams } from "react-router";
import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight, Drill, Text } from "lucide-react";
import type { Span } from "../../types";

const typeDisplayConfig: Record<
  string,
  {
    name: string;
    color: string;
    icon: React.ElementType;
  }
> = {
  function: {
    name: "Tool call",
    color: "bg-blue-500",
    icon: Drill,
  },
  generation: {
    name: "Text generation",
    color: "bg-green-500",
    icon: Text,
  },
};

export default function TraceDetail() {
  const { traceId } = useParams();
  const [spans, setSpans] = useState<Span[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSpans, setExpandedSpans] = useState<Record<string, boolean>>(
    {}
  );

  useEffect(() => {
    async function fetchSpans() {
      if (!traceId) return;
      try {
        const response = await fetch(`/api/frontend/traces/${traceId}/spans`);
        if (!response.ok) {
          throw new Error("Failed to fetch spans");
        }
        const data = await response.json();
        setSpans(data);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("An unknown error occurred");
        }
      } finally {
        setLoading(false);
      }
    }

    fetchSpans();
  }, [traceId]);

  const toggleExpand = (spanId: string) => {
    setExpandedSpans((prev) => ({ ...prev, [spanId]: !prev[spanId] }));
  };

  const filteredSpans = spans.filter(
    (span) => span.span_data?.type && span.span_data.type !== "agent"
  );

  const sortedSpans = [...filteredSpans].sort(
    (a, b) => new Date(a.started_at).getTime() - new Date(b.started_at).getTime()
  );

  const startTimes = sortedSpans.map((s) => new Date(s.started_at).getTime());
  const endTimes = sortedSpans.map((s) => new Date(s.ended_at).getTime());
  const minTime = Math.min(...startTimes);
  const maxTime = Math.max(...endTimes);
  const totalDuration = maxTime - minTime;

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="w-full">
      <div className="overflow-hidden border border-gray-200 rounded-lg bg-white">
        <table className="min-w-full divide-y divide-gray-200 table-fixed">
          <tbody className="divide-y divide-gray-200 bg-white">
            {sortedSpans.map((span) => {
              const isExpanded = expandedSpans[span.id];
              const startTime = new Date(span.started_at).getTime();
              const endTime = new Date(span.ended_at).getTime();
              const duration = endTime - startTime;

              const leftPercent =
                totalDuration > 0
                  ? ((startTime - minTime) / totalDuration) * 100
                  : 0;
              const widthPercent =
                totalDuration > 0 ? (duration / totalDuration) * 100 : 0;

              const spanType = span.span_data.type as string;
              const config = typeDisplayConfig[spanType];
              const displayName = config?.name || spanType;
              const color = config?.color || "bg-blue-500";
              const Icon = config?.icon;

              return (
                <>
                  <tr key={span.id}>
                    <td className="w-12 px-3 py-4 text-sm text-gray-500">
                      <button
                        onClick={() => toggleExpand(span.id)}
                        className="p-1 rounded-full hover:bg-gray-100"
                      >
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </button>
                    </td>
                    <td className="w-72 whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      <div className="flex items-center">
                        {Icon && <Icon className="h-4 w-4 mr-2" />}
                        {displayName}
                      </div>
                    </td>
                    <td className="w-32 whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {duration}ms
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      <div className="relative flex items-center w-full h-4">
                        <div
                          className={`${color} absolute h-2 w-0.5 rounded-full`}
                          style={{ left: `${leftPercent}%` }}
                        />
                        <div
                          className={`${color} absolute h-0.5`}
                          style={{
                            left: `${leftPercent}%`,
                            width: `${Math.max(widthPercent, 0.4)}%`,
                          }}
                        />
                        <div
                          className={`${color} absolute h-2 w-0.5 rounded-full`}
                          style={{
                            left: `calc(${leftPercent}% + ${Math.max(
                              widthPercent,
                              0.4
                            )}%)`,
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                  {isExpanded && (
                    <tr>
                      <td
                        colSpan={4}
                        className="px-6 py-4 bg-gray-50"
                      >
                        <pre className="text-xs text-gray-700 whitespace-pre-wrap">
                          {JSON.stringify(span.span_data, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  )}
                </>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
} 