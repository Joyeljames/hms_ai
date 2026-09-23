import { useEffect, useState } from "react";
import { RefreshCw, Receipt } from "lucide-react";
import {
  getReadyForBilling,
  createBill,
  collectPayment,
  getPendingBills,
  getTodayRevenue,
} from "../../api/endpoints";

const METHODS = ["cash", "upi", "card"];

export default function BillingPanel() {
  const [ready, setReady] = useState([]);
  const [bills, setBills] = useState([]);
  const [revenue, setRevenue] = useState(null);

  const [selected, setSelected] = useState(null);
  const [discount, setDiscount] = useState(0);
  const [method, setMethod] = useState("cash");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);

  const flash = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const load = async () => {
    try {
      const [r, b, rev] = await Promise.all([
        getReadyForBilling(),
        getPendingBills(),
        getTodayRevenue(),
      ]);
      setReady(r.data);
      setBills(b.data);
      setRevenue(rev.data);
    } catch {
      flash("error", "Could not load billing data");
    }
  };

  useEffect(() => { load(); }, []);

  // create bill from a dispensed prescription
  const handleCreate = async () => {
    setBusy(true);
    try {
      const res = await createBill({
        patient_id: selected.patient_id,
        prescription_id: selected.prescription_id,
        is_new_patient: selected.is_new_patient,
        discount: Number(discount) || 0,
      });
      flash("success", `Bill #${res.data.id} created — Rs ${res.data.total_amount}`);
      setSelected(null);
      setDiscount(0);
      load();
    } catch (err) {
      flash("error", err.response?.data?.detail || "Could not create bill");
    } finally {
      setBusy(false);
    }
  };

  const handlePay = async (billId) => {
    try {
      await collectPayment(billId, method);
      flash("success", "Payment collected");
      load();
    } catch (err) {
      flash("error", err.response?.data?.detail || "Payment failed");
    }
  };

  return (
    <div className="space-y-6">
      {message && (
        <div className={`rounded-lg px-4 py-2 text-sm ${
          message.type === "success" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-700"
        }`}>{message.text}</div>
      )}

      {/* REVENUE */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
        <Stat label="Today's revenue" value={`Rs ${revenue?.total_revenue ?? 0}`} />
        <Stat label="Bills paid" value={revenue?.total_patients_billed ?? 0} />
        <Stat label="Unpaid bills" value={bills.length} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* READY FOR BILLING */}
        <section className="rounded-xl border border-gray-200 bg-white">
          <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3">
            <h2 className="text-sm font-semibold text-gray-900">Ready to bill ({ready.length})</h2>
            <button onClick={load} className="text-gray-500 hover:text-gray-900"><RefreshCw size={16} /></button>
          </div>

          {ready.length === 0 ? (
            <p className="px-5 py-8 text-center text-sm text-gray-500">Nothing waiting</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {ready.map((r) => (
                <li key={r.prescription_id}
                    onClick={() => { setSelected(r); setDiscount(0); }}
                    className={`cursor-pointer px-5 py-3 hover:bg-gray-50 ${
                      selected?.prescription_id === r.prescription_id ? "bg-gray-50" : ""
                    }`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{r.patient_name}</p>
                      <p className="text-xs text-gray-500">
                        {r.patient_id}
                        {r.is_new_patient && <span className="ml-2 text-amber-700">new patient</span>}
                      </p>
                    </div>
                    <span className="text-sm text-gray-900">Rs {r.medicine_total}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}

          {/* CREATE BILL */}
          {selected && (
            <div className="border-t border-gray-200 p-5">
              <p className="mb-3 text-sm font-medium text-gray-900">
                Bill for {selected.patient_name}
              </p>
              <label className="mb-1 block text-xs font-medium text-gray-600">Discount (Rs)</label>
              <input
                type="number" min={0} value={discount}
                onChange={(e) => setDiscount(e.target.value)}
                className="mb-3 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
              <p className="mb-3 text-xs text-gray-500">
                Consultation and registration fees are added automatically by the server.
              </p>
              <button
                onClick={handleCreate}
                disabled={busy}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-gray-900 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
              >
                <Receipt size={16} />
                {busy ? "Creating…" : "Generate bill"}
              </button>
            </div>
          )}
        </section>

        {/* UNPAID BILLS */}
        <section className="rounded-xl border border-gray-200 bg-white">
          <div className="border-b border-gray-200 px-5 py-3">
            <h2 className="text-sm font-semibold text-gray-900">Collect payment ({bills.length})</h2>
          </div>

          {bills.length === 0 ? (
            <p className="px-5 py-8 text-center text-sm text-gray-500">No unpaid bills</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {bills.map((b) => (
                <li key={b.bill_id} className="px-5 py-4">
                  <div className="mb-2 flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-900">{b.patient_name}</p>
                      <p className="text-xs text-gray-500">Bill #{b.bill_id} · {b.patient_id}</p>
                    </div>
                    <p className="text-lg font-semibold text-gray-900">Rs {b.total_amount}</p>
                  </div>

                  <div className="mb-2 space-y-0.5 text-xs text-gray-500">
                    {b.registration_fee > 0 && <p>Registration: Rs {b.registration_fee}</p>}
                    <p>Consultation: Rs {b.consultation_fee}</p>
                    <p>Medicines: Rs {b.medicine_total}</p>
                    {b.discount > 0 && <p className="text-green-700">Discount: −Rs {b.discount}</p>}
                  </div>

                  <div className="flex gap-2">
                    <select
                      value={method}
                      onChange={(e) => setMethod(e.target.value)}
                      className="rounded-lg border border-gray-300 px-2 py-1.5 text-sm"
                    >
                      {METHODS.map((m) => (
                        <option key={m} value={m}>{m.toUpperCase()}</option>
                      ))}
                    </select>
                    <button
                      onClick={() => handlePay(b.bill_id)}
                      className="flex-1 rounded-lg bg-green-600 py-1.5 text-sm font-medium text-white hover:bg-green-700"
                    >
                      Mark paid
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white px-5 py-4">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-gray-900">{value}</p>
    </div>
  );
}