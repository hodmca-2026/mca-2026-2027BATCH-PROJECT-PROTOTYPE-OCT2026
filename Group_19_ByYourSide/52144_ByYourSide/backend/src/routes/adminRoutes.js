const express = require("express")
const authMiddleware = require("../middleware/authMiddleware")

const {
  getDashboardStats,
  getUsers,
  updateUserRole,
  getAssessments,
  getAnalytics,
} = require("../controllers/adminController")

const router = express.Router()

const adminOnly = (req, res, next) => {
  if (req.user?.role !== "admin") {
    return res.status(403).json({
      message: "Admin access required",
    })
  }

  next()
}

router.get(
  "/dashboard",
  authMiddleware,
  adminOnly,
  getDashboardStats
)

router.get(
  "/users",
  authMiddleware,
  adminOnly,
  getUsers
)

router.patch(
  "/users/:id/role",
  authMiddleware,
  adminOnly,
  updateUserRole
)

router.get(
  "/assessments",
  authMiddleware,
  adminOnly,
  getAssessments
)

router.get(
  "/analytics",
  authMiddleware,
  adminOnly,
  getAnalytics
)

module.exports = router