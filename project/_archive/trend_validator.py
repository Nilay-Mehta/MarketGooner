import re
import time
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class TrendReport(BaseModel):
    keyword: str
    trend_verdict: Literal["rising", "flat", "declining", "insufficient_data"] = "insufficient_data"
    slope_last_24mo: float = 0.0
    historical_points: List[int] = []

class TrendValidator:
    """
    Validates market demand trajectories for proposed startup wedges using Google Trends (pytrends).
    Protects against investing effort into declining search markets.
    """

    def __init__(self, hl: str = "en-US", tz: int = 360):
        self.hl = hl
        self.tz = tz

    def _extract_search_keyword(self, text: str) -> str:
        """Extracts a short, 1-3 word high-signal keyword suitable for Google Trends."""
        clean = re.sub(r'[^\w\s]', '', text.lower()).strip()
        words = [w for w in clean.split() if len(w) > 2 and w not in ["the", "and", "for", "with", "automated", "solution", "tool", "platform", "slash", "cost", "optimization"]]
        if len(words) >= 2:
            return " ".join(words[:2])
        elif words:
            return words[0]
        return clean.split()[0] if clean.split() else "saas"

    def validate_wedge(self, keywords: List[str], timeframe: str = "today 5-y") -> TrendReport:
        """
        Queries Google Trends for the given wedge keyword over the last 24-60 months.
        Calculates the 24-month slope and assigns a trend verdict.
        """
        if not keywords:
            return TrendReport(keyword="unknown", trend_verdict="insufficient_data", slope_last_24mo=0.0)

        raw_kw = keywords[0]
        search_kw = self._extract_search_keyword(raw_kw)
        
        try:
            from pytrends.request import TrendReq
            pytrends = TrendReq(hl=self.hl, tz=self.tz, timeout=(10, 25))
            pytrends.build_payload([search_kw], cat=0, timeframe=timeframe, geo="", gprop="")
            df = pytrends.interest_over_time()

            if df.empty or search_kw not in df.columns:
                return TrendReport(keyword=search_kw, trend_verdict="insufficient_data", slope_last_24mo=0.0)

            series = df[search_kw].tolist()
            # Take last 24 data points (or as many as available)
            recent_points = series[-24:] if len(series) >= 24 else series
            if len(recent_points) < 6:
                return TrendReport(keyword=search_kw, trend_verdict="insufficient_data", slope_last_24mo=0.0, historical_points=recent_points)

            # Simple linear regression slope calculation: sum((x - mean_x)*(y - mean_y)) / sum((x - mean_x)^2)
            n = len(recent_points)
            x_vals = list(range(n))
            mean_x = sum(x_vals) / n
            mean_y = sum(recent_points) / n
            numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_vals, recent_points))
            denominator = sum((x - mean_x) ** 2 for x in x_vals)
            
            slope = (numerator / denominator) if denominator != 0 else 0.0
            
            # Normalized slope per step relative to mean
            normalized_slope = (slope / max(mean_y, 1.0)) if mean_y > 0 else slope

            if normalized_slope > 0.04:
                verdict = "rising"
            elif normalized_slope < -0.04:
                verdict = "declining"
            else:
                verdict = "flat"

            return TrendReport(
                keyword=search_kw,
                trend_verdict=verdict,
                slope_last_24mo=round(float(normalized_slope), 4),
                historical_points=[int(p) for p in recent_points]
            )

        except Exception as e:
            # Gracefully handle 429, timeout, or network issues
            return TrendReport(keyword=search_kw, trend_verdict="insufficient_data", slope_last_24mo=0.0)
