import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../AuthContext";
import BrainIllustration from "../components/BrainIllustration";
import LanguageSwitcher from "../components/LanguageSwitcher";

export default function Home() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const steps = [1, 2, 3, 4, 5];
  const features = [1, 2, 3, 4];

  return (
    <div className="public-page">
      <header className="pub-nav">
        <div className="brand"><span className="logo-dot" />{t("brand")}</div>
        <div className="pub-nav-actions">
          <LanguageSwitcher />
          {user ? (
            <Link className="btn" to="/dashboard">{t("nav.openApp")}</Link>
          ) : (
            <>
              <Link className="btn btn-secondary" to="/login">{t("nav.login")}</Link>
              <Link className="btn" to="/register">{t("nav.register")}</Link>
            </>
          )}
        </div>
      </header>

      <section className="hero">
        <div className="hero-text">
          <span className="pill">{t("home.badge")}</span>
          <h1>{t("home.title")}</h1>
          <p>{t("home.subtitle")}</p>
          <div className="hero-actions">
            <Link className="btn btn-lg" to={user ? "/assessment" : "/login"}>{t("home.cta")}</Link>
            {!user && <Link className="btn btn-secondary btn-lg" to="/login">{t("home.ctaSecondary")}</Link>}
          </div>
        </div>
        <BrainIllustration className="hero-art" />
      </section>

      <section className="section">
        <h2 className="section-title">{t("home.howTitle")}</h2>
        <div className="steps-grid">
          {steps.map((n) => (
            <div className="card step-card" key={n}>
              <div className="step-num">{n}</div>
              <h3>{t(`home.step${n}Title`)}</h3>
              <p>{t(`home.step${n}Desc`)}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section alt">
        <h2 className="section-title">{t("home.featuresTitle")}</h2>
        <div className="feature-grid">
          {features.map((n) => (
            <div className="card" key={n}>
              <h3>{t(`home.f${n}Title`)}</h3>
              <p>{t(`home.f${n}Desc`)}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="disclaimer big">
          <b>{t("home.disclaimerTitle")}:</b> {t("home.disclaimer")}
        </div>
      </section>

      <footer className="pub-footer">{t("home.footer")}</footer>
    </div>
  );
}
