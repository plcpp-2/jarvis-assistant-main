from dataclasses import dataclass, field
from typing import List, Dict, Any
import uuid
import numpy as np
import pandas as pd
from datetime import datetime


@dataclass
class Asset:
    """Represents a financial asset"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str = ""
    name: str = ""
    asset_type: str = ""
    current_price: float = 0.0
    quantity: float = 0.0
    purchase_date: datetime = field(default_factory=datetime.now)


@dataclass
class Portfolio:
    """Comprehensive Portfolio Management"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Default Portfolio"
    assets: List[Asset] = field(default_factory=list)
    risk_tolerance: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)


class PortfolioManager:
    def __init__(self):
        """
        Advanced Portfolio Management System
        - Asset allocation
        - Risk assessment
        - Performance tracking
        """
        self.portfolios: Dict[str, Portfolio] = {}

    def create_portfolio(self, name: str, risk_tolerance: float = 0.5) -> Portfolio:
        """Create a new investment portfolio"""
        portfolio = Portfolio(name=name, risk_tolerance=risk_tolerance)
        self.portfolios[portfolio.id] = portfolio
        return portfolio

    def add_asset(self, portfolio_id: str, asset: Asset):
        """Add an asset to a specific portfolio"""
        if portfolio_id not in self.portfolios:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        self.portfolios[portfolio_id].assets.append(asset)

    def calculate_portfolio_metrics(self, portfolio_id: str) -> Dict[str, Any]:
        """Calculate comprehensive portfolio metrics"""
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        # Calculate total value
        total_value = sum(asset.current_price * asset.quantity for asset in portfolio.assets)

        # Calculate asset allocation
        asset_allocation = {
            asset.asset_type: sum(
                asset.current_price * asset.quantity
                for asset in portfolio.assets
                if asset.asset_type == asset.asset_type
            )
            / total_value
            for asset in portfolio.assets
        }

        return {
            "total_value": total_value,
            "asset_allocation": asset_allocation,
            "risk_score": self._calculate_risk_score(portfolio),
        }

    def _calculate_risk_score(self, portfolio: Portfolio) -> float:
        """Calculate portfolio risk score"""
        # Simplified risk calculation
        volatility_factors = {"crypto": 1.5, "stocks": 1.0, "bonds": 0.5}

        risk_components = [volatility_factors.get(asset.asset_type, 1.0) for asset in portfolio.assets]

        return np.mean(risk_components) * (1 - portfolio.risk_tolerance)


def main():
    # Demonstration of portfolio management
    portfolio_manager = PortfolioManager()

    # Create portfolio
    portfolio = portfolio_manager.create_portfolio(name="Balanced Investment Portfolio", risk_tolerance=0.6)

    # Add assets
    portfolio_manager.add_asset(
        portfolio.id, Asset(symbol="BTC", name="Bitcoin", asset_type="crypto", current_price=50000, quantity=0.5)
    )

    portfolio_manager.add_asset(
        portfolio.id, Asset(symbol="AAPL", name="Apple Inc.", asset_type="stocks", current_price=150, quantity=10)
    )

    # Calculate portfolio metrics
    metrics = portfolio_manager.calculate_portfolio_metrics(portfolio.id)
    print(metrics)


if __name__ == "__main__":
    main()
