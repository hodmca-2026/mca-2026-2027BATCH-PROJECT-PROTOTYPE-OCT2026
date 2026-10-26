import { useTranslation } from "react-i18next";

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  function change(e) {
    i18n.changeLanguage(e.target.value);
    localStorage.setItem("lang", e.target.value);
  }
  return (
    <select className="lang-select" value={i18n.language} onChange={change} aria-label={t("common.language")}>
      <option value="en">English</option>
      <option value="hi">हिन्दी</option>
      <option value="mr">मराठी</option>
    </select>
  );
}
