import { useEffect, useState } from "react";
import { Plus, AlertTriangle, RefreshCw, Download } from "lucide-react";
import {
  getAllMedicines,
  addMedicine,
  restockMedicine,
  exportData,
} from "../../api/endpoints";

const EMPTY = {
  name: "",
  unit: "tablets",
  price_per_unit: "",
  stock_quantity: "",
  low_stock_alert: 20,
};

export default function InventoryPanel() {
  const [medicines, setMedicines] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [showForm, setShowForm] = useState(false);
  const [restockQty, setRestockQty] = useState({});
  const [message, setMessage] = useState(null);

  const flash = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const load = async () => {
    try {
      const res = await getAllMedicines();
      setMedicines(res.data);
    } catch {
      flash("error", "Could not load inventory");
    }
  };

  useEffect(() => { load(); }, []);

  const handleAdd = async () => {
    if (!form.name || !form.price_per_unit) {
      return flash("error", "Name and price are required");
    }
    try {
      await addMedicine({
        name: form.name.trim(),
        unit: form.unit,
        price_per_unit: Number(form.price_per_unit),
        stock_quantity: Number(form.stock_quantity) || 0,
        low_stock_alert: Number(form.low_stock_alert) || 10,
      });
      flash("success", `${form.name} added`);
      setForm(EMPTY);
      setShowForm(false);
      load();
    } catch (err) {
      flash("error", err.response?.data?.detail || "Could not add medicine");
    }
  };

  const handleRestock = async (id) => {
    const qty = Number(restockQty[id]);
    if (!qty || qty <= 0) return flash("error", "Enter a quantity");
    try {
      await restockMedicine(id, qty);
      flash("success", `Added ${qty} units`);
      setRestockQty({ ...restockQty, [id]: "" });
      load();
    } catch (err) {
      flash("error", err.response?.data?.detail || "Restock failed");
    }
  };

  const handleExport = async () => {
    try {
      const res = await exportData();
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `HMS_AI_Export_${new Date().toISOString().slice(0, 10)}.xlsx`;
      link.click();
      window.URL.revokeObjectURL(url);
      flash("success", "Export downloaded");
    } catch {
      flash("error", "Export failed");
    }
  };

  const lowStock = medicines.filter(
    (m) => m.stock_quantity <= m.low_stock_alert
  );
  const totalValue = medicines.reduce(
    (s, m) => s + m.stock_quantity * m.price_per_unit, 0
  );

  return (
    <div className="space-y-4">
      {message && (
        <div className={`rounded-lg px-4 py-2 text-sm ${
          message.type === "success" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-700"
        }`}>{message.text}</div>
      )}

      {/* STATS */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
        <Stat label="Medicines" value={medicines.length} />
        <Stat label="Low stock" value={lowStock.length} alert={lowStock.length > 0} />
        <Stat label="Inventory value" value={`Rs ${totalValue.toFixed(0)}`} />
      </div>

      {/* LOW STOCK BANNER */}
      {lowStock.length > 0 && (
        <div className="flex items-start gap-2 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm">
          <AlertTriangle size={16} className="mt-0.5 shrink-0 text-amber-700" />
          <div>
            <p className="font-medium text-amber-900">Needs restocking</p>
            <p className="text-amber-800">
              {lowStock.map((m) => `${m.name} (${m.stock_quantity})`).join(" · ")}
            </p>
          </div>
        </div>
      )}

      {/* ACTIONS */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
        >
          <Plus size={16} />
          {showForm ? "Cancel" : "Add medicine"}
        </button>
        <button
          onClick={load}
          className="flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <RefreshCw size={16} /> Refresh
        </button>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <Download size={16} /> Export all data
        </button>
      </div>

      {/* ADD FORM */}
      {showForm && (
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <h3 className="mb-3 text-sm font-semibold text-gray-900">New medicine</h3>
          <div className="grid gap-3 md:grid-cols-5">
            <Field label="Name" value={form.name}
              onChange={(v) => setForm({ ...form, name: v })} />
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Unit</label>
              <select
                value={form.unit}
                onChange={(e) => setForm({ ...form, unit: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="tablets">tablets</option>
                <option value="capsules">capsules</option>
                <option value="ml">ml</option>
                <option value="bottles">bottles</option>
                <option value="sachets">sachets</option>
              </select>
            </div>
            <Field label="Price / unit" type="number" value={form.price_per_unit}
              onChange={(v) => setForm({ ...form, price_per_unit: v })} />
            <Field label="Opening stock" type="number" value={form.stock_quantity}
              onChange={(v) => setForm({ ...form, stock_quantity: v })} />
            <Field label="Alert below" type="number" value={form.low_stock_alert}
              onChange={(v) => setForm({ ...form, low_stock_alert: v })} />
          </div>
          <button
            onClick={handleAdd}
            className="mt-4 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
          >
            Add to inventory
          </button>
        </div>
      )}

      {/* TABLE */}
      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-600">
            <tr>
              <th className="px-4 py-2.5 text-left font-medium">Medicine</th>
              <th className="px-4 py-2.5 text-left font-medium">Stock</th>
              <th className="px-4 py-2.5 text-left font-medium">Price</th>
              <th className="px-4 py-2.5 text-left font-medium">Value</th>
              <th className="px-4 py-2.5 text-left font-medium">Restock</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {medicines.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                No medicines yet
              </td></tr>
            )}
            {medicines.map((m) => {
              const low = m.stock_quantity <= m.low_stock_alert;
              return (
                <tr key={m.id} className={low ? "bg-amber-50" : ""}>
                  <td className="px-4 py-2.5 font-medium text-gray-900">{m.name}</td>
                  <td className="px-4 py-2.5">
                    <span className={low ? "font-medium text-amber-800" : "text-gray-700"}>
                      {m.stock_quantity} {m.unit}
                    </span>
                    {low && <span className="ml-2 text-xs text-amber-700">low</span>}
                  </td>
                  <td className="px-4 py-2.5 text-gray-700">Rs {m.price_per_unit}</td>
                  <td className="px-4 py-2.5 text-gray-700">
                    Rs {(m.stock_quantity * m.price_per_unit).toFixed(0)}
                  </td>
                  <td className="px-4 py-2.5">
                    <div className="flex gap-1">
                      <input
                        type="number" min={1} placeholder="qty"
                        value={restockQty[m.id] || ""}
                        onChange={(e) =>
                          setRestockQty({ ...restockQty, [m.id]: e.target.value })
                        }
                        className="w-20 rounded border border-gray-300 px-2 py-1 text-sm"
                      />
                      <button
                        onClick={() => handleRestock(m.id)}
                        className="rounded bg-gray-900 px-3 py-1 text-xs font-medium text-white hover:bg-gray-800"
                      >
                        Add
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Stat({ label, value, alert }) {
  return (
    <div className={`rounded-xl border px-5 py-4 ${
      alert ? "border-amber-300 bg-amber-50" : "border-gray-200 bg-white"
    }`}>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-gray-900">{value}</p>
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