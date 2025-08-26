import { useEffect, useState } from "react";
import Loading from "../components/Loading";
import SchemaViewer from "../components/SchemaViewer";
import Breadcrumbs from "../components/Breadcrumbs";

interface Tool {
  name: string;
  description: string;
  params_json_schema: object;
}

export default function Tools() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTools();
  }, []);

  async function fetchTools() {
    try {
      setLoading(true);
      const response = await fetch("/api/frontend/tools");
      if (!response.ok) {
        throw new Error("Failed to fetch tools");
      }
      const data = await response.json();
      setTools(data);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <Loading />;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <>
      <div className="flex justify-between items-center mb-4 min-h-10">
        <Breadcrumbs />
      </div>
      <div className="overflow-hidden border border-zinc-200 dark:border-zinc-800 rounded-lg bg-white dark:bg-zinc-950">
        <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
          <thead className="bg-zinc-50 dark:bg-zinc-900">
            <tr>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider"
              >
                Name
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider"
              >
                Description
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider"
              >
                Parameters
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800 bg-white dark:bg-zinc-950">
            {tools.map((tool) => (
              <tr key={tool.name}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-zinc-900 dark:text-zinc-100">
                  {tool.name}
                </td>
                <td className="px-6 py-4 whitespace-normal text-sm text-zinc-500 dark:text-zinc-400">
                  {tool.description}
                </td>
                <td className="px-6 py-4 text-sm text-zinc-500 dark:text-zinc-400">
                  <SchemaViewer schema={tool.params_json_schema} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
} 