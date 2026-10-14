# ==========================================================
# prediction_service.py
#
# Unified Employee Attrition + Performance Prediction
# ==========================================================

import joblib
import numpy as np
import pandas as pd

from tensorflow import keras

from config import (
    ARTIFACT_DIR,
    MODEL_DIR,
    RESULT_DIR,
    ATTRITION_MODEL_PATH,
    PERFORMANCE_MODEL_PATH,
    ATTRITION_PREPROCESSOR_PATH,
    PERFORMANCE_PREPROCESSOR_PATH,
    THRESHOLD_PATH,
)
from logger import get_logger

logger = get_logger(__name__)


# ==========================================================
# LOAD MODELS
# ==========================================================

logger.info("Loading prediction models...")

attrition_model = keras.models.load_model(
    ATTRITION_MODEL_PATH
)

performance_model = keras.models.load_model(
    PERFORMANCE_MODEL_PATH
)

logger.info("Models loaded successfully.")


# ==========================================================
# LOAD PREPROCESSORS
# ==========================================================

logger.info("Loading preprocessors...")

attrition_preprocessor = joblib.load(
    ATTRITION_PREPROCESSOR_PATH
)

performance_preprocessor = joblib.load(
    PERFORMANCE_PREPROCESSOR_PATH
)

logger.info("Preprocessors loaded successfully.")


# ==========================================================
# LOAD ATTRITION THRESHOLD
# ==========================================================

DEFAULT_ATTRITION_THRESHOLD = 0.64

if THRESHOLD_PATH.exists():

    try:

        with open(
            THRESHOLD_PATH,
            "r"
        ) as file:

            ATTRITION_THRESHOLD = float(
                file.read().strip()
            )

    except (ValueError, OSError):

        ATTRITION_THRESHOLD = (
            DEFAULT_ATTRITION_THRESHOLD
        )

else:

    ATTRITION_THRESHOLD = (
        DEFAULT_ATTRITION_THRESHOLD
    )


# ==========================================================
# PERFORMANCE LABELS
# ==========================================================

PERFORMANCE_LABELS = {
    2: "Needs Improvement",
    3: "Average",
    4: "Good",
    5: "Excellent",
}


# ==========================================================
# REQUIRED RAW INPUT COLUMNS
# ==========================================================

REQUIRED_COLUMNS = [
    "age",
    "gender",
    "marital_status",
    "education_level",
    "department",
    "job_role",
    "job_level",
    "monthly_income",
    "stock_option_level",
    "salary_hike_pct",
    "years_at_company",
    "total_working_years",
    "years_since_promotion",
    "num_prior_companies",
    "work_mode",
    "commute_minutes",
    "overtime_hours_per_week",
    "business_travel_days_per_year",
    "training_hours",
    "manager_support_score",
    "burnout_score",
    "engagement_score",
    "work_life_balance_score",
    "performance_rating",
    "last_review_score",
    "uses_ai_tools_at_work",
    "perceived_ai_job_risk",
]


# ==========================================================
# VALIDATION
# ==========================================================

def validate_employee_data(employee_data):
    """
    Validate raw employee input.

    Parameters
    ----------
    employee_data : dict

    Returns
    -------
    dict
        Validated employee data.
    """

    if not isinstance(employee_data, dict):

        raise TypeError(
            "employee_data must be a dictionary."
        )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in employee_data
    ]

    if missing_columns:

        raise ValueError(
            "Missing required fields: "
            + ", ".join(missing_columns)
        )

    return employee_data


# ==========================================================
# PREPARE DATAFRAME
# ==========================================================

