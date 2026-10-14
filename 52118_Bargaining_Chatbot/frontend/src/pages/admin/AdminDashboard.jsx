import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Users, ShieldAlert, TrendingUp, Flag } from "lucide-react";
import { api } from "../../lib/api";
import { useUser } from "../../context/UserContext";

export default function AdminDashboard() {
  const { user, isAuthenticated } = useUser();
  const navigate = useNavigate();
  const [overview, setOverview] = useState(null);
  const [users, setUsers] = useState([]);
  const [tab, setTab] = useState("overview");

  function refresh() {
    api.adminOverview().then(setOverview).catch(() => {});
    api.adminUsers().then(setUsers).catch(() => {});
  }

  useEffect(() => {
    if (!isAuthenticated || user?.role !== "admin") { navigate("/login"); return; }
    refresh();
  }, [isAuthenticated]);

  async function toggleFlag(u) {
    if (u.is_flagged) await api.adminUnflagUser(u.id);
    else await api.adminFlagUser(u.id, "Manually flagged by admin");
    refresh();
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <h1 className="font-display text-3xl text-ink mb-1">Admin Panel</h1>
      <p className="text-ink-soft text-sm mb-8">Platform-wide bargaining health and fraud monitoring</p>

      <div className="flex gap-2 mb-8">
        {["overview", "users"].map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 rounded-full text-sm font-medium ${tab === t ? "bg-ink text-ivory" : "bg-ink/5 text-ink-soft"}`}>
            {t[0].toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === "overview" && overview && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Stat icon={Users} label="Total Users" value={overview.total_users} />
          <Stat icon={ShieldAlert} label="Flagged Accounts" value={overview.flagged} />
          <Stat icon={TrendingUp} label="Negotiations" value={`${overview.accepted}/${overview.total}`} sub="accepted / total" />
          <Stat icon={TrendingUp} label="GMV" value={`₹${Number(overview.gmv).toLocaleString("en-IN")}`} />
        </div>
      )}

      {tab === "users" && (
        <div className="flex flex-col gap-2">
          {users.map((u) => (
            <div key={u.id} className="bg-white rounded-2xl p-4 flex items-center gap-4 shadow-sm">
              <div className="flex-1">
                <p className="font-medium text-ink">{u.name} <span className="text-xs text-ink-soft">({u.role})</span></p>
                <p className="text-xs text-ink-soft">{u.email}</p>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-full bg-ink/5 text-ink-soft">{u.trust_tier} · {u.trust_score}</span>
              {u.is_flagged && <span className="text-xs px-2.5 py-1 rounded-full bg-rani/10 text-rani flex items-center gap-1"><Flag className="w-3 h-3" /> Flagged</span>}
              <motion.button whileTap={{ scale: 0.95 }} onClick={() => toggleFlag(u)} className={`text-xs px-4 py-2 rounded-full font-medium ${u.is_flagged ? "bg-sage/10 text-sage" : "bg-rani/10 text-rani"}`}>
                {u.is_flagged ? "Unflag" : "Flag"}
              </motion.button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Stat({ icon: Icon, label, value, sub }) {
  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm">
      <Icon className="w-5 h-5 text-rani mb-3" strokeWidth={1.5} />
      <p className="font-display text-2xl text-ink">{value}</p>
      <p className="text-xs text-ink-soft">{sub || label}</p>
    </div>
  );
}
