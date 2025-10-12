import { useNavigate, useParams } from "react-router";
import { useEffect, useState } from "react";
import Loading from "../../components/Loading";
import { Button } from "@headlessui/react";
import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Drill,
  Text,
} from "lucide-react";
import type { Span } from "../../types";
import Breadcrumbs from "../../components/Breadcrumbs";

type TraceNeighbors = {
  previous: string | null;
  next: string | null;
};

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
  const navigate = useNavigate();
  
  const [spans, setSpans] = useState<Span[]>([]);
  const [neighbors, setNeighbors] = useState<TraceNeighbors | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSpans, setExpandedSpans] = useState<Record<string, boolean>>(
    {}
  );

  useEffect(() => {
    async function fetchSpans() {
      if (!traceId) return;
      try {
        const response = await fetch(`api/frontend/traces/${traceId}/spans`);
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

    async function fetchNeighbors() {
      if (!traceId) return;
      try {
        const response = await fetch(`api/frontend/traces/${traceId}/neighbors`);
        if (!response.ok) {
          throw new Error("Failed to fetch neighbors");
        }
        const data = await response.json();
        setNeighbors(data);
      } catch (err) {
        // Not a critical error, so we just log it
        console.error(err);
      }
    }

    fetchSpans();
    fetchNeighbors();
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
    return <Loading />;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <>
      <div className="flex justify-between items-center mb-4 min-h-10">
        <Breadcrumbs />
        <div className="flex justify-end gap-2 mb-4">
          <Button
            onClick={() =>
              neighbors?.previous && navigate(`../${neighbors.previous}`)
            }
            className="px-2 py-1 text-sm rounded-md bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 data-hover:bg-zinc-100 data-hover:dark:bg-zinc-800 data-disabled:bg-zinc-100 data-disabled:text-zinc-400 data-disabled:dark:bg-zinc-800 data-disabled:dark:text-zinc-600 data-disabled:cursor-not-allowed data-disabled:border-transparent"
            disabled={!neighbors?.previous}
          >
            <div className="flex items-center">
              <ChevronLeft className="h-4 w-4" />
              <span className="ml-2">Previous</span>
            </div>
          </Button>
          <Button
            onClick={() =>
              neighbors?.next && navigate(`../${neighbors.next}`)
            }
            className="px-2 py-1 text-sm rounded-md bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 data-hover:bg-zinc-100 data-hover:dark:bg-zinc-800 data-disabled:bg-zinc-100 data-disabled:text-zinc-400 data-disabled:dark:bg-zinc-800 data-disabled:dark:text-zinc-600 data-disabled:cursor-not-allowed data-disabled:border-transparent"
            disabled={!neighbors?.next}
          >
            <div className="flex items-center">
              <span className="mr-2">Next</span>
              <ChevronRight className="h-4 w-4" />
            </div>
          </Button>
        </div>
      </div>
    <div className="w-full">
      <div className="overflow-hidden border border-zinc-200 dark:border-zinc-800 rounded-lg bg-white dark:bg-zinc-950">
        <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800 table-fixed">
          <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800 bg-white dark:bg-zinc-950">
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
                    <td className="w-12 px-3 py-4 text-sm text-zinc-500 dark:text-zinc-400">
                      <button
                        onClick={() => toggleExpand(span.id)}
                        className="p-1 rounded-full hover:bg-zinc-100 dark:hover:bg-zinc-800"
                      >
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </button>
                    </td>
                    <td className="w-72 whitespace-nowrap px-3 py-4 text-sm text-zinc-500 dark:text-zinc-400">
                      <div className="flex items-center">
                        {Icon && <Icon className="h-4 w-4 mr-2" />}
                        <div>
                          {displayName}
                          {spanType === "function" && span.span_data?.name && (
                            <div className="text-xs text-zinc-400 dark:text-zinc-500">
                              {span.span_data.name}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="w-32 whitespace-nowrap px-3 py-4 text-sm text-zinc-500 dark:text-zinc-400">
                      {duration}ms
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-zinc-500 dark:text-zinc-400">
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
                        className="px-6 py-4 bg-zinc-50 dark:bg-zinc-900"
                      >
                        <pre className="text-xs text-zinc-700 dark:text-zinc-300 whitespace-pre-wrap">
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
    </>
  );
} 