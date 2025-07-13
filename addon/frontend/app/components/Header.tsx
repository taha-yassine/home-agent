import { NavLink } from "react-router";

const tabs = [
  { name: "Conversations", href: "/" },
  { name: "Models", href: "/models" },
  { name: "Documents", href: "/documents" },
  { name: "Backends", href: "/backends" },
];

export default function Header() {
  return (
    <header className="bg-white dark:bg-zinc-950 text-zinc-900 dark:text-white border-b border-zinc-200 dark:border-zinc-800">
      <nav className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-bold">Home Agent</h1>
          </div>
          <div className="flex justify-center flex-1">
            <div className="flex items-baseline space-x-4">
              {tabs.map((tab) => (
                <NavLink
                  key={tab.name}
                  to={tab.href}
                  className={({ isActive }) =>
                    `px-3 py-2 rounded-md text-sm font-medium ${
                      isActive
                        ? "bg-zinc-200 dark:bg-zinc-700 text-zinc-900 dark:text-white"
                        : "text-zinc-500 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-white"
                    }`
                  }
                >
                  {tab.name}
                </NavLink>
              ))}
            </div>
          </div>
          <div className="flex items-center justify-end">
          </div>
        </div>
      </nav>
    </header>
  );
}
