import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/index.tsx"),
  route("models", "routes/models.tsx"),
  route("documents", "routes/documents.tsx"),
  route("backends", "routes/backends.tsx"),
] satisfies RouteConfig;
