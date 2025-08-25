import { NavLink, useLocation } from "react-router";
import { useRef } from "react";
import { Menu, MenuButton, MenuItem, MenuItems } from "@headlessui/react";
import { ChevronDown } from "lucide-react";
import ThemeToggle from "./ThemeToggle";

type NavItem = {
  name: string;
  href?: string;
  children?: { name: string; href: string }[];
};

const navItems: NavItem[] = [
  { name: "Conversations", href: "/conversations" },
  { name: "Tools", href: "/tools" },
  { name: "Documents", href: "/documents" },
  {
    name: "Connections",
    children: [
      { name: "LLM", href: "/connections/LLM" },
      { name: "MCP", href: "/connections/MCP" },
    ],
  },
  { name: "Usage", href: "/usage" },
];

export default function Header() {
  const location = useLocation();
  const buttonRef = useRef<HTMLButtonElement | null>(null);

  const activeTabClasses =
    "bg-zinc-200 dark:bg-zinc-700 text-zinc-900 dark:text-white";
  const inactiveTabClasses =
    "text-zinc-500 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-white";

  return (
    <header className="bg-white dark:bg-zinc-950 text-zinc-900 dark:text-white border-b border-zinc-200 dark:border-zinc-800">
      <nav className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-bold">Home Agent</h1>
          </div>
          <div className="flex justify-center flex-1">
            <div className="flex items-baseline space-x-4">
              {navItems.map((item) => {
                const isParentActive = item.href
                  ? location.pathname.startsWith(item.href)
                  : (item.children ?? []).some((c) =>
                      location.pathname.startsWith(c.href)
                    );

                if (!item.children) {
                  return (
                    <NavLink
                      key={item.name}
                      to={item.href!}
                      className={({ isActive }) =>
                        `px-3 py-2 rounded-md text-sm font-medium ${
                          isActive ? activeTabClasses : inactiveTabClasses
                        }`
                      }
                    >
                      {item.name}
                    </NavLink>
                  );
                }

                return (
                  <Menu as="div" className="relative" key={item.name}>
                    {({ open }) => (
                      <div
                        onMouseEnter={() => {
                          if (!open) buttonRef.current?.click();
                        }}
                      >
                        <MenuButton
                          ref={buttonRef}
                          className={`px-3 py-2 rounded-md text-sm font-medium cursor-pointer ${
                            isParentActive ? activeTabClasses : inactiveTabClasses
                          }`}
                        >
                          <span className="inline-flex items-center gap-1">
                            {item.name}
                            <ChevronDown
                              className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`}
                              aria-hidden="true"
                            />
                          </span>
                        </MenuButton>
                        <MenuItems
                          transition
                          anchor="bottom start"
                          className="absolute left-0 mt-2 w-44 origin-top-left divide-y divide-zinc-100 rounded-md bg-white dark:bg-zinc-900 shadow-lg ring-1 ring-black/5 focus:outline-none transition data-[closed]:scale-95 data-[closed]:opacity-0"
                        >
                          <div className="px-1 py-1">
                            {(item.children ?? []).map((child) => (
                              <MenuItem
                                key={child.href}
                                as={NavLink}
                                to={child.href}
                                className="group flex w-full items-center rounded-md px-2 py-2 text-sm text-zinc-700 dark:text-zinc-200 data-[focus]:bg-zinc-100 dark:data-[focus]:bg-zinc-800 data-[focus]:text-zinc-900 dark:data-[focus]:text-white"
                              >
                                {child.name}
                              </MenuItem>
                            ))}
                          </div>
                        </MenuItems>
                      </div>
                    )}
                  </Menu>
                );
              })}
            </div>
          </div>
          <div className="flex items-center justify-end">
            <ThemeToggle />
          </div>
        </div>
      </nav>
    </header>
  );
}
