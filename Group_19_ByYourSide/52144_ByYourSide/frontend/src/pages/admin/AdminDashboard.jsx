import { useEffect, useState } from 'react'
import { useAuth } from '../../context/AuthContext'

function AdminDashboard() {
  const { token } = useAuth()

  const [dashboard, setDashboard] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await fetch(
          'http://localhost:5000/api/admin/dashboard',
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )

        const data = await response.json()

        if (!response.ok) {
          throw new Error(
            data.message || 'Unable to load admin dashboard'
          )
        }

        setDashboard(data)
      } catch (error) {
        setError(error.message)
      } finally {
        setLoading(false)
      }
    }

    fetchDashboard()
  }, [token])

  if (loading) {
    return (
      <main className="admin-dashboard-page">
        <section className="admin-dashboard-state">
          <p>Loading dashboard...</p>
        </section>
      </main>
    )
  }

  if (error) {
    return (
      <main className="admin-dashboard-page">
        <section className="admin-dashboard-state admin-dashboard-error">
          <span className="auth-label">Error</span>

          <h1>Unable to load dashboard</h1>

          <p>{error}</p>
        </section>
      </main>
    )
  }

  return (
    <main className="admin-dashboard-page">
      <section className="admin-dashboard-header">
        <span className="auth-label">Administration</span>

        <h1>Admin Dashboard</h1>

        <p>
          Monitor users, assessments, and activity across ByYourSide.
        </p>
      </section>

      <section className="admin-stat-grid">
        <article className="admin-stat-card">
          <span className="admin-stat-label">Total Users</span>

          <strong>{dashboard.stats.totalUsers}</strong>

          <p>Registered users</p>
        </article>

        <article className="admin-stat-card">
          <span className="admin-stat-label">Total Assessments</span>

          <strong>{dashboard.stats.totalAssessments}</strong>

          <p>Completed check-ins</p>
        </article>

        <article className="admin-stat-card">
          <span className="admin-stat-label">Today</span>

          <strong>{dashboard.stats.assessmentsToday}</strong>

          <p>Assessments today</p>
        </article>
      </section>

      <section className="admin-recent-section">
        <div className="admin-section-header">
          <div>
            <span className="admin-stat-label">Activity</span>

            <h2>Recent assessments</h2>
          </div>
        </div>

        {dashboard.recentAssessments.length === 0 ? (
          <div className="admin-empty-state">
            <p>No assessments have been submitted yet.</p>
          </div>
        ) : (
          <div className="admin-assessment-list">
            {dashboard.recentAssessments.map((assessment) => (
              <article
                className="admin-assessment-card"
                key={assessment.id}
              >
                <div className="admin-assessment-main">
                  <span className="admin-stat-label">Pattern</span>

                  <h3>{assessment.prediction}</h3>

                  <p>
                    Submitted by {assessment.user_name}
                  </p>
                </div>

                <div className="admin-assessment-meta">
                  <span>{assessment.email}</span>

                  <time>
                    {new Date(
                      assessment.created_at
                    ).toLocaleString('en-IN', {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    })}
                  </time>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}

export default AdminDashboard