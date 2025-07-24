import { Link, useLocation } from "react-router";
import { Slash } from "lucide-react";

export default function Breadcrumbs() {
  const location = useLocation();
  const pathnames = location.pathname.split("/").filter((x) => x);

  if (pathnames.length === 0) {
    return null;
  }

  return (
    <nav className="flex" aria-label="Breadcrumb">
      <ol className="inline-flex items-center">
        {pathnames.map((value, index) => {
          const to = `/${pathnames.slice(0, index + 1).join("/")}`;
          const isLast = index === pathnames.length - 1;

          let name = value;
          name = value.charAt(0).toUpperCase() + value.slice(1);

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