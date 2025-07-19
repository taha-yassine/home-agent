import { Outlet } from "react-router";
import Breadcrumbs from "../../components/Breadcrumbs";

export default function ConversationsLayout() {
  return (
    <div className="p-8">
      <Breadcrumbs />
      <Outlet />
    </div>
  );
} 