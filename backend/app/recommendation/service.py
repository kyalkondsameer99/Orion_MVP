"""Application service — symbol validation + engine invocation."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.symbols import InvalidSymbolError, normalize_symbol
from app.recommendation.config import RecommendationEngineConfig
from app.recommendation.engine import run_recommendation
from app.schemas.recommendation_engine import RecommendationRequest, RecommendationResponse


class RecommendationService:
    """Thin façade so routes stay small and tests can inject `RecommendationEngineConfig`."""

    def __init__(self, config: RecommendationEngineConfig | None = None) -> None:
        self._config = config or RecommendationEngineConfig()

    def analyze(self, body: RecommendationRequest) -> RecommendationResponse:
        try:
            sym = normalize_symbol(body.symbol)
        except InvalidSymbolError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
        normalized = body.model_copy(update={"symbol": sym})
        return run_recommendation(normalized, self._config)
