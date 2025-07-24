import Breadcrumbs from "./Breadcrumbs";

export default function PageLayout({
  children,
  actions,
}: {
  children: React.ReactNode;
  actions?: React.ReactNode;
}) {
  return (
    <main className="p-8">
      <div className="flex justify-between items-center mb-4 min-h-10">
        <Breadcrumbs />
        {actions && <div>{actions}</div>}
      </div>
      {children}
    </main>
  );
} 