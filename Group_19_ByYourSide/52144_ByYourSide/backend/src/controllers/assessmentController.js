const pool = require("../config/db")

const predictAssessment = async (req, res) => {
  try {
    const { text } = req.body

    if (typeof text !== "string" || !text.trim()) {
      return res.status(400).json({
        message: "Assessment text is required",
      })
    }

    const cleanedText = text.trim()

    if (cleanedText.length > 5000) {
      return res.status(400).json({
        message: "Assessment text must be 5000 characters or less",
      })
    }

    const response = await fetch("http://127.0.0.1:8000/predict", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: cleanedText,
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      return res.status(502).json({
        message: "ML service error",
        detail: data.detail,
      })
    }

    const prediction = data.prediction

    if (typeof prediction !== "string" || !prediction.trim()) {
      return res.status(502).json({
        message: "Invalid response from ML service",
      })
    }

    const [result] = await pool.execute(
      `INSERT INTO assessments (user_id, text, prediction)
       VALUES (?, ?, ?)`,
      [req.user.id, cleanedText, prediction]
    )

    res.json({
      message: "Assessment processed successfully",
      assessmentId: result.insertId,
      prediction,
    })
  } catch (error) {
    console.error("Assessment error:", error.message)

    res.status(503).json({
      message: "Unable to process assessment",
    })
  }
}

const getAssessmentHistory = async (req, res) => {
  try {
    const [assessments] = await pool.execute(
      `SELECT id, text, prediction, created_at
       FROM assessments
       WHERE user_id = ?
       ORDER BY created_at DESC`,
      [req.user.id]
    )

    res.json({
      assessments,
    })
  } catch (error) {
    console.error("History error:", error.message)

    res.status(500).json({
      message: "Unable to fetch assessment history",
    })
  }
}

const getAssessmentById = async (req, res) => {
  try {
    const { id } = req.params

    const [assessments] = await pool.execute(
      `SELECT id, text, prediction, created_at
       FROM assessments
       WHERE id = ? AND user_id = ?`,
      [id, req.user.id]
    )

    if (assessments.length === 0) {
      return res.status(404).json({
        message: "Assessment not found",
      })
    }

    res.json({
      assessment: assessments[0],
    })
  } catch (error) {
    console.error("Assessment details error:", error.message)

    res.status(500).json({
      message: "Unable to fetch assessment",
    })
  }
}

module.exports = {
  predictAssessment,
  getAssessmentHistory,
  getAssessmentById,
}