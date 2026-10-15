 const express = require("express")
const cors = require("cors")

const userRoutes = require("./routes/userRoutes")
const authRoutes = require("./routes/authRoutes")
const assessmentRoutes = require("./routes/assessmentRoutes")
const adminRoutes = require("./routes/adminRoutes")

const app = express()

app.use(
  cors({
    origin: "http://localhost:5173",
  })
)

app.use(express.json())

app.use("/api/users", userRoutes)
app.use("/api/auth", authRoutes)
app.use("/api/assessment", assessmentRoutes)
app.use("/api/admin", adminRoutes)

app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    message: "ByYourSide backend is running",
  })
})

module.exports = app