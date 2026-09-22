import { useEffect, useState } from "react";
import { Sparkles, Trash2, Plus, Check, X, RefreshCw, FileText } from "lucide-react";
import Layout from "../../components/layout/Layout";
import {
  getTodayQueue,
  updateAppointmentStatus,
  searchPatients,
  getLast2Visits,
  getAllMedicines,
  createVisit,
  aiGeneratePrescription,
  aiApprovePrescription,
} from "../../api/endpoints";

const TIMINGS = ["after food", "before food", "with food", "at bedtime"];

const STATUS_STYLES = {
  waiting: "bg-amber-100 text-amber-800",
  with_doctor: "bg-blue-100 text-blue-800",
  done: "bg-green-100 text-green-800",
};

export default function DoctorDashboard() {
  const [queue, setQueue] = useState([]);
  const [inventory, setInventory] = useState([]);

  const [active, setActive] = useState(null);     // selected appointment
  const [patient, setPatient] = useState(null);   // patient details
  const [visits, setVisits] = useState([]);

  const [symptoms, setSymptoms] = useState("");
  const [generating, setGenerating] = useState(false);
  const [draft, setDraft] = useState(null);       // prescription being edited
  const [notes, setNotes] = useState("");
  const [followUp, setFollowUp] = useState("");

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(null);
  const [message, setMessage] = useState(null);

  // ─── LOAD ───
  const loadQueue = async () => {
    try {
      const res = await getTodayQueue();
      setQueue(res.data);
    } catch {
      flash("error", "Could not load queue");
    }
  };

  useEffect(() => {
    loadQueue();
    getAllMedicines()
      .then((res) => setInventory(res.data))
      .catch(() => flash("error", "Could not load medicines"));
  }, []);

  const flash = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  // ─── OPEN PATIENT ───
  const openPatient = async (appt) => {
    setActive(appt);
    setPatient(null);
    setVisits([]);
    setSymptoms("");
    setDraft(null);
    setNotes("");
    setFollowUp("");
    setSaved(null);

    if (appt.status === "waiting") {
      await updateAppointmentStatus(appt.id, "with_doctor");
      loadQueue();
    }

    try {
      const [p, v] = await Promise.all([
        searchPatients(appt.patient_id),
        getLast2Visits(appt.patient_id),
      ]);
      setPatient(p.data.find((x) => x.patient_id === appt.patient_id) || null);
      setVisits(v.data);
    } catch {
      flash("error", "Could not load patient details");
    }
  };

  // ─── AI GENERATE ───
  const handleGenerate = async () => {
    if (!symptoms.trim()) {
      flash("error", "Type the symptoms first");
      return;
    }
    setGenerating(true);
    setDraft(null);

    try {
      const res = await aiGeneratePrescription({
        patient_id: active.patient_id,
        symptoms: symptoms.trim(),
      });
      const data = res.data;

      // Map AI names to EXACT inventory names (case-safe)
      const byName = Object.fromEntries(
        inventory.map((m) => [m.name.toLowerCase(), m.name])
      );

      const medicines = (data.ai_medicines || []).map((m) => ({
        name: byName[m.name?.toLowerCase()] || m.name,
        frequency: Number(m.frequency) || 1,
        duration: Number(m.duration) || 1,
        timing: m.timing || "after food",
      }));

      setDraft({
        source: "ai",
        diagnosis: data.ai_diagnosis || "",
        medicines,
        interactions: data.interactions,
        rejected: data.rejected_hallucinations || [],
      });
    } catch (err) {
      flash("error", err.response?.data?.detail || "AI generation failed — write manually");
    } finally {
      setGenerating(false);
    }
  };

  const startManual = () => {
    setDraft({ source: "manual", diagnosis: "", medicines: [], interactions: null, rejected: [] });
  };

  const handleReject = () => {
    setDraft(null);
    flash("success", "AI suggestion rejected");
  };

  // ─── EDIT DRAFT ───
  const updateMed = (i, field, value) => {
    const medicines = [...draft.medicines];
    medicines[i] = { ...medicines[i], [field]: value };
    setDraft({ ...draft, medicines });
  };

  const removeMed = (i) => {
    setDraft({ ...draft, medicines: draft.medicines.filter((_, idx) => idx !== i) });
  };

  const addMed = (name) => {
    if (!name || draft.medicines.some((m) => m.name === name)) return;
    setDraft({
      ...draft,
      medicines: [...draft.medicines, { name, frequency: 1, duration: 5, timing: "after food" }],
    });
  };

  // ─── APPROVE ───
  const handleApprove = async () => {
    if (!symptoms.trim()) return flash("error", "Symptoms are required");
    if (!draft.diagnosis.trim()) return flash("error", "Diagnosis is required");
    if (draft.medicines.length === 0) return flash("error", "Add at least one medicine");

    setSaving(true);
    try {
      // 1. Save the visit note
      const visit = await createVisit({
        patient_id: active.patient_id,
        appointment_id: active.id,
        complaint: symptoms.trim(),
        diagnosis: draft.diagnosis.trim(),
        notes: notes || null,
        follow_up_date: followUp || null,
      });

      // 2. Create prescription → goes to pharmacy
      const rx = await aiApprovePrescription({
        patient_id: active.patient_id,
        visit_id: visit.data.id,
        diagnosis: draft.diagnosis.trim(),
        medicines: draft.medicines.map((m) => ({
          name: m.name,
          frequency: Number(m.frequency),
          duration: Number(m.duration),
          timing: m.timing,
        })),
      });

      setSaved(rx.data);
      setDraft(null);
      flash("success", "Prescription sent to pharmacy");
    } catch (err) {
      flash("error", err.response?.data?.detail || "Could not save prescription");
    } finally {
      setSaving(false);
    }
  };

  // ─── FINISH ───
  const handleFinish = async () => {
    await updateAppointmentStatus(active.id, "done");
    setActive(null);
    setSaved(null);
    loadQueue();
  };

  const pending = queue.filter((a) => a.status !== "done");
  const doneCount = queue.length - pending.length;

  return (
    <Layout>
      {message && (
        <div className={`mb-4 rounded-lg px-4 py-2 text-sm ${
          message.type === "success" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-700"
        }`}>
          {message.text}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-4">
        {/* ─── QUEUE ─── */}
        <aside className="rounded-xl border border-gray-200 bg-white lg:col-span-1">
          <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
            <div>
              <h2 className="text-sm font-semibold text-gray-900">Today's queue</h2>
              <p className="text-xs text-gray-500">{doneCount} done · {pending.length} pending</p>
            </div>
            <button onClick={loadQueue} className="text-gray-500 hover:text-gray-900">
              <RefreshCw size={16} />
            </button>
          </div>

          {pending.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-gray-500">No patients waiting</p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {pending.map((a) => (
                <li
                  key={a.id}
                  onClick={() => openPatient(a)}
                  className={`flex cursor-pointer items-center gap-3 px-4 py-3 hover:bg-gray-50 ${
                    active?.id === a.id ? "bg-gray-50" : ""
                  }`}
                >
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-100 text-xs font-semibold">
                    {a.token_number}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-gray-900">{a.patient_name}</p>
                    <span className={`rounded-full px-2 py-0.5 text-xs ${STATUS_STYLES[a.status]}`}>
                      {a.status.replace("_", " ")}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </aside>

        {/* ─── MAIN ─── */}
        <section className="space-y-4 lg:col-span-3">
          {!active ? (
            <div className="rounded-xl border border-dashed border-gray-300 bg-white py-20 text-center text-sm text-gray-500">
              Select a patient from the queue
            </div>
          ) : (
            <>
              {/* PATIENT CARD */}
              <div className="rounded-xl border border-gray-200 bg-white p-5">
                <div className="flex flex-wrap items-baseline gap-x-6 gap-y-1">
                  <h2 className="text-lg font-semibold text-gray-900">{active.patient_name}</h2>
                  <span className="text-sm text-gray-500">{active.patient_id}</span>
                  {patient && (
                    <>
                      <span className="text-sm text-gray-500 capitalize">{patient.gender}</span>
                      {patient.age != null && <span className="text-sm text-gray-500">{patient.age} yrs</span>}
                      <span className="text-sm text-gray-500">{patient.phone}</span>
                    </>
                  )}
                </div>
              </div>

              {/* LAST 2 VISITS */}
              <div className="rounded-xl border border-gray-200 bg-white p-5">
                <h3 className="mb-3 text-sm font-semibold text-gray-900">Recent visits</h3>
                {visits.length === 0 ? (
                  <p className="text-sm text-gray-500">First visit — no history</p>
                ) : (
                  <div className="grid gap-3 md:grid-cols-2">
                    {visits.map((v) => (
                      <div key={v.id} className="rounded-lg bg-gray-50 p-3 text-sm">
                        <p className="text-xs text-gray-500">{v.created_at?.slice(0, 10)}</p>
                        <p className="mt-1 text-gray-900"><span className="text-gray-500">Complaint:</span> {v.complaint}</p>
                        <p className="text-gray-900"><span className="text-gray-500">Diagnosis:</span> {v.diagnosis || "—"}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* SAVED STATE */}
              {saved ? (
                <div className="rounded-xl border border-green-200 bg-green-50 p-5">
                  <p className="text-sm font-semibold text-green-900">
                    Prescription #{saved.prescription_id} sent to pharmacy
                  </p>
                  <ul className="mt-2 space-y-1 text-sm text-green-900">
                    {saved.items.map((i) => (
                      <li key={i.medicine_name}>
                        {i.medicine_name} — {i.frequency}×/day × {i.duration} days = {i.quantity}
                      </li>
                    ))}
                  </ul>
                  {saved.skipped_medicines?.length > 0 && (
                    <p className="mt-2 text-xs text-amber-800">
                      Skipped (not in inventory): {saved.skipped_medicines.join(", ")}
                    </p>
                  )}
                  <button
                    onClick={handleFinish}
                    className="mt-4 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
                  >
                    Finish consultation
                  </button>
                </div>
              ) : (
                <>
                  {/* SYMPTOMS + GENERATE */}
                  <div className="rounded-xl border border-blue-200 bg-white p-5">
                    <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-900">
                      <Sparkles size={16} className="text-blue-600" />
                      AI prescription assistant
                    </h3>
                    <textarea
                      value={symptoms}
                      onChange={(e) => setSymptoms(e.target.value)}
                      rows={3}
                      placeholder="e.g. Fever 38.5°C, runny nose, headache for 2 days"
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gray-900"
                    />
                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        onClick={handleGenerate}
                        disabled={generating}
                        className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                      >
                        <Sparkles size={16} />
                        {generating ? "Generating…" : "Generate prescription"}
                      </button>
                      {!draft && (
                        <button
                          onClick={startManual}
                          className="flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                        >
                          <FileText size={16} />
                          Write manually
                        </button>
                      )}
                    </div>
                  </div>

                  {/* EDITOR */}
                  {draft && (
                    <PrescriptionEditor
                      draft={draft}
                      setDraft={setDraft}
                      inventory={inventory}
                      notes={notes}
                      setNotes={setNotes}
                      followUp={followUp}
                      setFollowUp={setFollowUp}
                      updateMed={updateMed}
                      removeMed={removeMed}
                      addMed={addMed}
                      onApprove={handleApprove}
                      onReject={handleReject}
                      saving={saving}
                    />
                  )}
                </>
              )}
            </>
          )}
        </section>
      </div>
    </Layout>
  );
}

// ═════════════════════════════════════════
// EDITOR — same component for AI and manual
// ═════════════════════════════════════════
function PrescriptionEditor({
  draft, setDraft, inventory, notes, setNotes, followUp, setFollowUp,
  updateMed, removeMed, addMed, onApprove, onReject, saving,
}) {
  const isAI = draft.source === "ai";
  const available = inventory.filter((m) => !draft.medicines.some((d) => d.name === m.name));

  return (
    <div className={`rounded-xl border p-5 ${isAI ? "border-amber-300 bg-amber-50" : "border-gray-200 bg-white"}`}>
      <h3 className="mb-4 text-sm font-semibold text-gray-900">
        {isAI ? "AI suggestion — review before approving" : "Manual prescription"}
      </h3>

      {/* DIAGNOSIS */}
      <label className="mb-1 block text-xs font-medium text-gray-600">Diagnosis</label>
      <input
        value={draft.diagnosis}
        onChange={(e) => setDraft({ ...draft, diagnosis: e.target.value })}
        className="mb-4 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-gray-900"
      />

      {/* MEDICINES */}
      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-600">
            <tr>
              <th className="px-3 py-2 text-left font-medium">Medicine</th>
              <th className="px-3 py-2 text-left font-medium">Per day</th>
              <th className="px-3 py-2 text-left font-medium">Days</th>
              <th className="px-3 py-2 text-left font-medium">Qty</th>
              <th className="px-3 py-2 text-left font-medium">Timing</th>
              <th />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {draft.medicines.length === 0 && (
              <tr><td colSpan={6} className="px-3 py-4 text-center text-gray-500">No medicines added</td></tr>
            )}
            {draft.medicines.map((m, i) => (
              <tr key={m.name}>
                <td className="px-3 py-2 font-medium text-gray-900">{m.name}</td>
                <td className="px-3 py-2">
                  <input type="number" min={1} max={6} value={m.frequency}
                    onChange={(e) => updateMed(i, "frequency", e.target.value)}
                    className="w-16 rounded border border-gray-300 px-2 py-1" />
                </td>
                <td className="px-3 py-2">
                  <input type="number" min={1} max={90} value={m.duration}
                    onChange={(e) => updateMed(i, "duration", e.target.value)}
                    className="w-16 rounded border border-gray-300 px-2 py-1" />
                </td>
                <td className="px-3 py-2 font-medium text-gray-900">
                  {(Number(m.frequency) || 0) * (Number(m.duration) || 0)}
                </td>
                <td className="px-3 py-2">
                  <select value={m.timing} onChange={(e) => updateMed(i, "timing", e.target.value)}
                    className="rounded border border-gray-300 px-2 py-1">
                    {TIMINGS.map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </td>
                <td className="px-3 py-2 text-right">
                  <button onClick={() => removeMed(i)} className="text-gray-400 hover:text-red-600">
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* ADD MEDICINE */}
      <div className="mt-3 flex items-center gap-2">
        <Plus size={16} className="text-gray-500" />
        <select
          value=""
          onChange={(e) => addMed(e.target.value)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm"
        >
          <option value="">Add medicine from inventory…</option>
          {available.map((m) => (
            <option key={m.id} value={m.name} disabled={m.stock_quantity <= 0}>
              {m.name} ({m.stock_quantity} in stock)
            </option>
          ))}
        </select>
      </div>

      {/* AI SAFETY INFO */}
      {isAI && (
        <div className="mt-4 space-y-1 text-xs">
          {draft.interactions && (
            <p className="text-gray-700"><span className="font-medium">Interactions:</span> {draft.interactions}</p>
          )}
          {draft.rejected.length > 0 && (
            <p className="text-red-700">
              <span className="font-medium">Blocked (not in inventory):</span> {draft.rejected.join(", ")}
            </p>
          )}
        </div>
      )}

      {/* NOTES + FOLLOW UP */}
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div className="md:col-span-2">
          <label className="mb-1 block text-xs font-medium text-gray-600">Doctor's notes</label>
          <input value={notes} onChange={(e) => setNotes(e.target.value)}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">Follow-up date</label>
          <input type="date" value={followUp} onChange={(e) => setFollowUp(e.target.value)}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm" />
        </div>
      </div>

      {/* ACTIONS */}
      <div className="mt-5 flex flex-wrap gap-2">
        <button
          onClick={onApprove}
          disabled={saving}
          className="flex items-center gap-2 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
        >
          <Check size={16} />
          {saving ? "Saving…" : isAI ? "Approve & send to pharmacy" : "Save & send to pharmacy"}
        </button>
        <button
          onClick={onReject}
          className="flex items-center gap-2 rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50"
        >
          <X size={16} />
          {isAI ? "Reject" : "Cancel"}
        </button>
      </div>
    </div>
  );
}