def prepare_dataframe(employee_data):
    """
    Convert raw employee dictionary to DataFrame.
    """

    employee_data = validate_employee_data(
        employee_data
    )

    # Create one-row DataFrame
    df = pd.DataFrame(
        [employee_data]
    )

    # Convert boolean field
    if isinstance(
        df.loc[0, "uses_ai_tools_at_work"],
        str
    ):

        value = str(
            df.loc[0, "uses_ai_tools_at_work"]
        ).strip().lower()

        if value in [
            "yes",
            "true",
            "1",
            "y"
        ]:

            df.loc[
                0,
                "uses_ai_tools_at_work"
            ] = 1

        elif value in [
            "no",
            "false",
            "0",
            "n"
        ]:

            df.loc[
                0,
                "uses_ai_tools_at_work"
            ] = 0

        else:

            raise ValueError(
                "uses_ai_tools_at_work must be "
                "Yes/No or True/False."
            )

    else:

        df[
            "uses_ai_tools_at_work"
        ] = df[
            "uses_ai_tools_at_work"
        ].astype(int)

    return df


# ==========================================================
# ATTRITION PREDICTION
# ==========================================================

def predict_attrition(employee_df):
    """
    Predict employee attrition probability.
    """

    # Transform raw employee data
    X_processed = (
        attrition_preprocessor
        .transform(employee_df)
    )

    X_processed = np.asarray(
        X_processed,
        dtype=np.float32
    )

    # Get probability
    probability = float(
        attrition_model
        .predict(
            X_processed,
            verbose=0
        )[0][0]
    )

    # Threshold selected during optimization
    prediction = int(
        probability >= ATTRITION_THRESHOLD
    )

    if prediction == 1:

        risk = "HIGH"

    else:

        # Add an intermediate risk level
        # for dashboard purposes.
        if probability >= 0.40:

            risk = "MEDIUM"

        else:

            risk = "LOW"

    return {
        "probability": probability,
        "percentage": round(
            probability * 100,
            2
        ),
        "prediction": prediction,
        "risk": risk,
        "threshold": ATTRITION_THRESHOLD,
    }


# ==========================================================
# PERFORMANCE PREDICTION
# ==========================================================

def predict_performance(employee_df):
    """
    Predict employee performance rating.
    """

    # Transform raw employee data
    X_processed = (
        performance_preprocessor
        .transform(employee_df)
    )

    X_processed = np.asarray(
        X_processed,
        dtype=np.float32
    )

    # Get probabilities for four classes
    probabilities = (
        performance_model
        .predict(
            X_processed,
            verbose=0
        )[0]
    )

    # Find highest probability class
    predicted_class = int(
        np.argmax(probabilities)
    )

    # Convert internal class:
    # 0 -> 2
    # 1 -> 3
    # 2 -> 4
    # 3 -> 5

    predicted_rating = (
        predicted_class + 2
    )

    confidence = float(
        probabilities[
            predicted_class
        ]
    )

    return {
        "rating": predicted_rating,
        "label": PERFORMANCE_LABELS[
            predicted_rating
        ],
        "confidence": confidence,
        "confidence_percentage": round(
            confidence * 100,
            2
        ),
        "probabilities": {
            str(class_id + 2): round(
                float(probability),
                4
            )
            for class_id, probability
            in enumerate(probabilities)
        },
    }


# ==========================================================
# HR RECOMMENDATIONS
# ==========================================================

