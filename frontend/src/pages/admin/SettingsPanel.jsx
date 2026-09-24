import { useState } from "react";
import { setClinicFees } from "../../api/endpoints";

export default function SettingsPanel() {
  const [fees, setFees] = useState({
    registration_fee: "",
    consultation_fee: "",
    follow_up_fee: "",
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  const flash = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await setClinicFees({
        registration_fee: Number(fees.registration_fee) || 0,
        consultation_fee: Number(fees.consultation_fee) || 0,
        follow_up_fee: Number(fees.follow_up_fee) || 0,
      });
      flash("success", "Fees updated");
      setFees({
        registration_fee: res.data.registration_fee,
        consultation_fee: res.data.consultation_fee,
        follow_up_fee: res.data.follow_up_fee,
      });
    } catch (err) {
      flash("error", err.response?.data?.detail || "Could not save fees");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-xl space-y-4">
      {message && (
        <div className={`rounded-lg px-4 py-2 text-sm ${
          message.type === "success" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-700"
        }`}>{message.text}</div>
      )}

      <div className="rounded-xl border border-gray-200 bg-white p-5">
        <h3 className="mb-1 text-sm font-semibold text-gray-900">Clinic fees</h3>
        <p className="mb-4 text-xs text-gray-500">
          These are applied automatically when a bill is generated.
        </p>

        <div className="space-y-3">
          <Field label="Registration fee (new patients only)"
            value={fees.registration_fee}
            onChange={(v) => setFees({ ...fees, registration_fee: v })} />
          <Field label="Consultation fee"
            value={fees.consultation_fee}
            onChange={(v) => setFees({ ...fees, consultation_fee: v })} />
          <Field label="Follow-up fee"
            value={fees.follow_up_fee}
            onChange={(v) => setFees({ ...fees, follow_up_fee: v })} />
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="mt-4 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save fees"}
        </button>
      </div>
    </div>
  );
}

function Field({ label, value, onChange }) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-gray-600">{label}</label>
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-500">Rs</span>
        <input
          type="number" min={0} value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gray-900"
        />
      </div>
    </div>
  );
}