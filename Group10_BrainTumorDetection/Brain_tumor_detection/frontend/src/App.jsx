import { Routes, Route, Navigate, NavLink, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "./AuthContext";
import LanguageSwitcher from "./components/LanguageSwitcher";

import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Assessment from "./pages/Assessment";
import UploadScan from "./pages/UploadScan";
import CaseList from "./pages/CaseList";
import CaseDetail from "./pages/CaseDetail";
import PredictionResult from "./pages/PredictionResult";
import ModelAdmin from "./pages/ModelAdmin";

function ProtectedLayout({ children }) {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link to="/" className="brand"><span className="logo-dot" />{t("brand")}</Link>
        <nav>
          <NavLink to="/assessment">{t("nav.assessment")}</NavLink>
          <NavLink to="/dashboard">{t("nav.dashboard")}</NavLink>
          <NavLink to="/cases">{t("nav.cases")}</NavLink>
          <NavLink to="/admin">{t("nav.admin")}</NavLink>
        </nav>
      </aside>
      <div className="main">
        <div className="topbar">
          <div className="user-chip">{user.full_name} &middot; {user.role}</div>
          <div className="topbar-actions">
            <LanguageSwitcher />
            <button className="btn-secondary" onClick={logout}>{t("nav.logout")}</button>
          </div>
        </div>
        {children}
      </div>
    </div>
  );
}

function NotFound() {
  const { t } = useTranslation();
  return (
    <div className="login-shell"><div className="card" style={{ textAlign: "center" }}>
      <h2>404</h2><p>{t("common.notFound")}</p><Link to="/">{t("common.goHome")}</Link>
    </div></div>
  );
}

const P = (el) => <ProtectedLayout>{el}</ProtectedLayout>;

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/assessment" element={P(<Assessment />)} />
      <Route path="/scan/:caseId" element={P(<UploadScan />)} />
      <Route path="/predictions/:predictionId" element={P(<PredictionResult />)} />
      <Route path="/dashboard" element={P(<Dashboard />)} />
      <Route path="/cases" element={P(<CaseList />)} />
      <Route path="/cases/:caseId" element={P(<CaseDetail />)} />
      <Route path="/admin" element={P(<ModelAdmin />)} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
