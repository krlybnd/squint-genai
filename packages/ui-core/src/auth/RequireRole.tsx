import { useEffect, type ReactNode } from "react";
import { useAuth } from "./AuthProvider";

export type RequireRoleProps = {
  roles: readonly string[];
  children: ReactNode;
  /** Called when access is denied; default redirects to `/`. */
  onDenied?: () => void;
  deniedFallback?: ReactNode;
};

export function RequireRole({ roles, children, onDenied, deniedFallback = null }: RequireRoleProps) {
  const auth = useAuth();
  const allowed = auth.hasAnyRole(...roles);

  useEffect(() => {
    if (!allowed && onDenied) {
      onDenied();
    }
  }, [allowed, onDenied]);

  if (!allowed) {
    if (onDenied && deniedFallback === null) {
      return null;
    }
    return <>{deniedFallback}</>;
  }
  return <>{children}</>;
}
