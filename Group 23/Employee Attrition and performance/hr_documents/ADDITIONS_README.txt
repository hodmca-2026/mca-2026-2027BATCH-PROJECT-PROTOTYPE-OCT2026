HR KNOWLEDGE CORPUS - EXPANSION NOTES

The archive contains the original 20 HR text documents plus 20 added sample documents (40 .txt documents total).

The added files are generic educational examples for a project knowledge-search corpus. They are not verified policies for a specific employer and should not be presented as legal, contractual, or organization-specific advice. Eligibility, deadlines, payments, and approvals are intentionally referred to the applicable organization policy, plan documents, and local requirements.

New topics by category:
Leave: parental leave, bereavement leave, attendance and absence reporting, unpaid leave requests.
Performance: performance improvement plans, goal setting, internal job transfers, employee recognition.
Benefits: wellbeing programs, dependent coverage, benefits enrollment changes, flexible work arrangements.
Training: onboarding, mandatory compliance training, certification support, training needs assessment.
Compensation: payroll discrepancy resolution, business expense reimbursement, incentive pay, payroll schedule and payslips.

After replacing the project's hr_documents folder with this expanded folder, rebuild the index using the project's existing script (from the project root):
    python build_inverted_index.py

Also check any hard-coded document counts or benchmark relevance judgments used by /api/ir-analysis. Rebuilds update the indexed corpus, but evaluation judgments may require separate maintenance.
