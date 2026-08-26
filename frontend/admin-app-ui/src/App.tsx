import { RequireRole } from "@are/ui-core/auth";
import { AdminPage } from "./features/admin/AdminPage";

const redirectHome = (): void => {
  window.location.replace("/");
};

export default function App() {
  return (
    <RequireRole roles={["admin"]} onDenied={redirectHome}>
      <AdminPage />
    </RequireRole>
  );
}
