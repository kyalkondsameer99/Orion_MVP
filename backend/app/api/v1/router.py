"""
Aggregate sub-routers for `/api/v1/*`.

Add new modules as you grow (e.g. `from app.api.v1 import paper`):
    api_router.include_router(paper.router, prefix="/paper", tags=["paper"])
"""

from fastapi import APIRouter

from app.api.v1 import broker, market_data, news, orders, positions, recommendation, watchlist

api_router = APIRouter()

api_router.include_router(watchlist.router, prefix="/watchlist", tags=["Watchlist"])
api_router.include_router(market_data.router, prefix="/market-data", tags=["Market data"])
api_router.include_router(news.router, prefix="/news", tags=["News"])
api_router.include_router(recommendation.router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(positions.router, prefix="/positions", tags=["Positions"])
api_router.include_router(broker.router, prefix="/broker", tags=["Broker"])
