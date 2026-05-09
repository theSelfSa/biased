import { AppShell } from "@/components/app-shell";
import { getSession } from "@/lib/session";

export default async function ProductLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getSession();

  return (
    <AppShell
      userLabel={session?.user?.email ?? "Demo owner workspace"}
    >
      {children}
    </AppShell>
  );
}
