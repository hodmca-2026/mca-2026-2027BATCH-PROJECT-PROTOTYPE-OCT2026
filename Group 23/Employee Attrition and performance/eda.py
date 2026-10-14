# notebooks/eda.py

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# ==========================================================
# LOAD
# ==========================================================

PROJECT_DIR = Path(__file__).resolve().parent

DATASET_PATH = (
    PROJECT_DIR
    / "data"
    / "employee_attrition_hr_2026.csv"
)

df = pd.read_csv(DATASET_PATH)


# ==========================================================
# BASIC INFORMATION
# ==========================================================

print("=" * 70)
print("DATASET OVERVIEW")
print("=" * 70)

print("\nShape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nData types:")
print(df.dtypes)

print("\nMissing values:")
print(df.isnull().sum())

print("\nDuplicate rows:")
print(df.duplicated().sum())


# ==========================================================
# STATISTICS
# ==========================================================

print("\nNumerical statistics:")
print(df.describe())


# ==========================================================
# ATTRITION DISTRIBUTION
# ==========================================================

plt.figure(figsize=(7, 5))

sns.countplot(
    data=df,
    x="attrition"
)

plt.title("Employee Attrition Distribution")
plt.xlabel("Attrition")
plt.ylabel("Number of Employees")

plt.tight_layout()
plt.show()


# ==========================================================
# PERFORMANCE DISTRIBUTION
# ==========================================================

plt.figure(figsize=(7, 5))

sns.countplot(
    data=df,
    x="performance_rating"
)

plt.title("Performance Rating Distribution")
plt.xlabel("Performance Rating")
plt.ylabel("Number of Employees")

plt.tight_layout()
plt.show()


# ==========================================================
# ATTRITION VS OVERTIME
# ==========================================================

plt.figure(figsize=(8, 5))

sns.boxplot(
    data=df,
    x="attrition",
    y="overtime_hours_per_week"
)

plt.title(
    "Attrition vs Overtime Hours"
)

plt.tight_layout()
plt.show()


# ==========================================================
# ATTRITION VS SATISFACTION
# ==========================================================

plt.figure(figsize=(8, 5))

sns.boxplot(
    data=df,
    x="attrition",
    y="engagement_score"
)

plt.title(
    "Attrition vs Engagement Score"
)

plt.tight_layout()
plt.show()


# ==========================================================
# ATTRITION BY DEPARTMENT
# ==========================================================

department_attrition = pd.crosstab(
    df["department"],
    df["attrition"],
    normalize="index"
) * 100

print("\nAttrition percentage by department:")
print(department_attrition)


department_attrition.plot(
    kind="bar",
    figsize=(10, 6)
)

plt.title(
    "Attrition Percentage by Department"
)

plt.xlabel("Department")
plt.ylabel("Percentage")

plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# ==========================================================
# PERFORMANCE VS ENGAGEMENT
# ==========================================================

plt.figure(figsize=(8, 5))

sns.boxplot(
    data=df,
    x="performance_rating",
    y="engagement_score"
)

plt.title(
    "Performance Rating vs Engagement"
)

plt.tight_layout()
plt.show()


# ==========================================================
# PERFORMANCE VS TRAINING
# ==========================================================

plt.figure(figsize=(8, 5))

sns.boxplot(
    data=df,
    x="performance_rating",
    y="training_hours"
)

plt.title(
    "Performance Rating vs Training Hours"
)

plt.tight_layout()
plt.show()


# ==========================================================
# CORRELATION HEATMAP
# ==========================================================

numeric_df = df.select_dtypes(
    include=["int64", "float64", "bool"]
)

plt.figure(figsize=(14, 10))

sns.heatmap(
    numeric_df.corr(),
    cmap="coolwarm",
    center=0
)

plt.title(
    "Numerical Feature Correlation"
)

plt.tight_layout()
plt.show()