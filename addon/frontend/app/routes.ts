import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/index.tsx"),
  route("tools", "routes/tools.tsx"),
  route("documents", "routes/documents.tsx"),
  route("connections", "routes/connections.tsx"),
  route("conversations", "routes/conversations/layout.tsx", [
    index("routes/conversations/index.tsx"),
    route(":traceId", "routes/conversations/trace.tsx"),
  ]),
] satisfies RouteConfig;
