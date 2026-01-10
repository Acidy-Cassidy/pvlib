

#!/usr/bin/env python3
import mypandas as pd

def main():
    print("Pandas version:", pd.__version__)
    # Create a DataFrame
    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie", "Diana"],
        "age": [25, 30, 35, 40],
        "score": [88.5, 92.0, 79.5, 85.0]
    })
    print("\nDataFrame:")
    print(df)

    # Basic selection and filtering
    print("\nPeople older than 30:")
    print(df[df["age"] > 30])

    # Add a new column
    df["passed"] = df["score"] >= 85
    print("\nWith 'passed' column:")
    print(df)

    # Grouping and aggregation
    avg_score = df["score"].mean()
    print("\nAverage score:", avg_score)

    # Sorting
    print("\nSorted by score (descending):")
    print(df.sort_values(by="score", ascending=False))

    # CSV round-trip test
    csv_file = "pandas_test.csv"
    df.to_csv(csv_file, index=False)
    df_loaded = pd.read_csv(csv_file)

    print("\nReloaded from CSV:")
    print(df_loaded)

    print("\n✅ Pandas basic test completed successfully")

if __name__ == "__main__":
    main()

