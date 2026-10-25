import { useState } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

export default function NewCase() {
  const navigate = useNavigate();
  const [patientRef, setPatientRef] = useState("");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState(""); // "creating" | "uploading" | "predicting"

  function handleFileSelect(e) {
    const f = e.target.files[0];
    if (!f) return;
    if (!["image/jpeg", "image/png"].includes(f.type)) {
      setError("Only JPEG or PNG images are supported.");
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      setError("File exceeds 10MB limit.");
      return;
    }
    setError("");
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!patientRef || !file) {
      setError("Patient reference ID and an MRI image are required.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      setStage("creating");
      const caseRes = await client.post("/cases", { patient_ref_id: patientRef });
      const caseId = caseRes.data.id;

      setStage("uploading");
      const formData = new FormData();
      formData.append("file", file);
      const uploadRes = await client.post(`/cases/${caseId}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setStage("predicting");
      const predRes = await client.post("/predictions", { image_id: uploadRes.data.image_id });

      navigate(`/predictions/${predRes.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
      setStage("");
    }
  }

  const stageLabel = {
    creating: "Creating case...",
    uploading: "Validating and uploading MRI...",
    predicting: "Running CNN prediction and Grad-CAM explanation...",
  }[stage];

  return (
    <div>
      <h2>New Case — MRI Upload</h2>
      <div className="card" style={{ maxWidth: 520 }}>
        <form onSubmit={handleSubmit}>
          <label>Patient Reference ID</label>
          <input
            value={patientRef}
            onChange={(e) => setPatientRef(e.target.value)}
            placeholder="e.g. REF-10234 (no personal names)"
            required
          />

          <label>MRI Image (JPEG/PNG, max 10MB)</label>
          <label className="upload-box" style={{ display: "block", marginBottom: 14 }}>
            {preview ? (
              <img src={preview} alt="preview" style={{ maxWidth: "100%", maxHeight: 220, borderRadius: 8 }} />
            ) : (
              <span>Click to select an MRI image</span>
            )}
            <input type="file" accept="image/jpeg,image/png" onChange={handleFileSelect} hidden />
          </label>

          {error && <div className="error-text">{error}</div>}
          {loading && <div className="loading-text" style={{ marginBottom: 14 }}>{stageLabel}</div>}

          <button type="submit" disabled={loading} style={{ width: "100%" }}>
            {loading ? "Processing..." : "Upload & Run Prediction"}
          </button>
        </form>
      </div>
    </div>
  );
}
