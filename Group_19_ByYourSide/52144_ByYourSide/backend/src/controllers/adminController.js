const pool = require("../config/db")

const getDashboardStats = async (req, res) => {
  try {
    const [[usersResult]] = await pool.execute(
      "SELECT COUNT(*) AS totalUsers FROM users"
    )

    const [[assessmentsResult]] = await pool.execute(
      "SELECT COUNT(*) AS totalAssessments FROM assessments"
    )

    const [[todayResult]] = await pool.execute(
      `SELECT COUNT(*) AS assessmentsToday
       FROM assessments
       WHERE DATE(created_at) = CURDATE()`
    )

    const [recentAssessments] = await pool.execute(
      `SELECT
        assessments.id,
        assessments.prediction,
        assessments.created_at,
        users.name AS user_name,
        users.email
       FROM assessments
       INNER JOIN users
         ON assessments.user_id = users.id
       ORDER BY assessments.created_at DESC
       LIMIT 5`
    )

    res.json({
      stats: {
        totalUsers: usersResult.totalUsers,
        totalAssessments: assessmentsResult.totalAssessments,
        assessmentsToday: todayResult.assessmentsToday,
      },
      recentAssessments,
    })
  } catch (error) {
    console.error("Admin dashboard error:", error.message)

    res.status(500).json({
      message: "Unable to load admin dashboard",
    })
  }
}

const getUsers = async (req, res) => {
  try {
    const [users] = await pool.execute(
      `SELECT id, name, email, role, created_at
       FROM users
       ORDER BY created_at DESC`
    )

    res.json({
      users,
    })
  } catch (error) {
    console.error("Admin users error:", error.message)

    res.status(500).json({
      message: "Unable to load users",
    })
  }
}
const updateUserRole = async (req, res) => {
  try {
    const { id } = req.params
    const { role } = req.body

    if (!["user", "admin"].includes(role)) {
      return res.status(400).json({
        message: "Invalid role",
      })
    }

    if (Number(id) === Number(req.user.id)) {
      return res.status(400).json({
        message: "You cannot change your own role",
      })
    }

    const [result] = await pool.execute(
      `UPDATE users
       SET role = ?
       WHERE id = ?`,
      [role, id]
    )

    if (result.affectedRows === 0) {
      return res.status(404).json({
        message: "User not found",
      })
    }

    res.json({
      message: "User role updated successfully",
    })
  } catch (error) {
    console.error("Update user role error:", error.message)

    res.status(500).json({
      message: "Unable to update user role",
    })
  }
}
const getAssessments = async (req, res) => {
  try {
    const [assessments] = await pool.execute(
      `SELECT
        assessments.id,
        assessments.user_id,
        users.name AS user_name,
        users.email,
        assessments.text,
        assessments.prediction,
        assessments.created_at
       FROM assessments
       INNER JOIN users
         ON assessments.user_id = users.id
       ORDER BY assessments.created_at DESC`
    )

    res.json({
      assessments,
    })
  } catch (error) {
    console.error("Admin assessments error:", error.message)

    res.status(500).json({
      message: "Unable to load assessments",
    })
  }
}

const getAnalytics = async (req, res) => {
  try {
    const [[totalResult]] = await pool.execute(
      `SELECT COUNT(*) AS totalAssessments
       FROM assessments`
    )

    const [predictionResults] = await pool.execute(
      `SELECT
        prediction,
        COUNT(*) AS count
       FROM assessments
       GROUP BY prediction
       ORDER BY count DESC`
    )

    const [dailyResults] = await pool.execute(
      `SELECT
        DATE(created_at) AS date,
        COUNT(*) AS count
       FROM assessments
       GROUP BY DATE(created_at)
       ORDER BY date ASC`
    )

    res.json({
      totalAssessments: totalResult.totalAssessments,
      predictions: predictionResults,
      dailyAssessments: dailyResults,
    })
  } catch (error) {
    console.error("Admin analytics error:", error.message)

    res.status(500).json({
      message: "Unable to load analytics",
    })
  }
}

module.exports = {
  getDashboardStats,
  getUsers,
  updateUserRole,
  getAssessments,
  getAnalytics,
}