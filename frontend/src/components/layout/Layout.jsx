import { NavLink, useNavigate } from "react-router-dom";
import { LogOut } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

const TABS = [
  { to: "/reception", label: "Reception", roles: ["receptionist", "admin"] },
  { to: "/doctor", label: "Doctor", roles: ["doctor", "admin"] },
  { to: "/pharmacy", label: "Pharmacy", roles: ["pharmacist", "admin"] },
  { to: "/admin", label: "Admin", roles: ["admin", "superadmin"] },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const visibleTabs = TABS.filter((t) => t.roles.includes(user?.role));

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-8">
            <span className="text-lg font-semibold text-gray-900">HMS AI</span>

            <nav className="flex gap-1">
              {visibleTabs.map((tab) => (
                <NavLink
                  key={tab.to}
                  to={tab.to}
                  className={({ isActive }) =>
                    `rounded-lg px-3 py-1.5 text-sm font-medium ${
                      isActive
                        ? "bg-gray-900 text-white"
                        : "text-gray-600 hover:bg-gray-100"
                    }`
                  }
                >
                  {tab.label}
                </NavLink>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">{user?.name}</p>
              <p className="text-xs capitalize text-gray-500">{user?.role}</p>
            </div>
            <button
              onClick={handleLogout}
              className="rounded-lg p-2 text-gray-500 hover:bg-gray-100"
              title="Logout"
            >
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-6">{children}</main>
    </div>
  );
}
