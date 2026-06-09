from datetime import date, timedelta
import unittest

from config.settings import Settings
from src.models import Paper
from src.ranking import (
    build_top_candidates,
    freshness_score,
    role_score,
    score_paper,
)


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

    def test_recent_paper_beats_ordinary_old_paper_for_technical_roles(
        self,
    ) -> None:
        recent_date = (date.today() - timedelta(days=60)).isoformat()
        old_date = (date.today() - timedelta(days=1800)).isoformat()
        recent = Paper(
            paper_id="recent",
            title="New robot policy system",
            abstract="A method with real robot experiments and deployment.",
            citation_count=10,
            influential_citation_count=1,
            publication_date=recent_date,
            source_pool="frontier",
        )
        ordinary_old = Paper(
            paper_id="old",
            title="Old robot policy system",
            abstract="A method with real robot experiments and deployment.",
            citation_count=100,
            influential_citation_count=5,
            publication_date=old_date,
            source_pool="high_impact",
        )
        keywords = ["Robot Learning"]

        self.assertGreater(
            role_score(recent, "deep_dive", keywords),
            role_score(ordinary_old, "deep_dive", keywords),
        )
        self.assertGreater(
            role_score(recent, "application", keywords),
            role_score(ordinary_old, "application", keywords),
        )

    def test_landmark_bonus_preserves_classic_paper_value(self) -> None:
        old_date = (date.today() - timedelta(days=1800)).isoformat()
        landmark = Paper(
            paper_id="landmark",
            title="Foundational robot learning policy",
            abstract="A foundational method and control architecture.",
            citation_count=3000,
            influential_citation_count=600,
            publication_date=old_date,
            source_pool="landmark",
        )
        ordinary = Paper(
            paper_id="ordinary",
            title=landmark.title,
            abstract=landmark.abstract,
            citation_count=100,
            influential_citation_count=5,
            publication_date=old_date,
            source_pool="high_impact",
        )

        self.assertGreater(
            role_score(landmark, "deep_dive", ["Robot Learning"]),
            role_score(ordinary, "deep_dive", ["Robot Learning"]),
        )
        self.assertEqual(freshness_score(landmark), 0.25)


if __name__ == "__main__":
    unittest.main()
