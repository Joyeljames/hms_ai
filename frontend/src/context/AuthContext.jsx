import { createContext, useContext, useState, useEffect } from "react";
import { login as loginApi } from "../api/endpoints";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On app start — check if already logged in
  useEffect(() => {
    const savedUser = localStorage.getItem("hms_user");
    const token = localStorage.getItem("hms_token");

    if (savedUser && token) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    const response = await loginApi(username, password);
    const data = response.data;

    localStorage.setItem("hms_token", data.access_token);

    const userData = {
      name: data.name,
      role: data.role,
      clinic_id: data.clinic_id,
      user_id: data.user_id,
    };

    localStorage.setItem("hms_user", JSON.stringify(userData));
    setUser(userData);

    return userData;
  };

  const logout = () => {
    localStorage.removeItem("hms_token");
    localStorage.removeItem("hms_user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}