def generate_recommendations(
    employee_df,
    attrition_result,
    performance_result
):
    """
    Generate rule-based HR recommendations.

    These are decision-support suggestions,
    not automatic HR decisions.

    The recommendation layer uses the employee's
    predicted attrition risk, predicted performance,
    and selected HR/workplace indicators.
    """

    recommendations = []


    # ======================================================
    # EXTRACT VALUES
    # ======================================================

    overtime = float(
        employee_df.loc[
            0,
            "overtime_hours_per_week"
        ]
    )

    engagement = float(
        employee_df.loc[
            0,
            "engagement_score"
        ]
    )

    burnout = float(
        employee_df.loc[
            0,
            "burnout_score"
        ]
    )

    manager_support = float(
        employee_df.loc[
            0,
            "manager_support_score"
        ]
    )

    years_since_promotion = float(
        employee_df.loc[
            0,
            "years_since_promotion"
        ]
    )

    work_life_balance = float(
        employee_df.loc[
            0,
            "work_life_balance_score"
        ]
    )

    training_hours = float(
        employee_df.loc[
            0,
            "training_hours"
        ]
    )

    perceived_ai_job_risk = float(
        employee_df.loc[
            0,
            "perceived_ai_job_risk"
        ]
    )


    # ======================================================
    # ATTRITION / RETENTION
    # ======================================================

    risk = str(
        attrition_result.get(
            "risk",
            "LOW"
        )
    ).upper()


    if risk == "HIGH":

        recommendations.append(
            "Schedule an employee-manager discussion "
            "to review retention, workload and employee support."
        )

        recommendations.append(
            "Review workload and overtime requirements "
            "and identify practical workload adjustments."
        )

    elif risk == "MEDIUM":

        recommendations.append(
            "Monitor employee engagement and workload "
            "through regular manager check-ins."
        )

    else:

        recommendations.append(
            "Continue routine employee engagement, "
            "development and retention monitoring."
        )


    # ======================================================
    # OVERTIME
    # ======================================================

    if overtime >= 15:

        recommendations.append(
            "Consider reducing excessive overtime "
            "and reviewing workload distribution."
        )


    # ======================================================
    # ENGAGEMENT
    # ======================================================

    if engagement <= 4:

        recommendations.append(
            "Conduct an employee engagement and "
            "satisfaction discussion."
        )

    elif engagement <= 6:

        recommendations.append(
            "Consider a structured engagement check-in "
            "to identify workplace concerns."
        )


    # ======================================================
    # BURNOUT
    # ======================================================

    if burnout >= 7:

        recommendations.append(
            "Review burnout indicators and consider "
            "workload or wellbeing support."
        )

    elif burnout >= 5:

        recommendations.append(
            "Monitor burnout indicators and review "
            "workload balance during regular check-ins."
        )


    # ======================================================
    # MANAGER SUPPORT
    # ======================================================

    if manager_support <= 4:

        recommendations.append(
            "Consider improving manager support "
            "and communication."
        )

    elif manager_support <= 6:

        recommendations.append(
            "Consider regular manager one-to-one "
            "conversations and feedback."
        )


    # ======================================================
    # PROMOTION / CAREER DEVELOPMENT
    # ======================================================

    if years_since_promotion >= 5:

        recommendations.append(
            "Review career progression and "
            "promotion opportunities."
        )

    elif years_since_promotion >= 4:

        recommendations.append(
            "Review career growth and development "
            "opportunities."
        )


    # ======================================================
    # WORK-LIFE BALANCE
    # ======================================================

    if work_life_balance <= 4:

        recommendations.append(
            "Review work-life balance and "
            "flexibility options."
        )

    elif work_life_balance <= 6:

        recommendations.append(
            "Monitor work-life balance and consider "
            "appropriate schedule or workload adjustments."
        )


    # ======================================================
    # TRAINING / DEVELOPMENT
    # ======================================================

    if training_hours < 15:

        recommendations.append(
            "Consider additional training and "
            "skill-development opportunities."
        )

    elif training_hours < 25:

        recommendations.append(
            "Consider targeted learning and "
            "skill-development activities."
        )


    # ======================================================
    # PERCEIVED AI JOB RISK
    # ======================================================

    if perceived_ai_job_risk >= 7:

        recommendations.append(
            "Consider AI upskilling, role-development "
            "and career communication to address perceived job risk."
        )


    # ======================================================
    # PERFORMANCE
    # ======================================================

    performance_rating = int(
        performance_result.get(
            "rating",
            3
        )
    )


    if performance_rating <= 2:

        recommendations.append(
            "Consider a structured performance "
            "improvement and support plan."
        )

    elif performance_rating == 3:

        recommendations.append(
            "Identify targeted development areas "
            "to improve performance."
        )

    elif performance_rating == 5:

        recommendations.append(
            "Consider recognition, career growth "
            "and development opportunities for this high performer."
        )


    # ======================================================
    # REMOVE DUPLICATES
    # ======================================================

    recommendations = list(
        dict.fromkeys(
            recommendations
        )
    )


    # ======================================================
    # SAFETY NET
    # ======================================================

    # Always provide at least one useful HR action.
    # This prevents the Prediction Lab from displaying
    # an empty recommendations section.

    if not recommendations:

        recommendations.append(
            "Continue routine performance reviews, "
            "employee development and engagement monitoring."
        )


    # Keep the UI focused on the most actionable items.
    return recommendations[:8]



