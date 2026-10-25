import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import client from "../api/client";

const levelBadge = (l) => (l === "high" ? "danger" : l === "moderate" ? "warning" : "success");

export default function CaseList() {
  const { t } = useTranslation();
  const [cases, setCases] = useState(null);
  const [error, setError] = useState("");
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");

  useEffect(() => {
    client.get("/cases").then((r) => setCases(r.data)).catch(() => setError(t("history.loadError")));
  }, []);

  const statuses = cases ? [...new Set(cases.map((c) => c.status))] : [];
  const filtered = (cases || []).filter(
    (c) => (status === "all" || c.status === status) &&
      `${c.case_code} ${c.patient_ref_id}`.toLowerCase().includes(q.toLowerCase())
  );

  return (
    <div>
      <h2>{t("history.title")}</h2>
      <div className="card">
        <div className="filter-row">
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("history.search")} />
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="all">{t("history.allStatus")}</option>
            {statuses.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        {error && <div className="error-text">{error}</div>}
        {!cases && !error && <div className="loading-text">{t("common.loading")}</div>}
        {cases && filtered.length === 0 && (
          <div className="empty-state">{t("history.empty")} <Link to="/assessment">{t("nav.assessment")}</Link></div>
        )}
        {filtered.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead><tr>
                <th>{t("history.caseCode")}</th><th>{t("history.patientRef")}</th><th>{t("history.latest")}</th>
                <th>{t("history.symptoms")}</th><th>{t("history.created")}</th><th />
              </tr></thead>
              <tbody>
                {filtered.map((c) => (
                  <tr key={c.id}>
                    <td>{c.case_code}</td>
                    <td>{c.patient_ref_id}</td>
                    <td>{c.latest_class
                      ? <Link to={`/predictions/${c.latest_prediction_id}`}>{t(`classes.${c.latest_class}`)} · {(c.latest_confidence * 100).toFixed(0)}%</Link>
                      : "—"}</td>
                    <td>{c.symptom_level ? <span className={`badge badge-${levelBadge(c.symptom_level)}`}>{t(`assess.level.${c.symptom_level}`)}</span> : "—"}</td>
                    <td>{new Date(c.created_at).toLocaleDateString()}</td>
                    <td><Link to={`/cases/${c.id}`}>{t("common.open")}</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
