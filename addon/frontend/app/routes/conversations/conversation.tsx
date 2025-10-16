import { useNavigate, useParams } from "react-router";
import { useEffect, useState, Fragment } from "react";
import Loading from "../../components/Loading";
import { Button, RadioGroup, Radio } from "@headlessui/react";
import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Drill,
  Text,
  Brain,
  ArrowRightToLine,
  ArrowRightFromLine,
  Cpu,
  ChartNoAxesColumnIncreasing,
  SlidersHorizontal,
  AlertTriangle,
  MessagesSquare,
} from "lucide-react";
import type { Span, ConversationTracesResponse, TraceWithSpans } from "../../types";
import Breadcrumbs from "../../components/Breadcrumbs";
import JsonCodeBlock from "../../components/JsonCodeBlock";

type ConversationNeighbors = {
  previous: string | null;
  next: string | null;
};

function renderKeyValue(label: React.ReactNode, value: React.ReactNode) {
  return (
    <div className="mb-2">
      <div className="text-sm font-medium uppercase tracking-wide text-zinc-600 dark:text-zinc-300">{label}</div>
      <div className="mt-4 text-sm text-zinc-800 dark:text-zinc-200">{value}</div>
    </div>
  );
}

function renderObjectAsCode(obj: unknown) {
  return (
    <div className="rounded-md border border-zinc-200 dark:border-zinc-800 bg-zinc-100 dark:bg-zinc-800 overflow-hidden">
      <pre className="text-xs text-zinc-700 dark:text-zinc-300 whitespace-pre-wrap p-3 overflow-x-auto font-mono">
        {typeof obj === "string" ? obj : JSON.stringify(obj, null, 2)}
      </pre>
    </div>
  );
}

