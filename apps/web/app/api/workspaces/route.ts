import { eq } from "drizzle-orm";
import { NextResponse } from "next/server";

import { db } from "@/lib/db";
import { businessWorkspaces, workspaceMembers } from "@/lib/schema";
import { getSession } from "@/lib/session";

export async function POST(request: Request) {
  const session = await getSession();

  if (!session?.user) {
    return NextResponse.json(
      { message: "Sign in before creating a workspace." },
      { status: 401 },
    );
  }

  const body = (await request.json()) as { name?: string; slug?: string };
  const name = body.name?.trim();
  const slug = body.slug?.trim();

  if (!name || !slug) {
    return NextResponse.json(
      { message: "Workspace name and slug are required." },
      { status: 400 },
    );
  }

  const existing = await db
    .select({ id: businessWorkspaces.id })
    .from(businessWorkspaces)
    .where(eq(businessWorkspaces.slug, slug))
    .limit(1);

  if (existing.length > 0) {
    return NextResponse.json(
      { message: "That workspace slug is already taken." },
      { status: 409 },
    );
  }

  const [workspace] = await db
    .insert(businessWorkspaces)
    .values({
      name,
      slug,
    })
    .returning();

  await db.insert(workspaceMembers).values({
    workspaceId: workspace.id,
    userId: session.user.id,
    role: "owner",
  });

  return NextResponse.json({
    message: "Workspace created successfully.",
    workspace,
  });
}
