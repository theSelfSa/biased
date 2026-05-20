import { memberRoleSchema } from "@biased/contracts";
import { and, eq } from "drizzle-orm";
import { NextResponse } from "next/server";

import { db } from "@/lib/db";
import { canManageWorkspaceMembers, parseMemberRole } from "@/lib/rbac";
import { businessWorkspaces, workspaceMembers } from "@/lib/schema";
import { getSession } from "@/lib/session";

type RoleUpdateRequest = {
  role?: string;
};

export async function PATCH(
  request: Request,
  context:
    | { params: Promise<{ slug: string; userId: string }> }
    | { params: { slug: string; userId: string } },
) {
  const { slug, userId } = await Promise.resolve(context.params);
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
  if (!canManageWorkspaceMembers(requesterRole)) {
    return NextResponse.json(
      { message: "Only owners can update member roles." },
      { status: 403 },
    );
  }

  const body = (await request.json()) as RoleUpdateRequest;
  const parsedRole = memberRoleSchema.safeParse(body.role);
  if (!parsedRole.success) {
    return NextResponse.json(
      { message: "Invalid role. Use owner, manager, or accountant." },
      { status: 400 },
    );
  }

  if (userId === session.user.id && parsedRole.data !== "owner") {
    return NextResponse.json(
      { message: "Owner cannot demote themselves." },
      { status: 400 },
    );
  }

  const [updated] = await db
    .update(workspaceMembers)
    .set({ role: parsedRole.data })
    .where(
      and(
        eq(workspaceMembers.workspaceId, workspace.id),
        eq(workspaceMembers.userId, userId),
      ),
    )
    .returning({
      userId: workspaceMembers.userId,
      role: workspaceMembers.role,
      createdAt: workspaceMembers.createdAt,
    });

  if (!updated) {
    return NextResponse.json({ message: "Member not found." }, { status: 404 });
  }

  return NextResponse.json({
    updated: true,
    member: {
      userId: updated.userId,
      role: parseMemberRole(updated.role) ?? parsedRole.data,
      createdAt: updated.createdAt,
    },
  });
}
