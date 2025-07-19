import { Link, useLocation } from "react-router";
import { Slash } from "lucide-react";

export default function Breadcrumbs() {
  const location = useLocation();
  const pathnames = location.pathname.split("/").filter((x) => x);

  if (pathnames.length === 0) {
    return null;
  }

  return (
    <nav className="flex mb-4" aria-label="Breadcrumb">
      <ol className="inline-flex items-center">
        {pathnames.map((value, index) => {
          const to = `/${pathnames.slice(0, index + 1).join("/")}`;
          const isLast = index === pathnames.length - 1;

          let name = value;
          if (index === 0 && value === "conversations") {
            name = "Conversations";
          }

          return (
            <li key={to}>
              <div className="flex items-center">
                {index > 0 && (
                  <Slash className="mx-3 w-4 h-4 text-gray-400" />
                )}
                {isLast ? (
                  <span className="text-sm font-medium text-gray-500">
                    {name}
                  </span>
                ) : (
                  <Link
                    to={to}
                    className="text-sm font-medium text-gray-700 hover:text-gray-900"
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