import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import client from "../api/client";
import { errMsg } from "../api/errors";

export default function UploadScan() {
  const { caseId } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [caseData, setCaseData] = useState(null);
  const [assessment, setAssessment] = useState(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");
  const [stage, setStage] = useState("");

  useEffect(() => {
    client.get(`/cases/${caseId}`).then((r) => setCaseData(r.data)).catch(() => setError(t("common.error")));
    client.get(`/symptoms/case/${caseId}`).then((r) => setAssessment(r.data)).catch(() => {});
  }, [caseId]);

  function onSelect(e) {
    const f = e.target.files[0];
    if (!f) return;
    if (!["image/jpeg", "image/png"].includes(f.type)) { setError(t("scan.badType")); return; }
    if (f.size > 10 * 1024 * 1024) { setError(t("scan.tooLarge")); return; }
    setError("");
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) { setError(t("scan.noFile")); return; }
    setError("");
    try {
      setStage("uploading");
      const fd = new FormData();
      fd.append("file", file);
      const up = await client.post(`/cases/${caseId}/upload`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      setStage("predicting");
      const pred = await client.post("/predictions", { image_id: up.data.image_id });
      navigate(`/predictions/${pred.data.id}`);
    } catch (err) {
      setError(errMsg(err, t("common.error")));
      setStage("");
    }
  }

  return (
    <div>
      <h2>{t("scan.title")}</h2>
      <p className="muted">{t("scan.step")}</p>

      {caseData && (
        <div className="card">
          <b>{t("scan.case")}:</b> {caseData.case_code} &middot; {caseData.patient_ref_id}
          {assessment && (
            <> &nbsp;|&nbsp; <b>{t("scan.symptomIndicator")}:</b>{" "}
              <span className={`badge badge-${assessment.level === "high" ? "danger" : assessment.level === "moderate" ? "warning" : "success"}`}>
                {t(`assess.level.${assessment.level}`)}
              </span></>
          )}
        </div>
      )}

      <form className="card" style={{ maxWidth: 560 }} onSubmit={handleSubmit}>
        <label className="upload-box" style={{ display: "block", marginBottom: 14 }}>
          {preview
            ? <img src={preview} alt="preview" style={{ maxWidth: "100%", maxHeight: 260, borderRadius: 8 }} />
            : <span>{t("scan.choose")}</span>}
          <input type="file" accept="image/jpeg,image/png" onChange={onSelect} hidden />
        </label>
        {error && <div className="error-text">{error}</div>}
        {stage && <div className="loading-text" style={{ marginBottom: 12 }}>{t(`scan.${stage}`)}</div>}
        <button type="submit" disabled={!!stage} style={{ width: "100%" }}>{t("scan.run")}</button>
      </form>
      <div className="disclaimer">{t("common.research")}</div>
    </div>
  );
}
