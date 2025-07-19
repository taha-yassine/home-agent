import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/index.tsx"),
  route("models", "routes/models.tsx"),
  route("documents", "routes/documents.tsx"),
  route("backends", "routes/backends.tsx"),
  route("conversations", "routes/conversations/layout.tsx", [
    index("routes/conversations/index.tsx"),
    route(":traceId", "routes/conversations/trace.tsx"),
  ]),
] satisfies RouteConfig;
