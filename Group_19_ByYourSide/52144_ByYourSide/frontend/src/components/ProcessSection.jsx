function ProcessSection() {
  return (
    <section className="process-section" id="how-it-works">
      <div className="container">
        <div className="section-heading">
          <span className="eyebrow">The ByYourSide approach</span>

          <h2>Notice. Understand. Respond.</h2>

          <p>
            You don't need to have all the answers. Sometimes the first
            step is simply paying attention.
          </p>
        </div>

        <div className="process-grid">
          <article className="process-card">
            <div className="process-number">01</div>
            <div className="process-icon">👀</div>

            <h3>Notice</h3>

            <p>
              Describe the changes you've noticed in someone's behaviour,
              communication, or everyday interactions.
            </p>
          </article>

          <article className="process-card">
            <div className="process-number">02</div>
            <div className="process-icon">💭</div>

            <h3>Understand</h3>

            <p>
              Get supportive guidance to help make sense of the patterns
              you've described.
            </p>
          </article>

          <article className="process-card">
            <div className="process-number">03</div>
            <div className="process-icon">🤝</div>

            <h3>Respond</h3>

            <p>
              Find practical suggestions for starting a caring,
              respectful conversation.
            </p>
          </article>
        </div>
      </div>
    </section>
  )
}

export default ProcessSection