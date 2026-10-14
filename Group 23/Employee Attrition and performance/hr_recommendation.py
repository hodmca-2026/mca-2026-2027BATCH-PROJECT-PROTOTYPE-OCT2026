"""
Unit VI - Knowledge-Based / Content-Based HR Recommendation

Uses employee prediction signals to construct an HR information need, then
retrieves and fuses relevant HR resources using:
    - BM25
    - TF-IDF
    - Language Model

The final recommendation uses Reciprocal Rank Fusion (RRF) so that a document
supported by multiple retrieval models receives a stronger recommendation
signal than a document appearing in only one ranked list.
"""

from prediction_service import predict_employee
from ir_analysis import (
    compare_retrieval_methods,
    extract_information
)


# ----------------------------------------------------------
# CREATE HR INFORMATION NEED
# ----------------------------------------------------------

def create_hr_query(employee_data, prediction_result):
    """Generate a domain-specific HR retrieval query."""

    queries = []

    attrition = prediction_result.get(
        "attrition",
        {}
    )
    performance = prediction_result.get(
        "performance",
        {}
    )

    risk = str(
        attrition.get(
            "risk",
            attrition.get("risk_level", "LOW")
        )
    ).upper()

    if risk == "HIGH":
        queries.append(
            "employee retention wellness work life balance support workload"
        )
    elif risk == "MEDIUM":
        queries.append(
            "employee engagement workload support retention"
        )
    else:
        queries.append(
            "employee development performance engagement HR policy"
        )

    burnout = float(
        employee_data.get("burnout_score", 0)
    )
    if burnout >= 7:
        queries.append(
            "burnout employee assistance wellness workload"
        )

    engagement = float(
        employee_data.get("engagement_score", 10)
    )
    if engagement <= 4:
        queries.append(
            "employee engagement support communication"
        )

    manager_support = float(
        employee_data.get("manager_support_score", 10)
    )
    if manager_support <= 4:
        queries.append(
            "manager support communication feedback"
        )

    years_since_promotion = float(
        employee_data.get("years_since_promotion", 0)
    )
    if years_since_promotion >= 4:
        queries.append(
            "promotion career development performance progression"
        )

    overtime = float(
        employee_data.get("overtime_hours_per_week", 0)
    )
    if overtime >= 15:
        queries.append(
            "overtime workload compensation work life balance"
        )

    work_life = float(
        employee_data.get("work_life_balance_score", 10)
    )
    if work_life <= 4:
        queries.append(
            "work life balance leave flexibility"
        )

    training = float(
        employee_data.get("training_hours", 0)
    )
    if training < 15:
        queries.append(
            "training skill development learning"
        )

    rating = int(
        float(
            performance.get(
                "rating",
                employee_data.get("performance_rating", 3)
            )
        )
    )

    if rating <= 2:
        queries.append(
            "performance improvement training support"
        )
    elif rating == 3:
        queries.append(
            "employee development performance training"
        )
    elif rating >= 5:
        queries.append(
            "employee recognition reward career development"
        )

    query = " ".join(queries).strip()

    if not query:
        return "employee development HR policy"

    return query


# ----------------------------------------------------------
# KNOWLEDGE-BASED RECOMMENDATION
# ----------------------------------------------------------

def recommend_hr_resources(
    employee_data,
    prediction_result,
    top_n=5
):
    """
    Retrieve and fuse HR resources for an employee's information need.

    Returns both model-specific rankings and a fused knowledge-based
    recommendation list.
    """

    query = create_hr_query(
        employee_data,
        prediction_result
    )

    retrieval = compare_retrieval_methods(
        query,
        top_k=max(5, int(top_n))
    )

    comparison = retrieval["comparison"]

    recommendations = []

    for item in comparison[:max(1, int(top_n))]:
        document_id = item["document"]

        methods = []

        if item["bm25_rank"] is not None:
            methods.append({
                "method": "BM25",
                "rank": item["bm25_rank"],
                "score": item["bm25_score"]
            })

        if item["tfidf_rank"] is not None:
            methods.append({
                "method": "TF-IDF",
                "rank": item["tfidf_rank"],
                "score": item["tfidf_score"]
            })

        if item["language_model_rank"] is not None:
            methods.append({
                "method": "Language Model",
                "rank": item["language_model_rank"],
                "score": item["language_model_score"]
            })

        extracted = extract_information(
            document_id
        )

        recommendations.append({
            "document": document_id,
            "rrf_score": item["rrf_score"],
            "method_agreement": item["method_agreement"],
            "best_rank": item["best_rank"],
            "methods": methods,
            "information_extraction": extracted
        })

    return {
        "query": query,
        "recommendation_type": "Knowledge-Based HR Recommendation",
        "retrieval_models": [
            "BM25",
            "TF-IDF",
            "Language Model"
        ],
        "recommendations": recommendations,
        "ranking_fusion": "Reciprocal Rank Fusion (RRF)"
    }


# ----------------------------------------------------------
# TEST
# ----------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("KNOWLEDGE-BASED HR RECOMMENDATION")
    print("=" * 70)

    employee = {
        "age": 30,
        "gender": "Male",
        "marital_status": "Single",
        "education_level": "Bachelors",
        "department": "Engineering",
        "job_role": "Data Engineer",
        "job_level": 2,
        "monthly_income": 50000,
        "stock_option_level": 1,
        "salary_hike_pct": 12,
        "years_at_company": 3,
        "total_working_years": 6,
        "years_since_promotion": 4,
        "num_prior_companies": 2,
        "work_mode": "Hybrid",
        "commute_minutes": 35,
        "overtime_hours_per_week": 15,
        "business_travel_days_per_year": 10,
        "training_hours": 10,
        "manager_support_score": 4,
        "burnout_score": 8,
        "engagement_score": 4,
        "work_life_balance_score": 4,
        "performance_rating": 3,
        "last_review_score": 6,
        "uses_ai_tools_at_work": True,
        "perceived_ai_job_risk": 6,
    }

    prediction = predict_employee(employee)

    print("\nPrediction:")
    print(
        "Attrition Risk : "
        f"{prediction['attrition']['risk']}"
    )
    print(
        "Attrition      : "
        f"{prediction['attrition']['percentage']}%"
    )
    print(
        "Performance     : "
        f"{prediction['performance']['rating']}"
    )

    result = recommend_hr_resources(
        employee,
        prediction,
        top_n=5
    )

    print("\nGenerated HR information need:")
    print(result["query"])

    print("\nRecommended HR resources:")

    for rank, item in enumerate(
        result["recommendations"],
        start=1
    ):
        print(
            f"\n{rank}. {item['document']}"
        )
        print(
            f"   RRF Score       : {item['rrf_score']}"
        )
        print(
            f"   Method Agreement: {item['method_agreement']}/3"
        )
        print(
            "   Retrieved by    : "
            + ", ".join(
                method["method"]
                for method in item["methods"]
            )
        )
