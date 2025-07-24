import { Outlet } from "react-router";
import PageLayout from "../../components/PageLayout";

export default function ConversationsLayout() {
  return (
    <PageLayout>
      <Outlet />
    </PageLayout>
  );
} 