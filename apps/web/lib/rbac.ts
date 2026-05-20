import { memberRoleSchema, type MemberRole } from "@biased/contracts";

const roleRank: Record<MemberRole, number> = {
  accountant: 1,
  manager: 2,
  owner: 3,
};

export function parseMemberRole(value: string | null | undefined) {
  const parsed = memberRoleSchema.safeParse(value);
  return parsed.success ? parsed.data : null;
}

export function hasRequiredRole(
  currentRole: MemberRole | null,
  minimumRole: MemberRole,
) {
  if (!currentRole) {
    return false;
  }
  return roleRank[currentRole] >= roleRank[minimumRole];
}

export function canViewWorkspaceMembers(currentRole: MemberRole | null) {
  return hasRequiredRole(currentRole, "manager");
}

export function canManageWorkspaceMembers(currentRole: MemberRole | null) {
  return hasRequiredRole(currentRole, "owner");
}
