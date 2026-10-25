import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import client from "../api/client";

export default function CaseDetail() {
  const { caseId } = useParams();
  const { t } = useTranslation();
  const [caseData, setCaseData] = useState(null);
  const [preds, setPreds] = useState([]);
  const [assessment, setAssessment] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    client.get(`/cases/${caseId}`).then((r) => setCaseData(r.data)).catch(() => setError(t("history.loadError")));
    client.get(`/cases/${caseId}/predictions`).then((r) => setPreds(r.data)).catch(() => {});
    client.get(`/symptoms/case/${caseId}`).then((r) => setAssessment(r.data)).catch(() => {});
  }, [caseId]);

  if (error) return <div className="error-text">{error}</div>;
  if (!caseData) return <div className="loading-text">{t("common.loading")}</div>;

  return (
    <div>
      <h2>{t("history.detailTitle")} {caseData.case_code}</h2>
      <div className="card">
        <p><b>{t("history.patientRef")}:</b> {caseData.patient_ref_id}</p>
        <p><b>{t("history.status")}:</b> <span className="badge badge-neutral">{caseData.status}</span></p>
        <p><b>{t("history.created")}:</b> {new Date(caseData.created_at).toLocaleString()}</p>
        {assessment && <p><b>{t("history.symptoms")}:</b> {t(`assess.level.${assessment.level}`)} ({assessment.score}/{assessment.max_score})</p>}
        <Link to="/cases">&larr; {t("common.back")}</Link>
      </div>
      <div className="card">
        <div className="page-head">
          <h2>{t("history.predictions")}</h2>
          <Link className="btn btn-secondary" to={`/scan/${caseId}`}>{t("history.addScan")}</Link>
        </div>
        {preds.length === 0 ? <div className="empty-state">{t("history.noPredictions")}</div> : (
          <table>
            <thead><tr><th>{t("result.predictedClass")}</th><th>{t("result.confidence")}</th><th>{t("result.model")}</th><th>{t("history.created")}</th><th /></tr></thead>
            <tbody>
              {preds.map((p) => (
                <tr key={p.id}>
                  <td>{t(`classes.${p.predicted_class}`)}</td>
                  <td>{(p.confidence_score * 100).toFixed(1)}%</td>
                  <td>{p.model_version}</td>
                  <td>{new Date(p.predicted_at).toLocaleString()}</td>
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
