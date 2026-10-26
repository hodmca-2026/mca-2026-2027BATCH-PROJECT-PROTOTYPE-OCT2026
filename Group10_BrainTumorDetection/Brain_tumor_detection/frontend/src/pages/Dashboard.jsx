import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import client from "../api/client";

export default function Dashboard() {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    client.get("/dashboard").then((r) => setData(r.data)).catch(() => setError(t("dashboard.loadError")));
  }, []);

  if (error) return <div className="error-text">{error}</div>;
  if (!data) return <div className="loading-text">{t("common.loading")}</div>;

  return (
    <div>
      <div className="page-head">
        <h2>{t("dashboard.title")}</h2>
        <Link className="btn" to="/assessment">{t("dashboard.startNow")}</Link>
      </div>
      {data.model_status.is_placeholder && <div className="disclaimer">⚠ {t("dashboard.placeholder")}</div>}
      <div className="card-grid">
        <div className="card stat-card"><div className="value">{data.total_cases}</div><div className="label">{t("dashboard.totalCases")}</div></div>
        <div className="card stat-card"><div className="value">{data.total_predictions}</div><div className="label">{t("dashboard.totalPredictions")}</div></div>
        <div className="card stat-card"><div className="value">{data.pending_reviews}</div><div className="label">{t("dashboard.pendingReviews")}</div></div>
        <div className="card stat-card"><div className="value" style={{ fontSize: 18 }}>🟢 {t("dashboard.operational")}</div><div className="label">{t("dashboard.systemStatus")}</div></div>
      </div>
      <div className="card">
        <h2>{t("dashboard.recent")}</h2>
        {data.recent_predictions.length === 0 ? (
          <div className="empty-state">{t("dashboard.empty")}</div>
        ) : (
          <table>
            <thead><tr><th>{t("history.caseCode")}</th><th>{t("result.predictedClass")}</th><th>{t("result.confidence")}</th><th /></tr></thead>
            <tbody>
              {data.recent_predictions.map((p) => (
                <tr key={p.id}>
                  <td>{p.case_code}</td>
                  <td>{t(`classes.${p.predicted_class}`)}</td>
                  <td>{(p.confidence_score * 100).toFixed(1)}%</td>
                  <td><Link to={`/predictions/${p.id}`}>{t("common.view")}</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
