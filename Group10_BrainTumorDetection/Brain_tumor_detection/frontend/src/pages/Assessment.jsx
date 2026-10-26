import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import client from "../api/client";
import { errMsg } from "../api/errors";

// Must match the question ids defined in backend/app/routers/symptoms.py
export const QUESTION_IDS = [
  "headache", "headache_morning", "nausea", "vision", "seizures", "weakness",
  "speech", "memory", "balance", "mood", "hearing", "persistent",
];

export default function Assessment() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [patientRef, setPatientRef] = useState("");
  const [answers, setAnswers] = useState(() => Object.fromEntries(QUESTION_IDS.map((q) => [q, 0])));
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!patientRef.trim()) { setError(t("assess.required")); return; }
    setError("");
    setLoading(true);
    try {
      const res = await client.post("/symptoms/assess", { patient_ref_id: patientRef.trim(), answers });
      navigate(`/scan/${res.data.case_id}`);
    } catch (err) {
      setError(errMsg(err, t("common.error")));
    } finally {
      setLoading(false);
    }
  }

  const options = [[0, "none"], [1, "sometimes"], [2, "often"]];

  return (
    <form onSubmit={handleSubmit}>
      <h2>{t("assess.title")}</h2>
      <p className="muted">{t("assess.intro")}</p>

      <div className="card">
        <label>{t("assess.patientRef")}</label>
        <input value={patientRef} onChange={(e) => setPatientRef(e.target.value)} placeholder="REF-10234" maxLength={60} />
        <div className="muted small" style={{ marginTop: -8 }}>{t("assess.patientRefHint")}</div>
      </div>

      <div className="card">
        {QUESTION_IDS.map((id) => (
          <div className="question-row" key={id}>
            <div className="question-text">{t(`assess.q.${id}`)}</div>
            <div className="segmented" role="radiogroup">
              {options.map(([value, key]) => (
                <label key={key} className={answers[id] === value ? "seg active" : "seg"}>
                  <input type="radio" name={id} checked={answers[id] === value}
                         onChange={() => setAnswers({ ...answers, [id]: value })} />
                  {t(`assess.${key}`)}
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>

      {error && <div className="error-text">{error}</div>}
      <button type="submit" disabled={loading}>{loading ? t("assess.submitting") : t("assess.submit")}</button>
      <div className="disclaimer">{t("common.research")}</div>
    </form>
  );
}
