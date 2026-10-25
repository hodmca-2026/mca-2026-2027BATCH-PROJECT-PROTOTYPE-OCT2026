import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import client from "../api/client";
import { useAuth } from "../AuthContext";
import { errMsg } from "../api/errors";
import BrainIllustration from "../components/BrainIllustration";
import LanguageSwitcher from "../components/LanguageSwitcher";

export default function Register() {
  const { t } = useTranslation();
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "doctor" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/assessment" replace />;
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await client.post("/auth/register", form);
      await login(form.email, form.password);
      navigate("/assessment");
    } catch (err) {
      setError(errMsg(err, t("auth.registerFailed")));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <aside className="auth-side">
        <Link to="/" className="brand light"><span className="logo-dot" />{t("brand")}</Link>
        <BrainIllustration className="auth-art" />
        <h2>{t("auth.sideTitle")}</h2>
        <p>{t("auth.sideText")}</p>
      </aside>
      <main className="auth-main">
        <div className="auth-lang"><LanguageSwitcher /></div>
        <form className="auth-card" onSubmit={handleSubmit}>
          <h1>{t("auth.registerTitle")}</h1>
          <label>{t("auth.fullName")}</label>
          <input value={form.full_name} onChange={set("full_name")} required />
          <label>{t("auth.email")}</label>
          <input type="email" value={form.email} onChange={set("email")} required />
          <label>{t("auth.password")} <span className="muted small">({t("auth.passwordHint")})</span></label>
          <input type="password" value={form.password} onChange={set("password")} minLength={6} required />
          <label>{t("auth.role")}</label>
          <select value={form.role} onChange={set("role")}>
            <option value="doctor">{t("auth.doctor")}</option>
            <option value="researcher">{t("auth.researcher")}</option>
          </select>
          {error && <div className="error-text">{error}</div>}
          <button type="submit" disabled={loading} style={{ width: "100%" }}>
            {loading ? t("auth.creating") : t("auth.createAccount")}
          </button>
          <p className="muted small">{t("auth.haveAccount")} <Link to="/login">{t("nav.login")}</Link></p>
        </form>
      </main>
    </div>
  );
}
