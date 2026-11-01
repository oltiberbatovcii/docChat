"""Print saved eval runs side by side. Usage: uv run python -m evals.compare_results <labels...>"""

import argparse
import json

from evals.run_evals import RESULTS_DIR

CONFIG_FIELDS = ["prompt", "chunk_size", "top_k"]
SUMMARY_FIELDS = [
    "refusal_accuracy",
    "false_refusal_rate",
    "answer_correctness_1_to_5",
    "citation_accuracy",
    "hit_rate_at_1",
    "mrr",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("labels", nargs="+")
    args = parser.parse_args()

    headers = ["label", *CONFIG_FIELDS, *SUMMARY_FIELDS]
    rows = [headers]
    for label in args.labels:
        paths = sorted(RESULTS_DIR.glob(f"*_{label}.json"))
        if not paths:
            parser.error(f"no results for label: {label}")
        run = json.loads(paths[-1].read_text(encoding="utf-8"))  # newest run with that label
        config, summary = run["config"], run["summary"]
        rows.append(
            [
                label,
                *[config[field] for field in CONFIG_FIELDS],
                *[summary[field] for field in SUMMARY_FIELDS],
            ]
        )

    # Transposed so the many metrics fit: one line per field, one column per run
    for column in zip(*rows, strict=True):
        print(f"{column[0]:<28}" + "".join(f"{value!s:>14}" for value in column[1:]))


if __name__ == "__main__":
    main()
