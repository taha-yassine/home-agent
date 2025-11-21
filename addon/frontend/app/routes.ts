import { type RouteConfig, index, route } from "@react-router/dev/routes";

const children = [
  index("routes/index.tsx"),
  route("tools", "routes/tools.tsx"),
  route("documents", "routes/documents.tsx"),
  route("settings", "routes/settings/layout.tsx", [
    index("routes/settings/index.tsx"),
    route("backends", "routes/settings/backends.tsx"),
    route("mcp", "routes/settings/mcp.tsx"),
    route("models", "routes/settings/models.tsx"),
  ]),
  route("conversations", "routes/conversations/layout.tsx", [
    index("routes/conversations/index.tsx"),
    route(":groupId", "routes/conversations/conversation.tsx"),
  ]),
  route("usage", "routes/usage.tsx"),
];

export default (
  import.meta.env.DEV
    ? children
    : [route("api/hassio_ingress/:token", "routes/ingress.tsx", children)]
) satisfies RouteConfig;
