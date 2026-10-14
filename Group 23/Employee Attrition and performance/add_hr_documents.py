from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
HR_DIR = PROJECT_DIR / "hr_documents"


documents = {

    # ======================================================
    # LEAVE
    # ======================================================

    "leave/sick_leave.txt": """
Sick Leave Policy

Employees may take sick leave when they are unable to work due to illness.

Employees should inform their manager as soon as possible when taking sick leave.

Medical documentation may be required according to organizational policy.

Employees should submit sick leave requests through the HR system.

Managers should handle sick leave requests consistently and confidentially.
""",

    "leave/annual_leave.txt": """
Annual Leave Policy

Employees are entitled to annual leave according to their employment terms.

Annual leave should normally be requested in advance through the HR portal.

Managers review leave requests based on staffing requirements and organizational policy.

Unused annual leave may be carried forward according to company rules.

Employees should coordinate planned leave with their team and manager.
""",

    "leave/emergency_leave.txt": """
Emergency Leave Policy

Emergency leave may be granted when an employee faces an unexpected personal or family emergency.

Employees should notify their manager as soon as reasonably possible.

The employee should submit the required leave request after the emergency situation is addressed.

HR may request supporting documentation when required by policy.

Emergency leave is reviewed according to organizational rules.
""",

    # ======================================================
    # PERFORMANCE
    # ======================================================

    "performance/appraisal_policy.txt": """
Employee Appraisal Policy

Employee appraisals are conducted periodically to evaluate performance and development.

Appraisals consider achievement of objectives, quality of work, teamwork, communication, and professional behavior.

Managers should provide constructive feedback during appraisal discussions.

Employees may discuss development goals with their managers.

Appraisal results may be considered for career development and recognition.
""",

    "performance/performance_review.txt": """
Performance Review Guidelines

Performance reviews should evaluate an employee's progress against agreed objectives.

Managers should consider productivity, work quality, engagement, teamwork, and communication.

Employees should receive clear feedback about strengths and areas for improvement.

Performance reviews should be based on documented work and objective evidence.

Employees may discuss performance concerns and development plans with their managers.
""",

    "performance/promotion_guidelines.txt": """
Promotion Guidelines

Employee promotions are based on performance, skills, experience, role requirements, and organizational needs.

Consistent achievement of performance objectives may support promotion consideration.

Employees may require additional skills or training before moving to a higher role.

Managers should discuss career development opportunities with employees.

Promotion decisions should follow organizational policies and approval procedures.
""",

    # ======================================================
    # BENEFITS
    # ======================================================

    "benefits/health_insurance.txt": """
Health Insurance Policy

Eligible employees may receive health insurance benefits according to organizational policy.

Health insurance may cover specified medical services, hospitalization, and other approved treatments.

Employees should review the insurance plan details to understand eligibility and coverage.

HR provides information about enrollment and changes to health insurance benefits.

Employees should contact HR for questions about insurance coverage.
""",

    "benefits/retirement_benefits.txt": """
Retirement Benefits Policy

Eligible employees may participate in retirement benefit programs provided by the organization.

Retirement contributions and eligibility depend on employment terms and organizational rules.

Employees can contact HR for information about retirement plans and contribution options.

Changes to retirement benefits are communicated through official HR channels.

Employees should review their retirement benefits periodically.
""",

    "benefits/employee_assistance.txt": """
Employee Assistance Program

The Employee Assistance Program provides support for employees experiencing personal or workplace challenges.

Support may include confidential counseling, wellbeing assistance, and guidance resources.

Employees may contact the appropriate assistance service directly according to organizational procedures.

The program is intended to support employee wellbeing and work-life balance.

Employees can contact HR for information about available assistance services.
""",

    # ======================================================
    # TRAINING
    # ======================================================

    "training/technical_training.txt": """
Technical Training Policy

Employees may participate in technical training programs to improve job-related skills.

Technical training may include programming, software tools, data analysis, cybersecurity, and technical certifications.

Managers may recommend training based on role requirements and performance development needs.

Employees may request technical training when they identify a skill gap.

Training participation should be recorded in the organization's training system.
""",

    "training/leadership_training.txt": """
Leadership Training Policy

Leadership training is designed to help employees develop management and leadership skills.

Topics may include communication, delegation, conflict management, decision making, and team development.

Employees preparing for leadership roles may be recommended for leadership development programs.

Managers should support employees participating in leadership training.

Leadership development may be considered during career planning and performance discussions.
""",

    "training/skill_development.txt": """
Skill Development Policy

Employees are encouraged to participate in skill development programs.

Skill development may include technical knowledge, communication, teamwork, problem solving, and professional skills.

Managers should identify development opportunities during performance discussions.

Employees may request training when additional skills are required for their current or future roles.

Training plans should align with employee development goals and organizational requirements.
""",

    # ======================================================
    # COMPENSATION
    # ======================================================

    "compensation/salary_policy.txt": """
Salary Policy

Employee salaries are determined based on job role, job level, skills, experience, market conditions, and organizational policies.

Salary reviews may occur periodically according to company procedures.

Employees should discuss salary-related questions with HR or their manager.

Salary changes require appropriate organizational approval.

Compensation information should be handled confidentially.
""",

    "compensation/bonus_policy.txt": """
Employee Bonus Policy

Employees may be eligible for bonuses based on organizational performance and individual performance.

Bonus eligibility and amounts depend on the applicable compensation plan.

Performance results, achievement of objectives, and business outcomes may be considered.

Bonus payments are subject to organizational approval and applicable policies.

Employees should contact HR for questions about bonus eligibility.
""",

    "compensation/compensation_policy.txt": """
Compensation Policy

The organization's compensation program includes salary, overtime compensation, bonuses, and other applicable rewards.

Compensation decisions consider job responsibilities, employee performance, experience, and organizational policies.

Employees should receive accurate information about compensation and payment procedures.

HR manages compensation policies and communicates approved changes.

Employees can contact HR for questions regarding compensation and benefits.
""",
}


def create_documents():

    created = 0

    for relative_path, content in documents.items():

        file_path = HR_DIR / relative_path

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            file_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                content.strip() + "\n"
            )

        print(f"Created: {file_path}")

        created += 1

    print("\n" + "=" * 70)
    print(f"Created {created} new HR documents.")
    print("=" * 70)


if __name__ == "__main__":
    create_documents()