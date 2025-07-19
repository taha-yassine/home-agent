import { useEffect, useState } from "react";
import { Link } from "react-router";
import TimeAgo from "timeago-react";
import { SquareChartGantt } from "lucide-react";

interface Conversation {
  id: string;
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
        const response = await fetch("/api/frontend/conversations");
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
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="overflow-hidden border border-gray-200 rounded-lg">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th
              scope="col"
              className="pl-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            ></th>
            <th
              scope="col"
              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              ID
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Started At
            </th>
            <th
              scope="col"
              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Instruction
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {conversations.map((conversation) => (
            <tr key={conversation.id} className="hover:bg-gray-100">
              <td className="pl-4 py-4 whitespace-nowrap text-sm font-medium">
                <Link
                  to={`/conversations/${conversation.id}`}
                  className="text-gray-500 hover:text-gray-900"
                  title="View conversation details"
                >
                  <SquareChartGantt className="h-5 w-5" />
                </Link>
              </td>
              <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {conversation.id}
              </td>
              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                <TimeAgo
                  title={new Date(conversation.started_at).toLocaleString()}
                  datetime={new Date(conversation.started_at)}
                />
              </td>
              <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                {conversation.instruction}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
} 