# ==========================================================
# MAIN PREDICTION FUNCTION
# ==========================================================

def predict_employee(employee_data):
    """
    Complete employee analysis.

    Returns:
        Attrition prediction
        Performance prediction
        Recommendations
    """

    # Prepare raw input
    employee_df = prepare_dataframe(
        employee_data
    )

    # ----------------------------------------------
    # ATTRITION
    # ----------------------------------------------

    attrition_result = (
        predict_attrition(
            employee_df
        )
    )

    # ----------------------------------------------
    # PERFORMANCE
    # ----------------------------------------------

    performance_result = (
        predict_performance(
            employee_df
        )
    )

    # ----------------------------------------------
    # RECOMMENDATIONS
    # ----------------------------------------------

    recommendations = (
        generate_recommendations(
            employee_df,
            attrition_result,
            performance_result
        )
    )

    # ----------------------------------------------
    # FINAL RESPONSE
    # ----------------------------------------------

    return {
        "success": True,

        "attrition": attrition_result,

        "performance": performance_result,

        "recommendations": recommendations,
    }


# ==========================================================
# TEST FUNCTION
# ==========================================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("TESTING PREDICTION SERVICE")
    print("=" * 70)

    test_employee = {
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
        "years_since_promotion": 3,
        "num_prior_companies": 2,
        "work_mode": "Hybrid",
        "commute_minutes": 35,
        "overtime_hours_per_week": 12,
        "business_travel_days_per_year": 10,
        "training_hours": 25,
        "manager_support_score": 7,
        "burnout_score": 5,
        "engagement_score": 7,
        "work_life_balance_score": 7,
        "performance_rating": 4,
        "last_review_score": 8,
        "uses_ai_tools_at_work": True,
        "perceived_ai_job_risk": 4,
    }

    try:

        result = predict_employee(
            test_employee
        )

        print("\n" + "=" * 70)
        print("PREDICTION RESULT")
        print("=" * 70)

        print("\nATTRITION")
        print(
            f"Probability : "
            f"{result['attrition']['percentage']}%"
        )

        print(
            f"Risk        : "
            f"{result['attrition']['risk']}"
        )

        print(
            f"Threshold   : "
            f"{result['attrition']['threshold']}"
        )

        print("\nPERFORMANCE")

        print(
            f"Rating      : "
            f"{result['performance']['rating']}"
        )

        print(
            f"Label       : "
            f"{result['performance']['label']}"
        )

        print(
            f"Confidence  : "
            f"{result['performance']['confidence_percentage']}%"
        )

        print("\nProbabilities:")

        for rating, probability in (
            result[
                "performance"
            ][
                "probabilities"
            ].items()
        ):

            print(
                f"Rating {rating}: "
                f"{probability:.2%}"
            )

        print("\nRECOMMENDATIONS")

        if result["recommendations"]:

            for number, recommendation in enumerate(
                result["recommendations"],
                start=1
            ):

                print(
                    f"{number}. {recommendation}"
                )

        else:

            print(
                "No immediate recommendations."
            )

        print("\n" + "=" * 70)
        print("PREDICTION SERVICE WORKING")
        print("=" * 70)

    except Exception as error:

        print("\nPrediction failed:")
        print(error)

        raise