import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Splash from "./pages/Splash";
import Login from "./pages/Login";
import ReceptionDashboard from "./pages/reception/ReceptionDashboard";
import DoctorDashboard from "./pages/doctor/DoctorDashboard";
import PharmacyDashboard from "./pages/pharmacy/PharmacyDashboard";
import AdminDashboard from "./pages/admin/AdminDashboard";

function RoleRedirect() {
  const { user, loading } = useAuth();

  if (loading) return <div className="p-8">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;

  const routes = {
    receptionist: "/reception",
    doctor: "/doctor",
    pharmacist: "/pharmacy",
    admin: "/admin",
    superadmin: "/admin",
  };

  return <Navigate to={routes[user.role] || "/login"} replace />;
}

export default function App() {
  const [showSplash, setShowSplash] = useState(true);

  const dismissSplash = () => setShowSplash(false);

  return (
    <AuthProvider>
      {showSplash && <Splash onDone={dismissSplash} />}

      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route path="/" element={<RoleRedirect />} />

          <Route
            path="/reception"
            element={
              <ProtectedRoute allowedRoles={["receptionist", "admin"]}>
                <ReceptionDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/doctor"
            element={
              <ProtectedRoute allowedRoles={["doctor", "admin"]}>
                <DoctorDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/pharmacy"
            element={
              <ProtectedRoute allowedRoles={["pharmacist", "admin"]}>
                <PharmacyDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRoles={["admin", "superadmin"]}>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}