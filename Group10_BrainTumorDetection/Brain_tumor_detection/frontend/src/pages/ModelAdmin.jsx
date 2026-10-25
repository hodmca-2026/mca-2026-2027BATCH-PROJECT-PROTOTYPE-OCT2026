import { useEffect, useState } from "react";
import client from "../api/client";

const pct = (v, d = 1) => (typeof v === "number" ? `${(v * 100).toFixed(d)}%` : "—");
const num = (v, d = 3) => (typeof v === "number" ? v.toFixed(d) : "—");

function ConfusionMatrix({ classes, matrix }) {
  const rowSum = matrix.map((r) => r.reduce((a, b) => a + b, 0) || 1);
  return (
    <div className="table-wrap">
      <table className="matrix">
        <thead><tr><th>True ↓ / Predicted →</th>{classes.map((c) => <th key={c}>{c}</th>)}</tr></thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={i}>
              <th>{classes[i]}</th>
              {row.map((v, j) => {
                const share = v / rowSum[i];
                return <td key={j} style={{ background: `rgba(37,99,235,${share * 0.85})`, color: share > 0.5 ? "#fff" : "inherit" }}>{v}</td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const Kv = ({ k, v }) => <div className="kv"><div className="k">{k}</div><div className="v">{v}</div></div>;

export default function ModelAdmin() {
  const [versions, setVersions] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    client.get("/models").then((r) => setVersions(r.data)).catch(() => setError("Could not load model versions."));
    client.get("/models/current").then((r) => setStatus(r.data)).catch(() => {});
  }, []);

  const m = status?.metrics;
  const tm = m?.test_metrics;
  const official = m?.test_metrics_official;
  const classes = m?.classes || status?.classes || [];
  const trained = status && !status.is_placeholder;

  return (
    <div>
      <h2>Model &amp; Admin</h2>

      {status && (
        <div className="card">
          <h2>Current model</h2>
          <p>
            <b>Architecture:</b> {status.architecture} &nbsp;
            {status.is_placeholder
              ? <span className="badge badge-warning">Untrained / demo placeholder</span>
              : <span className="badge badge-success">Trained</span>}
          </p>
          {status.is_placeholder && <div className="disclaimer">No trained model found. Train one with <code>ml/train.py</code> and restart the backend.</div>}
          {tm && trained && (
            <>
              <h3>Test metrics{official && official.n_images !== tm.n_images ? " (leakage-controlled)" : ""} — n = {tm.n_images}</h3>
              <div className="kv-grid">
                <Kv k="Accuracy" v={pct(tm.accuracy)} />
                <Kv k="Precision (macro)" v={pct(tm.precision_macro)} />
                <Kv k="Recall (macro)" v={pct(tm.recall_macro)} />
                <Kv k="F1 (macro)" v={pct(tm.f1_macro)} />
                <Kv k="ROC-AUC (OvR)" v={num(tm.roc_auc_ovr_macro)} />
                <Kv k="Confidence error (ECE)" v={num(tm.ece_uncalibrated ?? tm.ece)} />
              </div>
              {official && official.n_images !== tm.n_images && (
                <p className="muted small">Official Testing folder (n = {official.n_images}): accuracy {pct(official.accuracy)}.
                  {" "}The headline numbers exclude {m.dedup?.test_flagged_near_duplicates ?? 0} test images that are near-duplicates of training images.</p>
              )}
              {m.evaluation_protocol && <p className="muted small">{m.evaluation_protocol}</p>}
              {!m.evaluation_protocol && <p className="muted small">Run <code>python evaluate_model.py</code> in the ml folder for a leakage-controlled evaluation.</p>}
            </>
          )}
        </div>
      )}

      {tm?.confusion_matrix && trained && (
        <div className="card">
          <h2>Confusion matrix &amp; per-class results</h2>
          <ConfusionMatrix classes={classes} matrix={tm.confusion_matrix} />
          <h3>Per class</h3>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Class</th><th>Sensitivity</th><th>Specificity</th><th>Precision</th><th>F1</th></tr></thead>
              <tbody>
                {classes.map((c) => (
                  <tr key={c}>
                    <td>{c}</td>
                    <td>{pct(tm.per_class?.[c]?.sensitivity)}</td>
                    <td>{pct(tm.per_class?.[c]?.specificity)}</td>
                    <td>{pct(tm.classification_report?.[c]?.precision)}</td>
                    <td>{pct(tm.classification_report?.[c]?.["f1-score"])}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {m.dataset && <p className="muted small">Data: {m.dataset.name} — {m.dataset.train_images} training images, {m.dataset.test_official} test images.</p>}
        </div>
      )}

      <div className="card model-card">
        <h2>Model card</h2>
        <b>Intended use</b>
        <ul><li>Research and education: demonstrating explainable CNN decision support for brain MRI.</li>
            <li>A human (doctor/researcher) reviews every result and report.</li></ul>
        <b>Not intended for</b>
        <ul><li>Diagnosis, treatment decisions, or screening of real patients.</li>
            <li>Any scan type other than 2D brain MRI slices, or classes other than glioma, meningioma, pituitary tumor and no tumor.</li></ul>
        <b>Known limitations</b>
        <ul><li>Trained on one public dataset with no patient IDs, so scores can be optimistic even after near-duplicate filtering.</li>
            <li>Not validated on other hospitals, scanners, protocols, ages or populations.</li>
            <li>Grad-CAM shows model attention, not a tumor boundary.</li></ul>
      </div>

      <div className="card">
        <h2>Model versions</h2>
        {error && <div className="error-text">{error}</div>}
        {versions && versions.length === 0 && <div className="empty-state">No model versions registered yet.</div>}
        {versions && versions.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Version</th><th>Arch</th><th>Accuracy</th><th>Status</th><th>Deployment</th></tr></thead>
              <tbody>
                {versions.map((v) => (
                  <tr key={v.id}>
                    <td>{v.version_tag}</td><td>{v.architecture}</td><td>{v.accuracy ? pct(v.accuracy, 2) : "—"}</td>
                    <td>{v.is_placeholder ? <span className="badge badge-warning">placeholder</span> : <span className="badge badge-success">trained</span>}</td>
                    <td>{v.deployment_status}</td>
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
