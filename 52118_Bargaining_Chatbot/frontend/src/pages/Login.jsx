import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Sparkles, User, Store } from "lucide-react";
import { useUser } from "../context/UserContext";
import { api } from "../lib/api";

export default function Login() {
  const [mode, setMode] = useState("login"); // login | signup
  const [role, setRole] = useState("customer");
  const [form, setForm] = useState({ name: "", email: "", password: "", phone: "" });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login } = useUser();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = mode === "login"
        ? await api.login({ email: form.email, password: form.password })
        : await api.signup({ ...form, role });
      login(data.token, data.user);
      if (data.user.role === "seller") navigate("/seller");
      else if (data.user.role === "admin") navigate("/admin");
      else navigate("/");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-md mx-auto px-6 py-16">
      <div className="flex items-center gap-2 justify-center mb-8">
        <div className="w-9 h-9 rounded-full bg-ink flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-marigold" />
        </div>
        <span className="font-display text-2xl text-ink">Bazaaro</span>
      </div>

      <div className="flex bg-ink/5 rounded-full p-1 mb-8">
        <button onClick={() => setMode("login")} className={`flex-1 py-2 rounded-full text-sm font-medium transition-colors ${mode === "login" ? "bg-white shadow-sm text-ink" : "text-ink-soft"}`}>
          Log in
        </button>
        <button onClick={() => setMode("signup")} className={`flex-1 py-2 rounded-full text-sm font-medium transition-colors ${mode === "signup" ? "bg-white shadow-sm text-ink" : "text-ink-soft"}`}>
          Sign up
        </button>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {mode === "signup" && (
          <>
            <div className="flex gap-2">
              <RoleButton icon={User} label="Customer" active={role === "customer"} onClick={() => setRole("customer")} />
              <RoleButton icon={Store} label="Seller" active={role === "seller"} onClick={() => setRole("seller")} />
            </div>
            <input required placeholder="Full name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" />
            <input placeholder="Phone (optional)" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="input" />
          </>
        )}
        <input required type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input" />
        <input required type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="input" />

        {error && <p className="text-rani text-sm">{error}</p>}

        <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} disabled={loading} type="submit" className="bg-ink text-ivory py-3.5 rounded-full font-medium mt-2 disabled:opacity-60">
          {loading ? "Please wait..." : mode === "login" ? "Log in" : "Create account"}
        </motion.button>
      </form>

      <p className="text-center text-xs text-ink-soft/70 mt-8">
        Demo logins (password: password123): seller@bazaaro.com · admin@bazaaro.com · customer@bazaaro.com
      </p>

      <style>{`.input { background: white; border: 1px solid rgba(27,26,46,0.1); border-radius: 9999px; padding: 0.9rem 1.25rem; font-size: 0.875rem; outline: none; } .input:focus { border-color: #B8305C; }`}</style>
    </div>
  );
}

function RoleButton({ icon: Icon, label, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl text-sm font-medium border transition-colors ${
        active ? "bg-ink text-ivory border-ink" : "border-ink/15 text-ink-soft"
      }`}
    >
      <Icon className="w-4 h-4" /> {label}
    </button>
  );
}
