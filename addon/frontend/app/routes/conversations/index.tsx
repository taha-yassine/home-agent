import { useEffect, useState } from "react";
import { Link } from "react-router";
import Loading from "../../components/Loading";
import TimeAgo from "timeago-react";
import { SquareChartGantt } from "lucide-react";
import Breadcrumbs from "../../components/Breadcrumbs";

interface Conversation {
  group_id: string;
  started_at: string;
  instruction: string;
}

export default function Conversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchConversations() {
      try {
        const response = await fetch("api/frontend/conversations");
        if (!response.ok) {
          throw new Error("Failed to fetch conversations");
        }
        const data = await response.json();
        setConversations(data.conversations);
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

    fetchConversations();
  }, []);

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
      <div className="overflow-hidden border border-zinc-200 dark:border-zinc-800 rounded-lg">
        <table className="min-w-full divide-y divide-zinc-200 dark:divide-zinc-800">
          <thead className="bg-zinc-50 dark:bg-zinc-900">
            <tr>
              <th
                scope="col"
                className="pl-4 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider"
              ></th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider"
              >
                ID
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider"
              >
                Started At
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-wider"
              >
                Instruction
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-zinc-950 divide-y divide-zinc-200 dark:divide-zinc-800">
            {conversations.map((conversation) => (
              <tr key={conversation.group_id} className="hover:bg-zinc-100 dark:hover:bg-zinc-900">
                <td className="pl-4 py-4 whitespace-nowrap text-sm font-medium">
                  <Link
                    to={`${conversation.group_id}`}
                    className="text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white"
                    title="View conversation details"
                    relative="path"
                  >
                    <SquareChartGantt className="h-5 w-5" />
                  </Link>
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-zinc-900 dark:text-zinc-100">
                  {conversation.group_id}
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-zinc-500 dark:text-zinc-400">
                  <TimeAgo
                    title={new Date(conversation.started_at).toLocaleString()}
                    datetime={new Date(conversation.started_at)}
                  />
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-zinc-500 dark:text-zinc-400">
                  {conversation.instruction}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
} 