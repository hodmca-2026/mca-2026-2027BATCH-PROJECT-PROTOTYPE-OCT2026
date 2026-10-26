import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../AuthContext";
import { errMsg } from "../api/errors";
import BrainIllustration from "../components/BrainIllustration";
import LanguageSwitcher from "../components/LanguageSwitcher";

export default function Login() {
  const { t } = useTranslation();
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/assessment" replace />;

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/assessment"); // questionnaire is the first screen after login
    } catch (err) {
      setError(errMsg(err, t("auth.failed")));
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
          <h1>{t("auth.loginTitle")}</h1>
          <p className="muted">{t("auth.loginSubtitle")}</p>
          <label>{t("auth.email")}</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required autoFocus />
          <label>{t("auth.password")}</label>
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
          {error && <div className="error-text">{error}</div>}
          <button type="submit" disabled={loading} style={{ width: "100%" }}>
            {loading ? t("auth.signingIn") : t("auth.submit")}
          </button>
          <p className="muted small">{t("auth.noAccount")} <Link to="/register">{t("nav.register")}</Link></p>
          <p className="muted small">{t("auth.demoHint")}</p>
          <div className="disclaimer">{t("common.research")}</div>
        </form>
      </main>
    </div>
  );
}
