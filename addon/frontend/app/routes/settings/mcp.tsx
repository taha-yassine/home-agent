import Breadcrumbs from "../../components/Breadcrumbs";

export default function SettingsMcp() {
  return (
    <>
      <div className="flex justify-between items-center mb-4 min-h-10">
        <Breadcrumbs />
      </div>
      <div className="border border-zinc-200 dark:border-zinc-800 rounded-lg bg-white dark:bg-zinc-950 p-8 text-center">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          MCP support is still in development.
        </p>
      </div>
    </>
  );
}