function renderGenerationPretty(spanData: { [key: string]: any }) {
  const model = spanData.model || spanData.provider || spanData.engine;

  const isEmptyValue = (val: any) => {
    if (val === null || val === undefined) return true;
    if (typeof val === "string") return val.trim().length === 0;
    if (Array.isArray(val)) return val.length === 0;
    if (typeof val === "object") return Object.keys(val).length === 0;
    return false;
  };

  const inputItems: Array<any> | undefined = Array.isArray(spanData.input)
    ? spanData.input
    : Array.isArray(spanData.messages)
    ? spanData.messages
    : undefined;

  const outputArray: Array<any> | undefined = Array.isArray(spanData.output)
    ? spanData.output
    : undefined;

  const responseObj: any | undefined = outputArray?.find(
    (o: any) => o && (o.object === "response" || Array.isArray(o.output))
  );

  const innerOutput: Array<any> | undefined = Array.isArray(responseObj?.output)
    ? responseObj.output
    : undefined;

  const reasoningItem = innerOutput?.find((i: any) => i?.type === "reasoning");
  const reasoningText: string | undefined = reasoningItem?.content
    ?.filter((c: any) => c?.type === "reasoning_text")
    .map((c: any) => c?.text)
    .filter(Boolean)
    .join("\n\n");

  const outputItems: Array<any> = Array.isArray(innerOutput)
    ? innerOutput.filter(
        (i: any) =>
          i &&
          i.type !== "function_call" &&
          i.type !== "tool" &&
          i.type !== "tool_result"
      )
    : [];

  const usage =
    spanData.usage || spanData.token_usage || responseObj?.usage || undefined;

  const modelConfig = spanData.model_config || {};
  const params: Record<string, any> = {};
  [
    "temperature",
    "top_p",
    "tool_choice",
    "parallel_tool_calls",
    "max_tokens",
    "frequency_penalty",
    "presence_penalty",
  ].forEach((k) => {
    if (spanData[k] !== undefined && spanData[k] !== null) params[k] = spanData[k];
    else if (modelConfig[k] !== undefined && modelConfig[k] !== null)
      params[k] = modelConfig[k];
  });

  const inputElements = (inputItems || [])
    .map((m: any, idx: number) => {
      const role = m?.role || m?.author || "user";
      if (role === "tool") return null;
      const content = m?.content ?? m?.text ?? m?.value ?? "";
      const isEmpty = isEmptyValue(content);
      if (isEmpty) return null;
      return (
        <div key={idx}>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-200">{String(role)}</span>
          </div>
          {renderObjectAsCode(content)}
        </div>
      );
    })
    .filter(Boolean);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {Object.keys(params).length > 0 && (
        <div>
          {renderKeyValue(
            <span className="inline-flex items-center gap-2"><SlidersHorizontal className="h-3.5 w-3.5 text-zinc-500 dark:text-zinc-400" /><span>Parameters</span></span>,
            renderObjectAsCode(params)
          )}
        </div>
      )}

      {responseObj?.error && (
        <div className="sm:col-span-2 lg:col-span-3">
          {renderKeyValue(
            <span className="inline-flex items-center gap-2"><AlertTriangle className="h-3.5 w-3.5 text-red-600 dark:text-red-400" /><span>Error</span></span>,
            <span className="text-red-600 dark:text-red-400">{String(responseObj.error)}</span>
          )}
        </div>
      )}

      {inputElements.length > 0 && (
        <div className="sm:col-span-2 lg:col-span-3">
          {renderKeyValue(
            <span className="inline-flex items-center gap-2"><ArrowRightToLine className="h-3.5 w-3.5 text-zinc-500 dark:text-zinc-400" /><span>Input</span></span>,
            <div className="space-y-2">{inputElements}</div>
          )}
        </div>
      )}

      {(() => {
        const outputElements = outputItems
          .map((item: any, idx: number) => {
            const type = item?.type;
            if (type === "reasoning") {
              const text = (item?.content || [])
                .filter((c: any) => c?.type === "reasoning_text")
                .map((c: any) => c?.text)
                .filter(Boolean)
                .join("\n\n");
              if (!text || text.trim() === "") return null;
              return (
                <details key={idx} className="group rounded-md border border-zinc-200 dark:border-zinc-800 bg-zinc-100/60 dark:bg-zinc-800/60 p-3">
                  <summary className="flex items-center cursor-pointer text-sm font-medium text-zinc-700 dark:text-zinc-200 [&::-webkit-details-marker]:hidden">
                    <span className="flex items-center gap-2">
                      <Brain className="h-3.5 w-3.5 text-zinc-500 dark:text-zinc-400" />
                      <span>Reasoning</span>
                      <ChevronRight className="h-4 w-4 text-zinc-500 dark:text-zinc-400 transition-transform group-open:rotate-90" />
                    </span>
                  </summary>
                  <div className="mx-4 mt-4 text-xs text-zinc-700 dark:text-zinc-300 whitespace-pre-wrap font-mono overflow-x-auto">{text}</div>
                </details>
              );
            }
            if (type === "message") {
              const text = (item?.content || [])
                .filter((c: any) => c?.type === "output_text")
                .map((c: any) => c?.text)
                .filter(Boolean)
                .join("\n\n");
              if (!text || text.trim() === "") return null;
              return <div key={idx}>{renderObjectAsCode(text)}</div>;
            }
            if (isEmptyValue(item)) return null;
            return <div key={idx}>{renderObjectAsCode(item)}</div>;
          })
          .filter(Boolean);
        if (outputElements.length === 0) return null;
        return (
        <div className="sm:col-span-2 lg:col-span-3">
          {renderKeyValue(
            <span className="inline-flex items-center gap-2"><ArrowRightFromLine className="h-3.5 w-3.5 text-zinc-500 dark:text-zinc-400" /><span>Output</span></span>,
            <div className="space-y-2">{outputElements}</div>
          )}
        </div>
        );
      })()}

      {model && (
        <div>
          {renderKeyValue(
            <span className="inline-flex items-center gap-2"><Cpu className="h-3.5 w-3.5 text-zinc-500 dark:text-zinc-400" /><span>Model</span></span>,
            <code>{String(model)}</code>
          )}
        </div>
      )}

      {usage && (
        <div>
          {renderKeyValue(
            <span className="inline-flex items-center gap-2"><ChartNoAxesColumnIncreasing className="h-3.5 w-3.5 text-zinc-500 dark:text-zinc-400" /><span>Usage</span></span>,
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">Prompt tokens</div>
                <div className="mt-2 text-sm text-zinc-800 dark:text-zinc-200"><code>{String(usage.input_tokens)}</code></div>
              </div>
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">Completion tokens</div>
                <div className="mt-2 text-sm text-zinc-800 dark:text-zinc-200"><code>{String(usage.output_tokens)}</code></div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function renderFunctionPretty(spanData: { [key: string]: any }) {
  const functionName = spanData.name || spanData.tool || spanData.function || spanData.func;
  const args = spanData.arguments || spanData.args || spanData.input;
  const result = spanData.output || spanData.result || spanData.return_value || spanData.response;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      {args !== undefined && (
        <div className="sm:col-span-2 lg:col-span-3">
          {renderKeyValue
          (<span className="inline-flex items-center gap-2"><ArrowRightToLine className="h-3.5 w-3.5 text-zinc-500 dark:text-zinc-400" /><span>Input</span></span>, renderObjectAsCode(args))}
        </div>
      )}
      {result !== undefined && (
        <div className="sm:col-span-2 lg:col-span-3">
          {renderKeyValue(
            <span className="inline-flex items-center gap-2"><ArrowRightFromLine className="h-3.5 w-3.5 text-zinc-500 dark:text-zinc-400" /><span>Output</span></span>,
            renderObjectAsCode(result)
          )}
        </div>
      )}
    </div>
  );
}

function renderPrettySpanContent(span: Span) {
  const spanData = span.span_data || {};
  const spanType = (spanData.type as string) || span.span_type;

  if (spanType === "generation") {
    return renderGenerationPretty(spanData);
  }

  if (spanType === "function") {
    return renderFunctionPretty(spanData);
  }

  return null;
}

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

export default function ConversationDetail() {
  const { groupId } = useParams();
  const navigate = useNavigate();
  
  const [grouped, setGrouped] = useState<ConversationTracesResponse | null>(null);
  const [neighbors, setNeighbors] = useState<ConversationNeighbors | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSpans, setExpandedSpans] = useState<Record<string, boolean>>(
    {}
  );
  const [viewModeMap, setViewModeMap] = useState<Record<string, "pretty" | "json">>({});

  const formatShortDuration = (ms: number) => {
    if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
    return `${Math.round(ms)}ms`;
  };

  useEffect(() => {
    async function fetchSpans() {
      if (!groupId) return;
      try {
        const response = await fetch(`api/frontend/conversations/${groupId}/traces`);
        if (!response.ok) {
          throw new Error("Failed to fetch spans");
        }
        const data: ConversationTracesResponse = await response.json();
        setGrouped(data);
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
      if (!groupId) return;
      try {
        const response = await fetch(`api/frontend/conversations/${groupId}/neighbors`);
        if (!response.ok) {
          throw new Error("Failed to fetch neighbors");
        }
        const data = await response.json();
        setNeighbors(data);
      } catch (err) {
        console.error(err);
      }
    }

    fetchSpans();
    fetchNeighbors();
  }, [groupId]);

  const toggleExpand = (spanId: string) => {
    setExpandedSpans((prev) => ({ ...prev, [spanId]: !prev[spanId] }));
  };

  const setViewMode = (spanId: string, mode: "pretty" | "json") => {
    setViewModeMap((prev) => ({ ...prev, [spanId]: mode }));
  };

  const groupedTraces: TraceWithSpans[] = (grouped?.traces ?? []).map((t) => ({
    ...t,
    spans: t.spans.filter((s) => s.span_data?.type && s.span_data.type !== "agent"),
  }));

  // Use a global duration across all turns so Gantt bars are proportional between turns
  const globalDuration = Math.max(
    0,
    ...groupedTraces.map((t) => new Date(t.ended_at).getTime() - new Date(t.started_at).getTime())
  );


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
              {groupedTraces.map((turn, turnIndex) => (
                <Fragment key={turn.trace_id}>
                  <tr className="bg-zinc-50 dark:bg-zinc-900">
                    <td colSpan={4} className="px-4 py-2">
                      <div className="flex items-center justify-between text-xs text-zinc-600 dark:text-zinc-400">
                        <div className="flex items-center gap-2">
                          <MessagesSquare className="h-4 w-4" />
                          <div className="text-sm  font-semibold">Turn {turnIndex + 1}</div>
                        </div>
                        <div className="ml-2">
                          {(() => {
                            const dur = new Date(turn.ended_at).getTime() - new Date(turn.started_at).getTime();
                            return (
                              <span title={`${dur} ms`} className="opacity-80">{formatShortDuration(dur)}</span>
                            );
                          })()}
                        </div>
                      </div>
                    </td>
                  </tr>
                  {(() => {
                const turnStart = new Date(turn.started_at).getTime();
                const turnEnd = new Date(turn.ended_at).getTime();
                const turnTotal = Math.max(0, turnEnd - turnStart);
                return turn.spans.map((span) => {
                const isExpanded = expandedSpans[span.id];
                const startTime = new Date(span.started_at).getTime();
                const endTime = new Date(span.ended_at).getTime();
                const duration = endTime - startTime;

                // Scale by globalDuration so that spans are proportional across different turns
                const leftPercent = globalDuration > 0 ? ((startTime - turnStart) / globalDuration) * 100 : 0;
                const widthPercent = globalDuration > 0 ? (duration / globalDuration) * 100 : 0;

                const spanType = span.span_data.type as string;
                const config = typeDisplayConfig[spanType];
                const displayName = config?.name || spanType;
                const color = config?.color || "bg-blue-500";
                const Icon = config?.icon;

                return (
                  <Fragment key={span.id}>
                    <tr>
                      <td className="w-12 px-3 py-4 text-sm text-zinc-500 dark:text-zinc-400">
                        <Button
                          onClick={() => toggleExpand(span.id)}
                          className="p-1 rounded-full data-hover:bg-zinc-100 data-hover:dark:bg-zinc-800"
                        >
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </Button>
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
                          <div className="relative">
                            <div className="absolute right-0 top-2 text-xs">
                              <RadioGroup
                                value={(viewModeMap[span.id] ?? "pretty") as "pretty" | "json"}
                                onChange={(v: "pretty" | "json") => setViewMode(span.id, v)}
                              >
                                <div className="inline-flex rounded-md border border-zinc-200 dark:border-zinc-800 overflow-hidden">
                                  <Radio value="pretty" className={({ checked }) => `${checked ? "bg-transparent text-zinc-900 dark:text-zinc-100 font-medium" : "bg-zinc-200 text-zinc-600 dark:bg-zinc-700 dark:text-zinc-300"} px-2 py-1 cursor-pointer focus:outline-none`}>
                                    Pretty
                                  </Radio>
                                  <Radio value="json" className={({ checked }) => `${checked ? "bg-transparent text-zinc-900 dark:text-zinc-100 font-medium" : "bg-zinc-200 text-zinc-600 dark:bg-zinc-700 dark:text-zinc-300"} px-2 py-1 cursor-pointer focus:outline-none`}>
                                    JSON
                                  </Radio>
                                </div>
                              </RadioGroup>
                            </div>
                            {(viewModeMap[span.id] ?? "pretty") === "json" ? (
                              <div className="pt-12">
                                <JsonCodeBlock value={span.span_data} />
                              </div>
                            ) : (
                              <div className="pt-2 text-sm text-zinc-800 dark:text-zinc-200">
                                {renderPrettySpanContent(span)}
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
                });
                  })()}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
} 