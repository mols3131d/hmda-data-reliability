import json

from project_pivot.hmda_data.eda.analysis import analyze_hmda_csv

evidence = analyze_hmda_csv(
    source_path="data/raw/hmda/year_2025.csv",
    memory_limit="2GB",
    threads=2,
    temp_directory=".tmp",
)

with open("docs/references/hmda_eda_reference.json", "w") as f:
    json.dump(evidence, f, indent=2, ensure_ascii=False)

print("EDA completed on actual source.")
