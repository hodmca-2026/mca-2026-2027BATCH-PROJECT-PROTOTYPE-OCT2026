import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import client from "../api/client";
import { errMsg } from "../api/errors";

export default function PredictionResult() {
  const { predictionId } = useParams();
  const { t } = useTranslation();
  const [prediction, setPrediction] = useState(null);
  const [guidance, setGuidance] = useState(null);
  const [report, setReport] = useState(null);
  const [reviewText, setReviewText] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");

  useEffect(() => {
    client.get(`/predictions/${predictionId}`).then((r) => setPrediction(r.data)).catch(() => setError(t("result.loadError")));
    client.get(`/doctors/suggest/${predictionId}`).then((r) => setGuidance(r.data)).catch(() => {});
  }, [predictionId]);

  async function ensureReport() {
    if (report) return report;
    const res = await client.post("/reports/generate", { prediction_id: predictionId });
    setReport(res.data);
    setReviewText(res.data.reviewed_content || res.data.draft_content);
    return res.data;
  }

  async function run(name, fn) {
    setBusy(name);
    setError("");
    try { await fn(); } catch (err) { setError(errMsg(err, t("common.error"))); } finally { setBusy(""); }
  }

  const handleGenerate = () => run("generate", ensureReport);

  const handleSave = (approve) => run("save", async () => {
    const res = await client.put(`/reports/${report.id}/review`, { reviewed_content: reviewText, approve });
    setReport(res.data);
  });

  const handleDownload = () => run("download", async () => {
    let r = await ensureReport();
    const current = r.reviewed_content || r.draft_content;
    if (current !== reviewText) { // save unsaved edits so the PDF matches the screen
      r = (await client.put(`/reports/${r.id}/review`, { reviewed_content: reviewText, approve: r.review_status === "approved" })).data;
      setReport(r);
    }
    const res = await client.get(`/reports/${r.id}/download`, { responseType: "blob" });
    const url = URL.createObjectURL(res.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `brain-mri-report-${predictionId.slice(0, 8)}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  });

  if (error && !prediction) return <div className="error-text">{error}</div>;
  if (!prediction) return <div className="loading-text">{t("common.loading")}</div>;

  const pct = prediction.confidence_score * 100;
  const band = pct >= 85 ? "High" : pct >= 70 ? "Moderate" : "Low";
  const cls = t(`classes.${prediction.predicted_class}`);
  const sorted = Object.entries(prediction.all_class_probabilities).sort((a, b) => b[1] - a[1]);
  const a = guidance?.assessment;
  const levelBadge = (l) => (l === "high" ? "danger" : l === "moderate" ? "warning" : "success");

  return (
    <div>
      <h2>{t("result.title")}</h2>
      <p className="muted">{t("result.step")}</p>
      {error && <div className="error-text">{error}</div>}

      <div className="card">
        {prediction.model_version.includes("placeholder") && <div className="disclaimer">{t("result.placeholderWarning")}</div>}
        {pct < 70 && <div className="disclaimer warn">{t("result.lowConfidenceBanner")}</div>}
        <div className="result-head">
          <div><div className="muted small">{t("result.predictedClass")}</div><div className="big-value">{cls}</div></div>
          <div><div className="muted small">{t("result.confidence")}</div><div className="big-value">{pct.toFixed(1)}%</div></div>
          <div><div className="muted small">{t("result.model")}</div><div>{prediction.model_version}</div></div>
        </div>
        <h3>{t("result.probabilities")}</h3>
        {sorted.map(([k, p]) => (
          <div key={k}>
            <div className="prob-row"><span>{t(`classes.${k}`)}</span><span>{(p * 100).toFixed(1)}%</span></div>
            <div className="confidence-bar-track"><div className="confidence-bar-fill" style={{ width: `${p * 100}%` }} /></div>
          </div>
        ))}
      </div>

      <div className="card">
        <h2>{t("result.imagesTitle")}</h2>
        <div className="image-triple">
          {[["original", prediction.original_url], ["overlay", prediction.overlay_url], ["heatmap", prediction.heatmap_url]].map(([k, url]) => (
            <figure key={k}>{url && <img src={url} alt={t(`result.${k}`)} />}<figcaption>{t(`result.${k}`)}</figcaption></figure>
          ))}
        </div>
        <div className="disclaimer">{prediction.disclaimer}</div>
        <h3>{t("result.analysisTitle")}</h3>
        <p>{t(`result.analysis${band}`, { pct: pct.toFixed(1), cls })}</p>
        <p className="muted">{t("result.attention")}</p>
      </div>

      <div className="card">
        <h2>{t("result.symptomsTitle")}</h2>
        {a ? (
          <>
            <p><b>{t("result.symptomLevel")}:</b> <span className={`badge badge-${levelBadge(a.level)}`}>{t(`assess.level.${a.level}`)}</span> ({a.score}/{a.max_score})</p>
            {a.red_flags.length > 0 && (
              <p><b>{t("result.redFlags")}:</b> {a.red_flags.map((id) => t(`assess.q.${id}`)).join("; ")}</p>
            )}
          </>
        ) : <p className="muted">{t("result.noAssessment")}</p>}
      </div>

      <div className="card">
        <h2>{t("result.reportTitle")}</h2>
        <p className="muted">{t("result.reportHelp")}</p>
        {!report && (
          <button onClick={handleGenerate} disabled={!!busy}>{busy === "generate" ? t("result.generating") : t("result.generate")}</button>
        )}
        {report && (
          <>
            <p><span className={`badge ${report.review_status === "approved" ? "badge-success" : "badge-warning"}`}>
              {report.review_status === "approved" ? t("result.approved") : t("result.pending")}</span></p>
            <textarea rows={16} value={reviewText} onChange={(e) => setReviewText(e.target.value)} className="mono" />
            <div className="btn-row">
              <button className="btn-secondary" onClick={() => handleSave(false)} disabled={!!busy}>{t("result.saveEdits")}</button>
              <button onClick={() => handleSave(true)} disabled={!!busy}>{t("result.approve")}</button>
            </div>
          </>
        )}
        <div className="btn-row" style={{ marginTop: 14 }}>
          <button onClick={handleDownload} disabled={!!busy}>{busy === "download" ? t("result.downloading") : t("result.downloadPdf")}</button>
        </div>
      </div>

      {guidance && (
        <>
          <div className="card">
            <h2>{t("result.nextTitle")}</h2>
            <ul className="steps-list">
              {guidance.next_steps.map((s) => <li key={s.key}>{t(`guidance.${s.key}`, { defaultValue: s.text })}</li>)}
            </ul>
          </div>
          <div className="card">
            <h2>{t("result.doctorsTitle")}</h2>
            {guidance.doctors.some((d) => d.is_demo) && <div className="disclaimer">{t("result.doctorsNote")}</div>}
            <div className="doctor-grid">
              {guidance.doctors.map((d) => (
                <div className="doctor-card" key={d.id}>
                  <div className="doctor-name">{d.full_name} {d.is_demo && <span className="badge badge-neutral">{t("common.demo")}</span>}</div>
                  <div className="badge badge-success">{d.specialization}</div>
                  <div className="doctor-line"><b>{t("result.degree")}:</b> {d.degree}</div>
                  <div className="doctor-line"><b>{t("result.location")}:</b> {[d.hospital, d.address].filter(Boolean).join(", ")}</div>
                  <div className="doctor-line"><b>{t("result.phone")}:</b> {d.phone}</div>
                  <a className="btn btn-secondary" href={`tel:${d.phone.replace(/\s/g, "")}`}>{t("result.call")}</a>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
      <div className="disclaimer">{t("common.research")}</div>
    </div>
  );
}
