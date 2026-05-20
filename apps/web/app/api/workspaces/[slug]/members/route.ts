import { and, asc, eq } from "drizzle-orm";
import { NextResponse } from "next/server";

import { db } from "@/lib/db";
import { canViewWorkspaceMembers, parseMemberRole } from "@/lib/rbac";
import { businessWorkspaces, workspaceMembers } from "@/lib/schema";
import { getSession } from "@/lib/session";

export async function GET(
  _request: Request,
  context: { params: Promise<{ slug: string }> | { slug: string } },
) {
  const { slug } = await Promise.resolve(context.params);
  const session = await getSession();
  if (!session?.user) {
    return NextResponse.json({ message: "Sign in required." }, { status: 401 });
  }

  const [workspace] = await db
    .select({ id: businessWorkspaces.id, slug: businessWorkspaces.slug })
    .from(businessWorkspaces)
    .where(eq(businessWorkspaces.slug, slug))
    .limit(1);

  if (!workspace) {
    return NextResponse.json({ message: "Workspace not found." }, { status: 404 });
  }

  const [requesterMembership] = await db
    .select({ role: workspaceMembers.role })
    .from(workspaceMembers)
    .where(
      and(
        eq(workspaceMembers.workspaceId, workspace.id),
        eq(workspaceMembers.userId, session.user.id),
      ),
    )
    .limit(1);

  const requesterRole = parseMemberRole(requesterMembership?.role);
  if (!canViewWorkspaceMembers(requesterRole)) {
    return NextResponse.json(
      { message: "Insufficient role to view members." },
      { status: 403 },
    );
  }

  const members = await db
    .select({
      userId: workspaceMembers.userId,
      role: workspaceMembers.role,
      createdAt: workspaceMembers.createdAt,
    })
    .from(workspaceMembers)
    .where(eq(workspaceMembers.workspaceId, workspace.id))
    .orderBy(asc(workspaceMembers.createdAt));

  return NextResponse.json({
    workspace: workspace.slug,
    members: members.map((member) => ({
      userId: member.userId,
      role: parseMemberRole(member.role) ?? "accountant",
      createdAt: member.createdAt,
    })),
  });
}
