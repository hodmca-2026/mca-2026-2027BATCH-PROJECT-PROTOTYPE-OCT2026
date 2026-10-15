function AboutSection() {
  return (
    <section className="about-section" id="about">
      <div className="container about-grid">
        <div>
          <span className="eyebrow">A calmer way to check in</span>

          <h2>
            You don't have to be an expert to show that you care.
          </h2>
        </div>

        <div className="about-copy">
          <p>
            When someone's behaviour changes, it can be difficult to know
            what to say or whether you should say anything at all.
          </p>

          <p>
            ByYourSide gives you a simple place to pause, reflect on what
            you've noticed, and consider a supportive next step.
          </p>

          <div className="info-box">
            <span className="info-icon">i</span>

            <p>
              ByYourSide is a mental health awareness and support guidance
              tool. It does not provide medical diagnoses or predict what
              someone will do.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

export default AboutSection