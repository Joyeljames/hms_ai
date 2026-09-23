import { useEffect, useState } from "react";
import { Sparkles, AlertTriangle, Check, RefreshCw, Package } from "lucide-react";
import Layout from "../../components/layout/Layout";
import {
  getPharmacyPending,
  viewPrescription,
  dispensePrescription,
  aiProcessPharmacy,
  getAllMedicines,
} from "../../api/endpoints";

export default function PharmacyDashboard() {
  const [pending, setPending] = useState([]);
  const [inventory, setInventory] = useState([]);

  const [active, setActive] = useState(null);   // prescription detail
  const [items, setItems] = useState([]);       // editable rows
  const [extras, setExtras] = useState([]);     // pharmacist additions
  const [ai, setAi] = useState(null);           // agent result

  const [checking, setChecking] = useState(false);
  const [dispensing, setDispensing] = useState(false);
  const [message, setMessage] = useState(null);

  const flash = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const loadPending = async () => {
    try {
      const res = await getPharmacyPending();
      setPending(res.data);
    } catch {
      flash("error", "Could not load pending prescriptions");
    }
  };

  useEffect(() => {
    loadPending();
    getAllMedicines().then((r) => setInventory(r.data)).catch(() => {});
  }, []);

  // ─── OPEN PRESCRIPTION ───
  const open = async (p) => {
    setActive(null);
    setAi(null);
    setExtras([]);
    try {
      const res = await viewPrescription(p.prescription_id);
      setActive(res.data);
      setItems(
        res.data.items.map((i) => ({
          prescription_item_id: i.prescription_item_id,
          medicine_id: i.medicine_id,
          medicine_name: i.medicine_name,
          prescribed: i.quantity,
          quantity: i.quantity,          // editable
          price: i.price_per_unit ?? 0,
          available: i.available_stock ?? 0,
          in_stock: i.in_stock,
        }))
      );
    } catch {
      flash("error", "Could not open prescription");
    }
  };

  // ─── AI STOCK CHECK ───
  const runAI = async () => {
    setChecking(true);
    try {
      const res = await aiProcessPharmacy(active.prescription_id);
      setAi(res.data);
    } catch (err) {
      flash("error", err.response?.data?.detail || "AI check failed");
    } finally {
      setChecking(false);
    }
  };

  // ─── EDIT ───
  const setQty = (i, value) => {
    const next = [...items];
    next[i] = { ...next[i], quantity: Number(value) };
    setItems(next);
  };

  const addExtra = (name) => {
    const med = inventory.find((m) => m.name === name);
    if (!med || extras.some((e) => e.medicine_id === med.id)) return;
    setExtras([...extras, {
      medicine_id: med.id,
      medicine_name: med.name,
      quantity: 1,
      price: med.price_per_unit,
      available: med.stock_quantity,
    }]);
  };

  const setExtraQty = (i, value) => {
    const next = [...extras];
    next[i] = { ...next[i], quantity: Number(value) };
    setExtras(next);
  };

  const removeExtra = (i) => setExtras(extras.filter((_, idx) => idx !== i));

  // ─── TOTAL (Python-style exact math, computed here for preview only) ───
  const total =
    items.reduce((s, i) => s + i.quantity * i.price, 0) +
    extras.reduce((s, e) => s + e.quantity * e.price, 0);

  const hasShortage =
    items.some((i) => i.quantity > i.available) ||
    extras.some((e) => e.quantity > e.available);

  // ─── DISPENSE ───
  const handleDispense = async () => {
    if (hasShortage) return flash("error", "Some quantities exceed available stock");

    setDispensing(true);
    try {
      const res = await dispensePrescription(active.prescription_id, {
        items: items
          .filter((i) => i.quantity > 0)
          .map((i) => ({
            prescription_item_id: i.prescription_item_id,
            quantity: i.quantity,
          })),
        extra_items: extras.map((e) => ({
          medicine_id: e.medicine_id,
          quantity: e.quantity,
          timing: "after food",
        })),
      });

      flash("success", `Dispensed — medicine total Rs ${res.data.medicine_total}`);
      setActive(null);
      setAi(null);
      setExtras([]);
      loadPending();
      getAllMedicines().then((r) => setInventory(r.data));
    } catch (err) {
      flash("error", err.response?.data?.detail || "Dispense failed");
    } finally {
      setDispensing(false);
    }
  };

  const availableToAdd = inventory.filter(
    (m) => m.stock_quantity > 0 && !extras.some((e) => e.medicine_id === m.id)
  );

  return (
    <Layout>
      {message && (
        <div className={`mb-4 rounded-lg px-4 py-2 text-sm ${
          message.type === "success" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-700"
        }`}>{message.text}</div>
      )}

      <div className="grid gap-6 lg:grid-cols-4">
        {/* PENDING LIST */}
        <aside className="rounded-xl border border-gray-200 bg-white lg:col-span-1">
          <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
            <h2 className="text-sm font-semibold text-gray-900">
              Pending ({pending.length})
            </h2>
            <button onClick={loadPending} className="text-gray-500 hover:text-gray-900">
              <RefreshCw size={16} />
            </button>
          </div>

          {pending.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-gray-500">Nothing to dispense</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {pending.map((p) => (
                <li
                  key={p.prescription_id}
                  onClick={() => open(p)}
                  className={`cursor-pointer px-4 py-3 hover:bg-gray-50 ${
                    active?.prescription_id === p.prescription_id ? "bg-gray-50" : ""
                  }`}
                >
                  <p className="text-sm font-medium text-gray-900">{p.patient_name}</p>
                  <p className="text-xs text-gray-500">{p.patient_id} · Rx #{p.prescription_id}</p>
                </li>
              ))}
            </ul>
          )}
        </aside>

        {/* DETAIL */}
        <section className="space-y-4 lg:col-span-3">
          {!active ? (
            <div className="rounded-xl border border-dashed border-gray-300 bg-white py-20 text-center text-sm text-gray-500">
              Select a prescription to dispense
            </div>
          ) : (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-gray-200 bg-white p-5">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">{active.patient_name}</h2>
                  <p className="text-sm text-gray-500">
                    {active.patient_id} · Prescription #{active.prescription_id}
                  </p>
                </div>
                <button
                  onClick={runAI}
                  disabled={checking}
                  className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  <Sparkles size={16} />
                  {checking ? "Checking…" : "AI stock check"}
                </button>
              </div>

              {/* AI RESULT */}
              {ai && (
                <div className="rounded-xl border border-amber-300 bg-amber-50 p-5">
                  <h3 className="mb-2 text-sm font-semibold text-gray-900">AI stock report</h3>

                  {ai.out_of_stock?.length > 0 ? (
                    <div className="mb-3 flex items-start gap-2 text-sm text-red-800">
                      <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                      <div>
                        {ai.out_of_stock.map((o) => (
                          <p key={o.medicine_name}>
                            {o.medicine_name} — need {o.required}, have {o.available}
                          </p>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="mb-3 text-sm text-green-800">All medicines in stock</p>
                  )}

                  {ai.ai_alternatives?.length > 0 && (
                    <div className="text-sm text-gray-800">
                      <p className="font-medium">Suggested alternatives</p>
                      {ai.ai_alternatives.map((a, i) => (
                        <p key={i} className="text-xs">
                          {a.original} → <span className="font-medium">{a.suggested}</span> — {a.reason}
                        </p>
                      ))}
                      <p className="mt-2 text-xs text-gray-500">
                        Suggestions only. Add manually below if you agree.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* ITEMS TABLE */}
              <div className="rounded-xl border border-gray-200 bg-white p-5">
                <h3 className="mb-3 text-sm font-semibold text-gray-900">Prescribed medicines</h3>

                <div className="overflow-x-auto rounded-lg border border-gray-200">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-xs text-gray-600">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium">Medicine</th>
                        <th className="px-3 py-2 text-left font-medium">Prescribed</th>
                        <th className="px-3 py-2 text-left font-medium">Dispense</th>
                        <th className="px-3 py-2 text-left font-medium">Stock</th>
                        <th className="px-3 py-2 text-right font-medium">Amount</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {items.map((i, idx) => {
                        const short = i.quantity > i.available;
                        return (
                          <tr key={i.prescription_item_id} className={short ? "bg-red-50" : ""}>
                            <td className="px-3 py-2 font-medium text-gray-900">{i.medicine_name}</td>
                            <td className="px-3 py-2 text-gray-500">{i.prescribed}</td>
                            <td className="px-3 py-2">
                              <input
                                type="number" min={0} value={i.quantity}
                                onChange={(e) => setQty(idx, e.target.value)}
                                className={`w-20 rounded border px-2 py-1 ${
                                  short ? "border-red-400" : "border-gray-300"
                                }`}
                              />
                            </td>
                            <td className={`px-3 py-2 ${short ? "font-medium text-red-700" : "text-gray-500"}`}>
                              {i.available}
                            </td>
                            <td className="px-3 py-2 text-right text-gray-900">
                              Rs {(i.quantity * i.price).toFixed(2)}
                            </td>
                          </tr>
                        );
                      })}

                      {extras.map((e, idx) => (
                        <tr key={`x-${e.medicine_id}`} className="bg-blue-50">
                          <td className="px-3 py-2 font-medium text-gray-900">
                            {e.medicine_name}
                            <span className="ml-2 text-xs text-blue-700">added</span>
                          </td>
                          <td className="px-3 py-2 text-gray-400">—</td>
                          <td className="px-3 py-2">
                            <input
                              type="number" min={1} value={e.quantity}
                              onChange={(ev) => setExtraQty(idx, ev.target.value)}
                              className="w-20 rounded border border-gray-300 px-2 py-1"
                            />
                          </td>
                          <td className="px-3 py-2 text-gray-500">{e.available}</td>
                          <td className="px-3 py-2 text-right">
                            <span className="text-gray-900">Rs {(e.quantity * e.price).toFixed(2)}</span>
                            <button onClick={() => removeExtra(idx)} className="ml-3 text-xs text-red-600 hover:underline">
                              remove
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* ADD EXTRA */}
                <div className="mt-3 flex items-center gap-2">
                  <Package size={16} className="text-gray-500" />
                  <select
                    value=""
                    onChange={(e) => addExtra(e.target.value)}
                    className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm"
                  >
                    <option value="">Add extra medicine…</option>
                    {availableToAdd.map((m) => (
                      <option key={m.id} value={m.name}>
                        {m.name} ({m.stock_quantity} in stock)
                      </option>
                    ))}
                  </select>
                </div>

                {/* TOTAL + DISPENSE */}
                <div className="mt-5 flex flex-wrap items-center justify-between gap-4 border-t border-gray-200 pt-4">
                  <div>
                    <p className="text-xs text-gray-500">Medicine total</p>
                    <p className="text-2xl font-semibold text-gray-900">Rs {total.toFixed(2)}</p>
                  </div>
                  <button
                    onClick={handleDispense}
                    disabled={dispensing || hasShortage}
                    className="flex items-center gap-2 rounded-lg bg-gray-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
                  >
                    <Check size={16} />
                    {dispensing ? "Dispensing…" : "Confirm & dispense"}
                  </button>
                </div>

                {hasShortage && (
                  <p className="mt-2 text-xs text-red-700">
                    Reduce quantities to available stock before dispensing.
                  </p>
                )}
              </div>
            </>
          )}
        </section>
      </div>
    </Layout>
  );
}