import json
from dataclasses import asdict
import numpy as np

from src.prototype import OpenReviewClient


def main():
    openreview_client = OpenReviewClient()

    papers = openreview_client.get_papers("ICLR", "2024")

    papers = list(filter(lambda paper: paper.avg_score > 0, papers))

    score_list = np.array([paper.avg_score for paper in target])

    print(f"total number of papers: {len(papers)}")
    for i in [0, 25, 33.33, 50, 66.67, 75, 90, 100]:
        print(f"{i}th percentile: {np.percentile(score_list, i)}")

    with open("assests/data.json", "w") as f:
        json.dump([asdict(p) for p in papers], f, indent=4)

if __name__ == "__main__":
    main()
