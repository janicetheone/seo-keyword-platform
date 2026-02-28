"""
Heat Score Algorithm (0-100)

Composite scoring:
- Google Trends score (35%)
- Autocomplete rank position (20%)
- Source diversity (15%)
- Rising trend bonus (15%)
- Competition inverse score (15%)
"""


def calculate_heat_score(
    trends_score: float = 0,
    autocomplete_rank: int | None = None,
    source_count: int = 1,
    is_rising: bool = False,
    competition: float | None = None,
) -> float:
    """Calculate composite heat score (0-100)."""

    # 1. Trends component (0-35)
    # trends_score from pytrends is 0-100
    trends_component = (min(trends_score, 100) / 100) * 35

    # 2. Autocomplete rank component (0-20)
    # Lower rank = better. Rank 1 = 20 points, rank 10 = 10 points, rank 20+ = 5 points
    if autocomplete_rank is not None and autocomplete_rank > 0:
        if autocomplete_rank <= 3:
            ac_component = 20
        elif autocomplete_rank <= 10:
            ac_component = 20 - (autocomplete_rank - 1) * 1.2
        else:
            ac_component = max(5, 10 - (autocomplete_rank - 10) * 0.5)
    else:
        ac_component = 5  # no autocomplete data → baseline

    # 3. Source diversity component (0-15)
    # Found by more sources = more validated
    source_component = min(source_count, 4) / 4 * 15

    # 4. Rising trend bonus (0-15)
    rising_component = 15 if is_rising else 0

    # 5. Competition inverse (0-15)
    # Lower competition = higher opportunity score
    if competition is not None:
        comp_component = (1 - min(competition, 1)) * 15
    else:
        comp_component = 7.5  # unknown → mid score

    total = trends_component + ac_component + source_component + rising_component + comp_component
    return round(min(total, 100), 1)
