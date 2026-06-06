import unittest

from config.settings import Settings
from src.models import Paper
from src.ranking import build_top_candidates, score_paper


class RankingTests(unittest.TestCase):
    def test_recent_relevant_paper_has_positive_score(self) -> None:
        paper = Paper(
            paper_id="1",
            title="Embodied AI for Robotic Manipulation",
            abstract="A robot learning method for manipulation.",
            citation_count=20,
            publication_date="2026-01-01",
            source_pool="high_impact",
        )
        self.assertGreater(
            score_paper(paper, ["Embodied AI", "Robotic Manipulation"]),
            0,
        )

    def test_candidate_ids_are_unique(self) -> None:
        duplicate_a = Paper(
            paper_id="same",
            title="Embodied AI",
            abstract="robot learning",
            source_pool="high_impact",
        )
        duplicate_b = Paper(
            paper_id="same",
            title="Embodied AI",
            abstract="robot learning",
            source_pool="frontier",
        )
        results = build_top_candidates(
            {
                "high_impact": [duplicate_a],
                "frontier": [duplicate_b],
                "landmark": [],
            },
            ["Embodied AI"],
            Settings(),
        )
        self.assertEqual(
            len({paper.paper_id for paper in results}),
            len(results),
        )


if __name__ == "__main__":
    unittest.main()
