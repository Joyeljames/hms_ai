import { useEffect, useState } from "react";
import { UserPlus } from "lucide-react";
import { getAllStaff, createStaff, deactivateStaff } from "../../api/endpoints";
import { useAuth } from "../../context/AuthContext";

const ROLES = ["receptionist", "doctor", "pharmacist", "admin"];
const EMPTY = { name: "", username: "", password: "", role: "receptionist" };

export default function StaffPanel() {
  const { user } = useAuth();
  const [staff, setStaff] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [showForm, setShowForm] = useState(false);
  const [message, setMessage] = useState(null);

  const flash = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const load = async () => {
    try {
      const res = await getAllStaff();
      setStaff(res.data);
    } catch {
      flash("error", "Could not load staff");
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    if (!form.name || !form.username || !form.password) {
      return flash("error", "All fields are required");
    }
    try {
      await createStaff(form);
      flash("success", `${form.name} added as ${form.role}`);
      setForm(EMPTY);
      setShowForm(false);
      load();
    } catch (err) {
      flash("error", err.response?.data?.detail || "Could not create staff");
    }
  };

  const handleDeactivate = async (id, name) => {
    if (!window.confirm(`Deactivate ${name}? They will no longer be able to log in.`)) return;
    try {
      await deactivateStaff(id);
      flash("success", `${name} deactivated`);
      load();
    } catch (err) {
      flash("error", err.response?.data?.detail || "Could not deactivate");
    }
  };

  return (
    <div className="space-y-4">
      {message && (
        <div className={`rounded-lg px-4 py-2 text-sm ${
          message.type === "success" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-700"
        }`}>{message.text}</div>
      )}

      <button
        onClick={() => setShowForm(!showForm)}
        className="flex items-center gap-2 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
      >
        <UserPlus size={16} />
        {showForm ? "Cancel" : "Add staff"}
      </button>

      {showForm && (
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <h3 className="mb-3 text-sm font-semibold text-gray-900">New staff account</h3>
          <div className="grid gap-3 md:grid-cols-4">
            <Field label="Full name" value={form.name}
              onChange={(v) => setForm({ ...form, name: v })} />
            <Field label="Username" value={form.username}
              onChange={(v) => setForm({ ...form, username: v })} />
            <Field label="Password" type="password" value={form.password}
              onChange={(v) => setForm({ ...form, password: v })} />
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Role</label>
              <select
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm capitalize"
              >
                {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
          </div>
          <button
            onClick={handleCreate}
            className="mt-4 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
          >
            Create account
          </button>
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-600">
            <tr>
              <th className="px-4 py-2.5 text-left font-medium">Name</th>
              <th className="px-4 py-2.5 text-left font-medium">Username</th>
              <th className="px-4 py-2.5 text-left font-medium">Role</th>
              <th className="px-4 py-2.5 text-left font-medium">Status</th>
              <th className="px-4 py-2.5" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {staff.map((s) => (
              <tr key={s.id} className={s.is_active ? "" : "opacity-50"}>
                <td className="px-4 py-2.5 font-medium text-gray-900">
                  {s.name}
                  {s.id === user?.user_id && (
                    <span className="ml-2 text-xs text-gray-500">you</span>
                  )}
                </td>
                <td className="px-4 py-2.5 text-gray-700">{s.username}</td>
                <td className="px-4 py-2.5 capitalize text-gray-700">{s.role}</td>
                <td className="px-4 py-2.5">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    s.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"
                  }`}>
                    {s.is_active ? "active" : "inactive"}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-right">
                  {s.is_active && s.id !== user?.user_id && (
                    <button
                      onClick={() => handleDeactivate(s.id, s.name)}
                      className="text-xs font-medium text-red-600 hover:underline"
                    >
                      Deactivate
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Field({ label, value, onChange, type = "text" }) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-gray-600">{label}</label>
      <input
        type={type} value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gray-900"
      />
    </div>
  );
}