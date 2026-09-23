import { useEffect, useState } from "react";
import { Search, UserPlus, RefreshCw } from "lucide-react";
import BillingPanel from "./BillingPanel";
import Layout from "../../components/layout/Layout";
import {
  searchPatients,
  registerPatient,
  bookAppointment,
  getTodayQueue,
  getTodayStats,
  updateAppointmentStatus,
  getDoctors,
} from "../../api/endpoints";

const EMPTY_FORM = {
  name: "",
  phone: "",
  gender: "male",
  date_of_birth: "",
  address: "",
};

const STATUS_STYLES = {
  waiting: "bg-amber-100 text-amber-800",
  with_doctor: "bg-blue-100 text-blue-800",
  done: "bg-green-100 text-green-800",
};

export default function ReceptionDashboard() {
  const [stats, setStats] = useState(null);
  const [queue, setQueue] = useState([]);
  const [doctors, setDoctors] = useState([]);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [selected, setSelected] = useState(null);
  const [doctorId, setDoctorId] = useState("");

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);

  const [message, setMessage] = useState(null);
  const [view, setView] = useState("queue");

  // ─── LOAD DATA ───
  const loadDashboard = async () => {
    try {
      const [q, s, d] = await Promise.all([
        getTodayQueue(),
        getTodayStats(),
        getDoctors(),
      ]);
      setQueue(q.data);
      setStats(s.data);
      setDoctors(d.data);
      if (d.data.length && !doctorId) setDoctorId(d.data[0].id);
    } catch (err) {
      showMessage("error", "Could not load dashboard");
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  // ─── SEARCH (debounced) ───
  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await searchPatients(query.trim());
        setResults(res.data);
      } catch {
        setResults([]);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3500);
  };

  const selectPatient = (patient) => {
    setSelected(patient);
    setQuery("");
    setResults([]);
    setShowForm(false);
  };

  // ─── REGISTER ───
  const handleRegister = async () => {
    if (!form.name || !form.phone) {
      showMessage("error", "Name and phone are required");
      return;
    }
    try {
      const payload = { ...form };
      if (!payload.date_of_birth) delete payload.date_of_birth;

      const res = await registerPatient(payload);
      showMessage("success", `Registered ${res.data.name} (${res.data.patient_id})`);
      setForm(EMPTY_FORM);
      selectPatient(res.data);
    } catch (err) {
      showMessage("error", err.response?.data?.detail || "Registration failed");
    }
  };

  // ─── BOOK ───
  const handleBook = async () => {
    if (!selected || !doctorId) return;
    try {
      const res = await bookAppointment({
        patient_id: selected.patient_id,
        doctor_id: Number(doctorId),
      });
      showMessage("success", `Token ${res.data.token_number} assigned to ${selected.name}`);
      setSelected(null);
      loadDashboard();
    } catch (err) {
      showMessage("error", err.response?.data?.detail || "Booking failed");
    }
  };

  // ─── STATUS ───
  const handleStatus = async (id, status) => {
    try {
      await updateAppointmentStatus(id, status);
      loadDashboard();
    } catch {
      showMessage("error", "Could not update status");
    }
  };

    return (
    <Layout>
      {/* TAB SWITCH */}
      <div className="mb-6 flex gap-2">
        <button
          onClick={() => setView("queue")}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${
            view === "queue" ? "bg-gray-900 text-white" : "border border-gray-300 bg-white text-gray-700"
          }`}
        >
          Queue
        </button>
        <button
          onClick={() => setView("billing")}
          className={`rounded-lg px-4 py-2 text-sm font-medium ${
            view === "billing" ? "bg-gray-900 text-white" : "border border-gray-300 bg-white text-gray-700"
          }`}
        >
          Billing
        </button>
      </div>

      {view === "billing" && <BillingPanel />}

      {view === "queue" && (
        <>
          {/* STATS */}
          <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label="Total today" value={stats?.total_today ?? "–"} />
            <StatCard label="Waiting" value={stats?.waiting ?? "–"} />
            <StatCard label="With doctor" value={stats?.with_doctor ?? "–"} />
            <StatCard label="Done" value={stats?.done ?? "–"} />
          </div>

          {message && (
            <div
              className={`mb-4 rounded-lg px-4 py-2 text-sm ${
                message.type === "success"
                  ? "bg-green-50 text-green-800"
                  : "bg-red-50 text-red-700"
              }`}
            >
              {message.text}
            </div>
          )}

          <div className="grid gap-6 lg:grid-cols-5">
            {/* LEFT — SEARCH / REGISTER / BOOK */}
            <section className="space-y-4 lg:col-span-2">
              <div className="rounded-xl border border-gray-200 bg-white p-5">
                <h2 className="mb-3 text-sm font-semibold text-gray-900">Find patient</h2>

                <div className="relative">
                  <Search size={16} className="absolute left-3 top-2.5 text-gray-400" />
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Name, phone or P-0001"
                    className="w-full rounded-lg border border-gray-300 py-2 pl-9 pr-3 text-sm outline-none focus:border-gray-900"
                  />

                  {results.length > 0 && (
                    <ul className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg">
                      {results.map((p) => (
                        <li
                          key={p.patient_id}
                          onClick={() => selectPatient(p)}
                          className="cursor-pointer px-3 py-2 text-sm hover:bg-gray-50"
                        >
                          <span className="font-medium text-gray-900">{p.name}</span>
                          <span className="ml-2 text-gray-500">
                            {p.patient_id} · {p.phone}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <button
                  onClick={() => {
                    setShowForm(!showForm);
                    setSelected(null);
                  }}
                  className="mt-3 flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-gray-900"
                >
                  <UserPlus size={16} />
                  {showForm ? "Cancel" : "New patient"}
                </button>
              </div>

              {/* REGISTER FORM */}
              {showForm && (
                <div className="rounded-xl border border-gray-200 bg-white p-5">
                  <h2 className="mb-3 text-sm font-semibold text-gray-900">Register patient</h2>
                  <div className="space-y-3">
                    <Input label="Name" value={form.name}
                      onChange={(v) => setForm({ ...form, name: v })} />
                    <Input label="Phone" value={form.phone}
                      onChange={(v) => setForm({ ...form, phone: v })} />
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="mb-1 block text-xs font-medium text-gray-600">Gender</label>
                        <select
                          value={form.gender}
                          onChange={(e) => setForm({ ...form, gender: e.target.value })}
                          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                        >
                          <option value="male">Male</option>
                          <option value="female">Female</option>
                          <option value="other">Other</option>
                        </select>
                      </div>
                      <Input label="Date of birth" type="date" value={form.date_of_birth}
                        onChange={(v) => setForm({ ...form, date_of_birth: v })} />
                    </div>
                    <Input label="Address" value={form.address}
                      onChange={(v) => setForm({ ...form, address: v })} />

                    <button
                      onClick={handleRegister}
                      className="w-full rounded-lg bg-gray-900 py-2 text-sm font-medium text-white hover:bg-gray-800"
                    >
                      Register
                    </button>
                  </div>
                </div>
              )}

              {/* BOOK APPOINTMENT */}
              {selected && (
                <div className="rounded-xl border border-gray-900 bg-white p-5">
                  <p className="text-xs text-gray-500">Selected patient</p>
                  <p className="text-base font-semibold text-gray-900">{selected.name}</p>
                  <p className="mb-4 text-sm text-gray-500">
                    {selected.patient_id} · {selected.phone}
                  </p>

                  <label className="mb-1 block text-xs font-medium text-gray-600">Doctor</label>
                  <select
                    value={doctorId}
                    onChange={(e) => setDoctorId(e.target.value)}
                    className="mb-3 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  >
                    {doctors.map((d) => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>

                  <button
                    onClick={handleBook}
                    className="w-full rounded-lg bg-gray-900 py-2 text-sm font-medium text-white hover:bg-gray-800"
                  >
                    Assign token
                  </button>
                </div>
              )}
            </section>

            {/* RIGHT — TODAY'S QUEUE */}
            <section className="rounded-xl border border-gray-200 bg-white lg:col-span-3">
              <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3">
                <h2 className="text-sm font-semibold text-gray-900">Today's queue</h2>
                <button onClick={loadDashboard} className="text-gray-500 hover:text-gray-900" title="Refresh">
                  <RefreshCw size={16} />
                </button>
              </div>

              {queue.length === 0 ? (
                <p className="px-5 py-10 text-center text-sm text-gray-500">No patients yet today</p>
              ) : (
                <ul className="divide-y divide-gray-100">
                  {queue.map((a) => (
                    <li key={a.id} className="flex items-center gap-4 px-5 py-3">
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gray-100 text-sm font-semibold text-gray-900">
                        {a.token_number}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-gray-900">{a.patient_name}</p>
                        <p className="text-xs text-gray-500">{a.patient_id} · {a.doctor_name}</p>
                      </div>
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[a.status] || "bg-gray-100 text-gray-700"}`}>
                        {a.status.replace("_", " ")}
                      </span>
                      {a.status === "waiting" && (
                        <button onClick={() => handleStatus(a.id, "with_doctor")}
                          className="text-xs font-medium text-blue-700 hover:underline">
                          Send in
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </>
      )}
    </Layout>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white px-5 py-4">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-gray-900">{value}</p>
    </div>
  );
}

function Input({ label, value, onChange, type = "text" }) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-gray-600">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gray-900"
      />
    </div>
  );
}
