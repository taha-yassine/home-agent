import { Link, useLocation } from "react-router";
import { Slash } from "lucide-react";
import { useIngressBasePath } from "../hooks/useIngressBase";

export default function Breadcrumbs() {
  const location = useLocation();
  // Minimal overrides to map acronym slugs to display labels while keeping URLs lowercase (e.g., "llm" -> "LLM").
  const LABEL_OVERRIDES: Record<string, string> = { llm: "LLM", mcp: "MCP" };
  const pathnameBase = useIngressBasePath();
  // Strip the ingress base from the current pathname to compute breadcrumb parts.
  const relativePathname =
    pathnameBase && location.pathname.startsWith(pathnameBase)
      ? location.pathname.slice(pathnameBase.length)
      : location.pathname;
  const pathnames = relativePathname.split("/").filter((x) => x);

 

  if (pathnames.length === 0) {
    return null;
  }

  return (
    <nav className="flex" aria-label="Breadcrumb">
      <ol className="inline-flex items-center">
        {pathnames.map((value, index) => {
          const relativeTo = `/${pathnames.slice(0, index + 1).join("/")}`;
          // Re-prefix links with the ingress base so navigation stays under ingress.
          const to = `${pathnameBase}${relativeTo}`;
          const isLast = index === pathnames.length - 1;

          const lower = value.toLowerCase();
          let name = LABEL_OVERRIDES[lower] ?? (value.charAt(0).toUpperCase() + value.slice(1));

          return (
            <li key={to}>
              <div className="flex items-center">
                {index > 0 && (
                  <Slash className="mx-3 w-4 h-4 text-zinc-400 dark:text-zinc-500" />
                )}
                {isLast ? (
                  <span className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
                    {name}
                  </span>
                ) : (
                  <Link
                    to={to}
                    className="text-sm font-medium text-zinc-700 hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-white"
                  >
                    {name}
                  </Link>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
} 