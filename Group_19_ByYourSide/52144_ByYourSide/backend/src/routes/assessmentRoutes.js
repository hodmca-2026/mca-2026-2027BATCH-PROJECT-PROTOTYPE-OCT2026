const express = require("express")
const authMiddleware = require("../middleware/authMiddleware")

const {
  predictAssessment,
  getAssessmentHistory,
  getAssessmentById,
} = require("../controllers/assessmentController")

const router = express.Router()

router.post("/", authMiddleware, predictAssessment)

router.get("/history", authMiddleware, getAssessmentHistory)

router.get("/:id", authMiddleware, getAssessmentById)

module.exports = router