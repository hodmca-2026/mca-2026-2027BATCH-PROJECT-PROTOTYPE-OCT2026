import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import SupportGuidance from '../../components/SupportGuidance'

function Result() {
  const { id } = useParams()
  const { token } = useAuth()

  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(!!id)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) {
      const storedResult = sessionStorage.getItem('assessmentResult')

      if (storedResult) {
        setResult(JSON.parse(storedResult))
      }

      setLoading(false)
      return
    }

    const fetchAssessment = async () => {
      try {
        const response = await fetch(
          `http://localhost:5000/api/assessment/${id}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )

        const data = await response.json()

        if (!response.ok) {
          throw new Error(
            data.message || 'Unable to load assessment'
          )
        }

        setResult({
          text: data.assessment.text,
          prediction: data.assessment.prediction,
          created_at: data.assessment.created_at,
        })
      } catch (error) {
        setError(error.message)
      } finally {
        setLoading(false)
      }
    }

    fetchAssessment()
  }, [id, token])

  if (loading) {
    return (
      <main className="result-page">
        <section className="result-card result-empty">
          <span className="auth-label">Loading</span>

          <h1>Loading your check-in</h1>

          <p>
            We're retrieving your previous check-in and its guidance.
          </p>
        </section>
      </main>
    )
  }

  if (error) {
    return (
      <main className="result-page">
        <section className="result-card result-empty">
          <span className="auth-label">Unable to load</span>

          <h1>Check-in not found</h1>

          <p>{error}</p>

          <Link to="/history" className="button button-primary">
            Back to history
          </Link>
        </section>
      </main>
    )
  }

  if (!result) {
    return (
      <main className="result-page">
        <section className="result-card result-empty">
          <span className="auth-label">No result</span>

          <h1>No check-in found</h1>

          <p>
            Complete a check-in first to receive awareness and supportive
            guidance.
          </p>

          <Link to="/assessment" className="button button-primary">
            Start a check-in
          </Link>
        </section>
      </main>
    )
  }

  return (
    <main className="result-page">
      <section className="result-header">
        <span className="auth-label">
          {id ? 'Previous check-in' : 'Check-in result'}
        </span>

        <h1>What the check-in identified</h1>

        <p>
          Based on the information you provided, ByYourSide identified the
          following pattern. This is intended to support awareness and
          conversation, not provide a medical diagnosis.
        </p>
      </section>

      <section className="result-card result-pattern">
        <div className="result-pattern-header">
          <span className="result-label">Observed pattern</span>

          <span className="result-badge">Awareness</span>
        </div>

        <h2>{result.prediction}</h2>

        <p>
          This classification reflects patterns found in the information
          provided during the check-in. Consider the person's broader
          circumstances, recent changes, and behaviour when deciding how
          to respond.
        </p>
      </section>

      <section className="guidance-grid">
        <article className="guidance-card">
          <span className="guidance-number">01</span>

          <h2>What you can do</h2>

          <ul>
            <li>Choose a calm moment to talk with them.</li>
            <li>
              Listen without immediately judging or trying to fix things.
            </li>
            <li>
              Let them know that you are available to support them.
            </li>
            <li>
              Pay attention to changes that continue or become more
              concerning.
            </li>
          </ul>
        </article>

        <article className="guidance-card">
          <span className="guidance-number">02</span>

          <h2>What you can say</h2>

          <p>
            You don't need to have the perfect words. A simple and genuine
            conversation can be a good starting point.
          </p>

          <div className="support-quote">
            "I've noticed that things seem a little different lately. I'm
            here if you want to talk."
          </div>

          <Link to="/assessment" className="text-link">
            Check another observation →
          </Link>
        </article>
      </section>

      <SupportGuidance />

      <section className="guidance-notice">
        <div>
          <span className="result-label">Important</span>

          <h2>Look at the bigger picture</h2>

          <p>
            A check-in result is only one piece of information. It should
            not be treated as a diagnosis or as a prediction of what
            someone will do. If you are seriously concerned about
            someone's immediate safety, seek appropriate help from local
            emergency or professional support services.
          </p>
        </div>
      </section>

      <section className="result-actions">
        <Link to="/assessment" className="button button-primary">
          New check-in
        </Link>

        <Link to="/dashboard" className="button button-secondary">
          Back to dashboard
        </Link>
      </section>
    </main>
  )
}

export default Result