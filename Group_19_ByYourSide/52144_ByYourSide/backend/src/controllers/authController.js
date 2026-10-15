const jwt = require("jsonwebtoken")
const bcrypt = require("bcryptjs")
const pool = require("../config/db")

const register = async (req, res) => {
  try {
    const { name, email, password } = req.body

    if (
      typeof name !== "string" ||
      typeof email !== "string" ||
      typeof password !== "string" ||
      !name.trim() ||
      !email.trim() ||
      !password
    ) {
      return res.status(400).json({
        message: "Name, email and password are required",
      })
    }

    const cleanedName = name.trim()
    const cleanedEmail = email.trim().toLowerCase()

    if (cleanedName.length > 100) {
      return res.status(400).json({
        message: "Name must be 100 characters or less",
      })
    }

    if (cleanedEmail.length > 255) {
      return res.status(400).json({
        message: "Email must be 255 characters or less",
      })
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cleanedEmail)) {
      return res.status(400).json({
        message: "Please enter a valid email address",
      })
    }

    if (password.length < 8) {
      return res.status(400).json({
        message: "Password must be at least 8 characters",
      })
    }

    if (password.length > 128) {
      return res.status(400).json({
        message: "Password must be 128 characters or less",
      })
    }

    const [existingUsers] = await pool.execute(
      "SELECT id FROM users WHERE email = ?",
      [cleanedEmail]
    )

    if (existingUsers.length > 0) {
      return res.status(409).json({
        message: "Email already registered",
      })
    }

    const hashedPassword = await bcrypt.hash(password, 10)

    await pool.execute(
      "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
      [cleanedName, cleanedEmail, hashedPassword]
    )

    res.status(201).json({
      message: "User registered successfully",
    })
  } catch (error) {
    console.error("Registration error:", error.message)

    res.status(500).json({
      message: "Internal server error",
    })
  }
}

const login = async (req, res) => {
  try {
    const { email, password } = req.body

    if (
      typeof email !== "string" ||
      typeof password !== "string" ||
      !email.trim() ||
      !password
    ) {
      return res.status(400).json({
        message: "Email and password are required",
      })
    }

    const cleanedEmail = email.trim().toLowerCase()

    if (cleanedEmail.length > 255) {
      return res.status(400).json({
        message: "Invalid email or password",
      })
    }

    const [users] = await pool.execute(
      "SELECT * FROM users WHERE email = ?",
      [cleanedEmail]
    )

    if (users.length === 0) {
      return res.status(401).json({
        message: "Invalid email or password",
      })
    }

    const user = users[0]

    const passwordMatch = await bcrypt.compare(
      password,
      user.password
    )

    if (!passwordMatch) {
      return res.status(401).json({
        message: "Invalid email or password",
      })
    }

    const token = jwt.sign(
      {
        id: user.id,
        role: user.role,
      },
      process.env.JWT_SECRET,
      {
        expiresIn: "1d",
      }
    )

    res.json({
      message: "Login successful",
      token,
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        role: user.role,
      },
    })
  } catch (error) {
    console.error("Login error:", error.message)

    res.status(500).json({
      message: "Internal server error",
    })
  }
}

module.exports = {
  register,
  login,
}