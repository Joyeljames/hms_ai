import { useState } from "react";
import { Sparkles, Package, Users, Settings } from "lucide-react";
import Layout from "../../components/layout/Layout";
import AssistantPanel from "./AssistantPanel";
import InventoryPanel from "./InventoryPanel";
import StaffPanel from "./StaffPanel";
import SettingsPanel from "./SettingsPanel";

const TABS = [
  { id: "assistant", label: "AI Assistant", icon: Sparkles },
  { id: "inventory", label: "Inventory", icon: Package },
  { id: "staff", label: "Staff", icon: Users },
  { id: "settings", label: "Settings", icon: Settings },
];

export default function AdminDashboard() {
  const [tab, setTab] = useState("assistant");

  return (
    <Layout>
      <div className="mb-6 flex flex-wrap gap-2">
        {TABS.map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium ${
                tab === t.id
                  ? "bg-gray-900 text-white"
                  : "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
              }`}
            >
              <Icon size={16} />
              {t.label}
            </button>
          );
        })}
      </div>

      {tab === "assistant" && <AssistantPanel />}
      {tab === "inventory" && <InventoryPanel />}
      {tab === "staff" && <StaffPanel />}
      {tab === "settings" && <SettingsPanel />}
    </Layout>
  );
}