"""
Intelligent Data Dictionary Agent - Backend Prototype
Extracts schema metadata and provides basic conversational insights.
"""
import pandas as pd

# Step 1: Load Dataset
file_path = input("Enter excel file path: ")
df = pd.read_excel(file_path)

print("\n=== Schema Information ===")
print(df.dtypes)

print("\n=== Null Value Count ===")
print(df.isnull().sum())

print("\n=== Basic Statistics ===")
print(df.describe())

# Simple AI-like explanation
print("\n=== AI Generated Table Insight ===")
print(f"This dataset contains {df.shape[0]} rows and {df.shape[1]} columns.")
print("It includes the following columns:")
for col in df.columns:
    print(f"- {col}")

# Simple conversational interface
while True:
    question = input("\nAsk about your dataset (type 'exit' to quit): ")

    if question.lower() == "exit":
        break

    elif "column" in question.lower() or "schema" in question.lower():
        print("\nColumns in the dataset:")
        print(df.columns.tolist())

    elif "null" in question.lower() or "missing" in question.lower():
        print("\nNull value count:")
        print(df.isnull().sum())

    elif "row" in question.lower():
        print(f"\nThe dataset contains {df.shape[0]} rows.")

    elif "data type" in question.lower() or "type" in question.lower():
        print("\nData types of each column:")
        print(df.dtypes)

    elif "profit" in question.lower() and "profit" in df.columns.str.lower().tolist():
        print("\nBasic statistics for profit column:")
        print(df["Profit"].describe())
    else:
        print("\nThis prototype currently supports schema and basic data-related queries.")


