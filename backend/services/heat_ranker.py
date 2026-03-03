"""
Heat Score Algorithm (0-100)

Composite scoring:
- Search volume score (25%)  ← real data from DataForSEO when available
- Google Trends score (25%)
- Autocomplete rank position (15%)
- Source diversity (10%)
- Rising trend bonus (10%)
- Competition inverse score (15%)
"""
import math


def calculate_heat_score(
    trends_score: float = 0,
    autocomplete_rank: int | None = None,
    source_count: int = 1,
    is_rising: bool = False,
    competition: float | None = None,
    search_volume: int | None = None,
) -> float:
    """Calculate composite heat score (0-100)."""

    # 1. Search volume component (0-25)
    # Uses log scale: 10→5pts, 100→10pts, 1000→15pts, 10000→20pts, 100000+→25pts
    if search_volume is not None and search_volume > 0:
        vol_component = min(math.log10(search_volume) / 5 * 25, 25)
    else:
        vol_component = 0  # no data yet

    # 2. Trends component (0-25)
    # trends_score from pytrends is 0-100
    trends_component = (min(trends_score, 100) / 100) * 25

    # 3. Autocomplete rank component (0-15)
    # Lower rank = better. Rank 1 = 15pts, rank 10 = 8pts, rank 20+ = 3pts
    if autocomplete_rank is not None and autocomplete_rank > 0:
        if autocomplete_rank <= 3:
            ac_component = 15
        elif autocomplete_rank <= 10:
            ac_component = 15 - (autocomplete_rank - 1) * 1.0
        else:
            ac_component = max(3, 8 - (autocomplete_rank - 10) * 0.5)
    else:
        ac_component = 4  # no autocomplete data → baseline

    # 4. Source diversity component (0-10)
    source_component = min(source_count, 4) / 4 * 10

    # 5. Rising trend bonus (0-10)
    rising_component = 10 if is_rising else 0

    # 6. Competition inverse (0-15)
    # Lower competition = higher opportunity score
    if competition is not None:
        comp_component = (1 - min(competition, 1)) * 15
    else:
        comp_component = 7.5  # unknown → mid score

    total = vol_component + trends_component + ac_component + source_component + rising_component + comp_component
    return round(min(total, 100), 1)
