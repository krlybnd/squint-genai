import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  addTenantMember,
  fetchTenantMembersPage,
  fetchUsersPage,
  removeTenantMember,
  updateTenantMemberRoles,
  type TenantMember,
  type User,
} from "../../api/admin";
import { MembershipPanel, type MembershipRow } from "./MembershipPanel";

const PAGE_SIZE = 50;

type TenantMembersSectionProps = {
  tenantAlias: string;
  onMembershipChanged?: (username?: string) => void;
};

export function TenantMembersSection({ tenantAlias, onMembershipChanged }: TenantMembersSectionProps) {
  const { t } = useTranslation();
  const [members, setMembers] = useState<TenantMember[]>([]);
  const [membersFirst, setMembersFirst] = useState(0);
  const [membersHasMore, setMembersHasMore] = useState(false);
  const [loadingMembers, setLoadingMembers] = useState(true);
  const [loadingMoreMembers, setLoadingMoreMembers] = useState(false);

  const [userSearch, setUserSearch] = useState("");
  const [userCandidates, setUserCandidates] = useState<User[]>([]);
  const [usersFirst, setUsersFirst] = useState(0);
  const [usersHasMore, setUsersHasMore] = useState(false);
  const [loadingUsers, setLoadingUsers] = useState(false);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pickUsername, setPickUsername] = useState("");

  const loadMembersPage = useCallback(
    async (first: number, append: boolean) => {
      if (append) setLoadingMoreMembers(true);
      else setLoadingMembers(true);
      setError(null);
      try {
        const page = await fetchTenantMembersPage(tenantAlias, { first, max: PAGE_SIZE });
        setMembers((prev) => (append ? [...prev, ...page.items] : page.items));
        setMembersFirst(first + page.items.length);
        setMembersHasMore(page.has_more);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        if (!append) setMembers([]);
      } finally {
        setLoadingMembers(false);
        setLoadingMoreMembers(false);
      }
    },
    [tenantAlias],
  );

  useEffect(() => {
    setMembers([]);
    setMembersFirst(0);
    void loadMembersPage(0, false);
  }, [loadMembersPage]);

  const loadUserCandidates = useCallback(async (search: string, first: number, append: boolean) => {
    setLoadingUsers(true);
    setError(null);
    try {
      const page = await fetchUsersPage({ search: search.trim() || undefined, first, max: PAGE_SIZE });
      setUserCandidates((prev) => (append ? [...prev, ...page.items] : page.items));
      setUsersFirst(first + page.items.length);
      setUsersHasMore(page.has_more);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      if (!append) setUserCandidates([]);
    } finally {
      setLoadingUsers(false);
    }
  }, []);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      setUsersFirst(0);
      void loadUserCandidates(userSearch, 0, false);
    }, 280);
    return () => window.clearTimeout(handle);
  }, [userSearch, loadUserCandidates]);

  const memberUsernames = useMemo(() => new Set(members.map((m) => m.username)), [members]);

  const addableOptions = useMemo(() => {
    return userCandidates
      .filter((u) => !memberUsernames.has(u.username))
      .map((u) => ({
        value: u.username,
        label: u.email ? `${u.username} (${u.email})` : u.username,
      }));
  }, [userCandidates, memberUsernames]);

  const selectOptions = useMemo(
    () => [{ value: "", label: t("admin.selectUser") }, ...addableOptions],
    [addableOptions, t],
  );

  async function handleAdd() {
    const username = pickUsername.trim();
    if (!username) return;
    setBusy(true);
    setError(null);
    try {
      await addTenantMember(tenantAlias, username, ["read"]);
      setPickUsername("");
      await loadMembersPage(0, false);
      onMembershipChanged?.(username);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleRolesChange(username: string, roles: string[]) {
    const previous = members.find((m) => m.username === username)?.roles ?? [];
    setMembers((prev) =>
      prev.map((member) => (member.username === username ? { ...member, roles } : member)),
    );
    setError(null);
    try {
      const updated = await updateTenantMemberRoles(tenantAlias, username, roles);
      setMembers((prev) =>
        prev.map((member) =>
          member.username === username ? { ...member, roles: updated.roles } : member,
        ),
      );
      onMembershipChanged?.(username);
    } catch (err) {
      setMembers((prev) =>
        prev.map((member) =>
          member.username === username ? { ...member, roles: previous } : member,
        ),
      );
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function handleRemove(username: string) {
    if (!window.confirm(t("admin.confirmRemoveMember", { username }))) return;
    setBusy(true);
    setError(null);
    try {
      await removeTenantMember(tenantAlias, username);
      await loadMembersPage(0, false);
      onMembershipChanged?.(username);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const items: MembershipRow[] = members.map((member) => ({
    id: member.id,
    primary: member.username,
    secondary: member.email ?? undefined,
    roles: member.roles ?? [],
    rolesDisabled: busy,
    onRolesChange: (roles) => void handleRolesChange(member.username, roles),
    actions: [
      {
        key: "remove",
        label: t("admin.removeMember"),
        variant: "danger" as const,
        disabled: busy,
        onClick: () => void handleRemove(member.username),
      },
    ],
  }));

  return (
    <MembershipPanel
      error={error}
      loading={loadingMembers}
      loadingMessage={t("admin.loading")}
      emptyMessage={t("admin.noMembers")}
      items={items}
      search={{
        label: t("admin.searchUsers"),
        placeholder: t("admin.searchUsersPlaceholder"),
        value: userSearch,
        onChange: setUserSearch,
        disabled: busy,
      }}
      add={{
        value: pickUsername,
        options: selectOptions,
        onChange: setPickUsername,
        placeholder: loadingUsers ? t("admin.loading") : t("admin.selectUser"),
        ariaLabel: t("admin.selectUser"),
        disabled: busy || loadingUsers || addableOptions.length === 0,
        buttonLabel: t("admin.addMember"),
        onAdd: () => void handleAdd(),
        addDisabled: busy || !pickUsername.trim(),
      }}
      loadMore={[
        ...(usersHasMore
          ? [
              {
                key: "users",
                label: t("admin.loadMoreUsers"),
                loadingLabel: t("admin.loading"),
                onClick: () => void loadUserCandidates(userSearch, usersFirst, true),
                disabled: loadingUsers || busy,
                loading: loadingUsers,
                placement: "before-list" as const,
              },
            ]
          : []),
        ...(membersHasMore
          ? [
              {
                key: "members",
                label: t("admin.loadMoreMembers"),
                loadingLabel: t("admin.loading"),
                onClick: () => void loadMembersPage(membersFirst, true),
                disabled: loadingMoreMembers || busy,
                loading: loadingMoreMembers,
                placement: "after-list" as const,
              },
            ]
          : []),
      ]}
    />
  );
}
