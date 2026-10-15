import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

function Dashboard() {
  const { user } = useAuth()

  return (
    <main className="dashboard-page">
      <section className="dashboard-header">
        <span className="auth-label">Your space</span>

        <h1>
          Welcome, {user?.name}
        </h1>

        <p>
          Take a moment to check in, understand what someone may be going
          through, and find ways to offer support.
        </p>
      </section>

      <section className="dashboard-actions">
        <Link to="/assessment" className="dashboard-card">
          <span className="dashboard-card-label">Start a check-in</span>

          <h2>Understand what may be happening</h2>

          <p>
            Share a few observations about someone you care about and receive
            supportive guidance.
          </p>

          <span className="dashboard-card-link">
            Start check-in →
          </span>
        </Link>

        <Link to="/history" className="dashboard-card">
          <span className="dashboard-card-label">Your history</span>

          <h2>Review previous check-ins</h2>

          <p>
            View your previous check-ins and the guidance provided.
          </p>

          <span className="dashboard-card-link">
            View history →
          </span>
        </Link>
      </section>

      <section className="dashboard-info">
        <div>
          <span className="dashboard-card-label">Remember</span>

          <h2>Notice. Understand. Respond.</h2>

          <p>
            ByYourSide is designed to help you notice concerning patterns and
            think about supportive ways to respond. It does not provide a
            medical diagnosis.
          </p>
        </div>
      </section>
    </main>
  )
}

export default Dashboard