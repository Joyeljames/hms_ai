import client from "./client";

// ─── AUTH ───
export const login = (username, password) => {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  return client.post("/auth/login", formData, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
};

// ─── PATIENTS ───
export const registerPatient = (data) => client.post("/patients/register_patients", data);
export const searchPatients = (query) =>
  client.get(`/patients/search_patients?query=${encodeURIComponent(query)}`);
export const getAllPatients = () => client.get("/patients/all");

// ─── APPOINTMENTS ───
export const bookAppointment = (data) => client.post("/appointments/book", data);
export const getTodayQueue = () => client.get("/appointments/today");
export const updateAppointmentStatus = (id, status) =>
  client.put(`/appointments/${id}/status`, { status });
export const getTodayStats = () => client.get("/appointments/stats/today");
export const getDoctors = () => client.get("/appointments/doctors");

// ─── VISITS ───
export const createVisit = (data) => client.post("/visits/create_visit", data);
export const getPatientVisits = (patientId) => client.get(`/visits/patient/${patientId}`);
export const getLast2Visits = (patientId) => client.get(`/visits/patient/${patientId}/last2`);


// ─── MEDICINES ───
export const getAllMedicines = () => client.get("/medicines/all");
export const searchMedicines = (query) => client.get(`/medicines/search?query=${query}`);
export const addMedicine = (data) => client.post("/medicines/add_medicine", data);
export const restockMedicine = (id, quantity) =>
  client.put(`/medicines/${id}/restock`, { quantity });
export const getLowStock = () => client.get("/medicines/low_stock");23

// ─── PRESCRIPTIONS ───
export const createPrescription = (data) => client.post("/prescriptions/create", data);
export const getPendingPrescriptions = () => client.get("/prescriptions/pending");

// ─── PHARMACY ───
export const getPharmacyPending = () => client.get("/pharmacy/pending");
export const viewPrescription = (id) => client.get(`/pharmacy/prescription/${id}`);
export const dispensePrescription = (id, data) => client.post(`/pharmacy/dispense/${id}`, data);
export const deactivateStaff = (userId) =>
  client.put(`/admin/staff/${userId}/deactivate`);
export const clearAdminChat = () => client.post("/ai/admin/clear");

// ─── BILLING ───
export const createBill = (data) => client.post("/billing/create", data);
export const collectPayment = (billId, method) =>
  client.post(`/billing/${billId}/pay`, { payment_method: method });
export const getPendingBills = () => client.get("/billing/pending");
export const getTodayRevenue = () => client.get("/billing/today/revenue");
export const getReadyForBilling = () => client.get("/billing/ready");

// ─── ADMIN ───
export const createStaff = (data) => client.post("/admin/staff/create", data);
export const getAllStaff = () => client.get("/admin/staff/all");
export const setClinicFees = (data) => client.post("/admin/settings/fees", data);

// ─── AI AGENTS ───
export const aiGeneratePrescription = (data) => client.post("/ai/doctor/generate", data);
export const aiApprovePrescription = (data) => client.post("/ai/doctor/approve", data);
export const aiProcessPharmacy = (id) => client.post(`/ai/pharmacy/process/${id}`);
export const aiAdminAsk = (question) => client.post("/ai/admin/ask", { question });

// ─── EXPORT ───
export const exportData = () => client.get("/export/all", { responseType: "blob" });