"""
End-to-end API test: register -> login -> symptom questionnaire -> MRI upload -> prediction
-> Grad-CAM file URLs -> report -> PDF download -> doctor suggestions -> history.

The CNN itself is replaced by a tiny stub (so the test runs without PyTorch); everything else
(auth, validation, DB, file serving, PDF, guidance) is the real code.

Run from backend/:   python tests/test_flow.py     (or: pytest tests)
Needs: pip install pytest httpx
"""
import os
import shutil
import sys
import tempfile
import types
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"

from PIL import Image  # noqa: E402

fake = types.ModuleType("app.ml.inference")
fake.DISCLAIMER_TEXT = "The highlighted region shows areas that contributed to the model's prediction."
fake.get_model_status = lambda: {"is_placeholder": True, "architecture": "resnet18",
                                 "classes": ["glioma", "meningioma", "notumor", "pituitary"], "metrics": None}


def _predict(image_path, heatmap_path, overlay_path):
    img = Image.open(image_path).convert("RGB").resize((224, 224))
    img.save(heatmap_path)
    img.save(overlay_path)
    return {"predicted_class": "meningioma", "confidence_score": 0.62,
            "all_class_probabilities": {"glioma": 0.1, "meningioma": 0.62, "notumor": 0.2, "pituitary": 0.08},
            "is_placeholder": True, "disclaimer": fake.DISCLAIMER_TEXT}


fake.predict_with_explanation = _predict
sys.modules["app.ml.inference"] = fake

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.core.config import settings  # noqa: E402


def _png(size=160, kind="mri"):
    import numpy as np
    rng = np.random.default_rng(1)
    yy, xx = np.mgrid[0:size, 0:size]
    g = (255 * np.exp(-((yy - size / 2) ** 2 + (xx - size / 2) ** 2) / (2 * (size / 4) ** 2))
         + rng.normal(0, 8, (size, size))).clip(0, 255).astype("uint8")
    im = Image.fromarray(g, "L")
    if kind == "color":
        im = Image.merge("RGB", (im, im.point(lambda v: 255 - v), im.point(lambda v: v // 3)))
    if kind == "blank":
        im = Image.new("L", (size, size), 120)
    buf = BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def test_full_flow():
    c = TestClient(app)
    assert c.get("/api/health").json() == {"status": "ok"}

    # admins cannot self-register
    r = c.post("/api/auth/register", json={"full_name": "X", "email": "evil@example.com",
                                           "password": "secret1", "role": "admin"})
    assert r.status_code == 403

    r = c.post("/api/auth/register", json={"full_name": "Tester", "email": "tester@example.com",
                                           "password": "secret1", "role": "doctor"})
    assert r.status_code == 201, r.text
    token = c.post("/api/auth/login", json={"email": "tester@example.com", "password": "secret1"}).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    assert c.get("/api/cases").status_code == 401  # auth required

    # symptom questionnaire creates the case
    r = c.post("/api/symptoms/assess", headers=h, json={"patient_ref_id": "REF-001",
              "answers": {"headache": 2, "seizures": 1, "nausea": 1}})
    assert r.status_code == 201, r.text
    a = r.json()
    assert a["level"] in ("moderate", "high") and "seizures" in a["red_flags"]
    case_id = a["case_id"]
    assert c.post("/api/symptoms/assess", headers=h, json={"patient_ref_id": "R", "answers": {"bogus": 1}}).status_code == 400
    assert c.post("/api/symptoms/assess", headers=h, json={"patient_ref_id": "R", "answers": {"headache": 5}}).status_code == 400

    # upload validation
    bad = c.post(f"/api/cases/{case_id}/upload", headers=h, files={"file": ("x.png", b"not an image", "image/png")})
    assert bad.status_code == 400
    bad = c.post(f"/api/cases/{case_id}/upload", headers=h, files={"file": ("x.txt", b"hi", "text/plain")})
    assert bad.status_code == 400
    for name, data in (("photo.png", _png(kind="color")), ("tiny.png", _png(size=64)), ("blank.png", _png(kind="blank"))):
        r = c.post(f"/api/cases/{case_id}/upload", headers=h, files={"file": (name, data, "image/png")})
        assert r.status_code == 400, (name, r.status_code, r.text)
    up = c.post(f"/api/cases/{case_id}/upload", headers=h, files={"file": ("scan.png", _png(), "image/png")})
    assert up.status_code == 200, up.text

    # prediction + files
    r = c.post("/api/predictions", headers=h, json={"image_id": up.json()["image_id"]})
    assert r.status_code == 201, r.text
    p = r.json()
    for key in ("original_url", "overlay_url", "heatmap_url"):
        assert p[key].startswith("/api/files/"), p
        assert c.get(p[key]).status_code == 200
    assert c.get("/api/files/../../etc/passwd").status_code in (404, 422)
    assert c.get(f"/api/predictions/{p['id']}/explanation", headers=h).status_code == 200

    # report + PDF
    rep = c.post("/api/reports/generate", headers=h, json={"prediction_id": p["id"]})
    assert rep.status_code == 201, rep.text
    pdf = c.get(f"/api/reports/{rep.json()['id']}/download", headers=h)
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF", pdf.text[:200]
    assert c.put(f"/api/reports/{rep.json()['id']}/review", headers=h,
                 json={"reviewed_content": "Reviewed.", "approve": True}).json()["review_status"] == "approved"

    # guidance + doctors
    g = c.get(f"/api/doctors/suggest/{p['id']}", headers=h).json()
    assert g["doctors"] and all(d["phone"] and d["degree"] and d["city"] for d in g["doctors"])
    keys = [s["key"] for s in g["next_steps"]]
    assert "placeholder" in keys and "low_confidence" in keys and "symptoms_urgent" in keys
    assert "consult_specialist" in keys
    assert not any("treat" in s["text"].lower() and "medicat" in s["text"].lower() for s in g["next_steps"])

    # history
    cases = c.get("/api/cases", headers=h).json()
    row = [x for x in cases if x["id"] == case_id][0]
    assert row["latest_class"] == "meningioma" and row["symptom_level"] == a["level"]
    assert c.get(f"/api/cases/{case_id}/predictions", headers=h).json()[0]["id"] == p["id"]
    assert c.get("/api/dashboard", headers=h).status_code == 200

    shutil.rmtree(settings.UPLOAD_DIR / case_id, ignore_errors=True)


if __name__ == "__main__":
    test_full_flow()
    print("ALL OK")
