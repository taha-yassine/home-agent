import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/index.tsx"),
  route("tools", "routes/tools.tsx"),
  route("documents", "routes/documents.tsx"),
  route("connections", "routes/connections/layout.tsx", [
    index("routes/connections/index.tsx"),
    route("llm", "routes/connections/llm.tsx"),
    route("mcp", "routes/connections/mcp.tsx"),
  ]),
  route("conversations", "routes/conversations/layout.tsx", [
    index("routes/conversations/index.tsx"),
    route(":traceId", "routes/conversations/trace.tsx"),
  ]),
  route("usage", "routes/usage.tsx"),
] satisfies RouteConfig;
