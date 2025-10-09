"""
交易參數驗證功能
驗證交易參數的合理性和合規性
使用 Python 3.12+ 語法
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ValidationResult(BaseModel):
    """驗證結果"""

    is_valid: bool
    validation_errors: list[str]
    warnings: list[str]
    recommendations: list[str]
    risk_score: float  # 0-100
    validated_parameters: dict[str, Any]
    timestamp: datetime


class TradingValidator:
    """
    交易參數驗證器
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("trading_validator")

        # 驗證規則配置
        self.validation_rules = {
            "min_trade_amount": 50000,  # 最小交易金額 (TWD)
            "max_position_ratio": 0.15,  # 最大單一部位比例
            "max_daily_trades": 10,  # 每日最大交易次數
            "min_lot_size": 1000,  # 台股最小交易單位
            "max_leverage": 1.0,  # 最大槓桿倍數
            "blacklist_symbols": ["9999", "0000"],  # 黑名單代碼
        }

    async def validate_trade_parameters(
        self,
        symbol: str,
        action: str,  # "buy" 或 "sell"
        quantity: int,
        price: float | None = None,
        portfolio_value: float = 1000000,
        current_positions: dict[str, Any] | None = None,
        daily_trade_count: int = 0,
    ) -> ValidationResult:
        """
        驗證交易參數

        Args:
            symbol: 股票代碼
            action: 交易動作
            quantity: 交易數量
            price: 交易價格 (None 表示市價)
            portfolio_value: 投資組合總值
            current_positions: 當前持倉
            daily_trade_count: 當日交易次數

        Returns:
            驗證結果
        """
        errors = []
        warnings = []
        recommendations = []
        risk_score = 0

        current_positions = current_positions or {}

        try:
            # 基本參數驗證
            basic_validation = self._validate_basic_parameters(symbol, action, quantity, price)
            errors.extend(basic_validation["errors"])
            warnings.extend(basic_validation["warnings"])
            risk_score += basic_validation["risk_score"]

            # 市場規則驗證
            market_validation = self._validate_market_rules(symbol, quantity)
            errors.extend(market_validation["errors"])
            warnings.extend(market_validation["warnings"])
            risk_score += market_validation["risk_score"]

            # 投資組合限制驗證
            portfolio_validation = self._validate_portfolio_limits(
                symbol, action, quantity, price, portfolio_value, current_positions
            )
            errors.extend(portfolio_validation["errors"])
            warnings.extend(portfolio_validation["warnings"])
            recommendations.extend(portfolio_validation["recommendations"])
            risk_score += portfolio_validation["risk_score"]

            # 交易頻率驗證
            frequency_validation = self._validate_trading_frequency(daily_trade_count)
            errors.extend(frequency_validation["errors"])
            warnings.extend(frequency_validation["warnings"])
            risk_score += frequency_validation["risk_score"]

            # 風險評估
            risk_assessment = self._assess_trade_risk(
                symbol, action, quantity, price, portfolio_value, current_positions
            )
            warnings.extend(risk_assessment["warnings"])
            recommendations.extend(risk_assessment["recommendations"])
            risk_score += risk_assessment["risk_score"]

            # 生成建議
            if not errors and not warnings:
                recommendations.append("交易參數通過所有驗證，可以執行")

            return ValidationResult(
                is_valid=len(errors) == 0,
                validation_errors=errors,
                warnings=warnings,
                recommendations=recommendations,
                risk_score=min(100, risk_score),
                validated_parameters={
                    "symbol": symbol,
                    "action": action,
                    "quantity": quantity,
                    "price": price,
                    "trade_value": (price or 0) * quantity,
                },
                timestamp=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Trade validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                validation_errors=[f"驗證過程發生錯誤: {e}"],
                warnings=[],
                recommendations=["請檢查交易參數並重新提交"],
                risk_score=100,
                validated_parameters={},
                timestamp=datetime.now(),
            )

    def _validate_basic_parameters(
        self, symbol: str, action: str, quantity: int, price: float | None
    ) -> dict[str, Any]:
        """驗證基本參數"""
        errors = []
        warnings = []
        risk_score = 0

        # 股票代碼驗證
        if not symbol or len(symbol) < 4:
            errors.append("股票代碼格式不正確")
            risk_score += 20

        if symbol in self.validation_rules["blacklist_symbols"]:
            errors.append(f"股票代碼 {symbol} 在交易黑名單中")
            risk_score += 50

        # 交易動作驗證
        if action not in ["buy", "sell"]:
            errors.append(f"不支援的交易動作: {action}")
            risk_score += 30

        # 數量驗證
        if quantity <= 0:
            errors.append("交易數量必須大於 0")
            risk_score += 30

        if quantity % self.validation_rules["min_lot_size"] != 0:
            errors.append(f"交易數量必須是 {self.validation_rules['min_lot_size']} 的倍數")
            risk_score += 15

        # 價格驗證
        if price is not None:
            if price <= 0:
                errors.append("交易價格必須大於 0")
                risk_score += 25

            if price > 1000:  # 台股價格通常不會超過 1000
                warnings.append("交易價格似乎異常高，請確認")
                risk_score += 10

        return {
            "errors": errors,
            "warnings": warnings,
            "risk_score": risk_score,
        }

    def _validate_market_rules(self, symbol: str, quantity: int) -> dict[str, Any]:
        """驗證市場規則"""
        errors = []
        warnings = []
        risk_score = 0

        # 檢查是否為有效的台股代碼
        if len(symbol) == 4 and symbol.isdigit():
            # 台股代碼格式正確
            pass
        elif len(symbol) >= 5:
            # ETF 或其他特殊標的
            if not any(c.isalpha() for c in symbol):
                warnings.append("非標準股票代碼格式，請確認標的正確性")
                risk_score += 5
        else:
            errors.append("股票代碼格式不符合台股規範")
            risk_score += 20

        # 交易單位檢查
        if quantity < self.validation_rules["min_lot_size"]:
            errors.append(f"交易數量不能少於 {self.validation_rules['min_lot_size']} 股")
            risk_score += 15

        # 大額交易警告
        if quantity > 100000:  # 超過 10 萬股
            warnings.append("大額交易，請確認流動性充足")
            risk_score += 10

        return {
            "errors": errors,
            "warnings": warnings,
            "risk_score": risk_score,
        }

    def _validate_portfolio_limits(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: float | None,
        portfolio_value: float,
        current_positions: dict[str, Any],
    ) -> dict[str, Any]:
        """驗證投資組合限制"""
        errors = []
        warnings = []
        recommendations = []
        risk_score = 0

        # 計算交易金額
        estimated_price = price or 100  # 如果沒有價格，使用估計值
        trade_value = quantity * estimated_price

        # 最小交易金額檢查
        if trade_value < self.validation_rules["min_trade_amount"]:
            errors.append(f"交易金額不能少於 NT${self.validation_rules['min_trade_amount']:,}")
            risk_score += 15

        if action == "buy":
            # 買入檢查
            position_ratio = trade_value / portfolio_value

            # 單一部位比例檢查
            if position_ratio > self.validation_rules["max_position_ratio"]:
                errors.append(
                    f"單一部位不能超過投資組合的 {self.validation_rules['max_position_ratio']:.1%}"
                )
                risk_score += 25

            # 檢查現有部位
            current_value = 0
            if symbol in current_positions:
                current_qty = current_positions[symbol].get("quantity", 0)
                current_price = current_positions[symbol].get("current_price", estimated_price)
                current_value = current_qty * current_price

            total_value = current_value + trade_value
            total_ratio = total_value / portfolio_value

            if total_ratio > self.validation_rules["max_position_ratio"]:
                errors.append(
                    f"加計現有部位後，{symbol} 總部位將超過 {self.validation_rules['max_position_ratio']:.1%} 限制"
                )
                risk_score += 20

            # 現金充足性檢查（簡化）
            if trade_value > portfolio_value * 0.5:
                warnings.append("交易金額較大，請確認現金充足")
                risk_score += 10

        elif action == "sell":
            # 賣出檢查
            if symbol not in current_positions:
                errors.append(f"投資組合中沒有 {symbol} 持倉，無法賣出")
                risk_score += 30
            else:
                current_qty = current_positions[symbol].get("quantity", 0)
                if quantity > current_qty:
                    errors.append(f"賣出數量 ({quantity:,}) 超過持有數量 ({current_qty:,})")
                    risk_score += 25

                # 部分賣出建議
                if quantity == current_qty:
                    recommendations.append("將清空 {symbol} 持倉")
                elif quantity / current_qty > 0.5:
                    warnings.append("賣出比例較高，請確認投資策略")
                    risk_score += 5

        return {
            "errors": errors,
            "warnings": warnings,
            "recommendations": recommendations,
            "risk_score": risk_score,
        }

    def _validate_trading_frequency(self, daily_trade_count: int) -> dict[str, Any]:
        """驗證交易頻率"""
        errors = []
        warnings = []
        risk_score = 0

        max_trades = self.validation_rules["max_daily_trades"]

        if daily_trade_count >= max_trades:
            errors.append(f"已達到每日最大交易次數限制 ({max_trades} 次)")
            risk_score += 20
        elif daily_trade_count >= max_trades * 0.8:
            warnings.append("接近每日交易次數上限，請謹慎操作")
            risk_score += 10

        return {
            "errors": errors,
            "warnings": warnings,
            "risk_score": risk_score,
        }

    def _assess_trade_risk(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: float | None,
        portfolio_value: float,
        current_positions: dict[str, Any],
    ) -> dict[str, Any]:
        """評估交易風險"""
        warnings = []
        recommendations = []
        risk_score = 0

        trade_value = quantity * (price or 100)
        position_ratio = trade_value / portfolio_value

        # 風險分級
        if position_ratio > 0.10:
            risk_score += 15
            warnings.append("大額交易，建議設定停損點")
            recommendations.append("考慮分批建倉以降低風險")

        if position_ratio > 0.05:
            risk_score += 10
            recommendations.append("建議密切關注標的基本面變化")

        # 集中度風險
        portfolio_count = len(current_positions)
        if portfolio_count < 5 and action == "buy":
            risk_score += 10
            warnings.append("投資組合集中度較高")
            recommendations.append("考慮增加投資標的以分散風險")

        # 動作特定風險
        if action == "buy":
            recommendations.append("建議設定停損價位")
            if price:
                stop_loss = price * 0.92  # 8% 停損
                recommendations.append(f"建議停損價位: NT${stop_loss:.2f}")

        elif action == "sell":
            if symbol in current_positions:
                purchase_price = current_positions[symbol].get("purchase_price", price)
                if purchase_price and price:
                    gain_loss = (price - purchase_price) / purchase_price
                    if gain_loss < -0.15:
                        warnings.append("虧損賣出，請確認投資策略")
                        risk_score += 5

        return {
            "warnings": warnings,
            "recommendations": recommendations,
            "risk_score": risk_score,
        }

    def get_validation_rules(self) -> dict[str, Any]:
        """獲取當前驗證規則"""
        return self.validation_rules.copy()

    def update_validation_rule(self, rule_name: str, value: Any) -> bool:
        """更新驗證規則"""
        if rule_name in self.validation_rules:
            self.validation_rules[rule_name] = value
            self.logger.info(f"Updated validation rule {rule_name} to {value}")
            return True
        return False

    async def validate_batch_trades(
        self,
        trades: list[dict[str, Any]],
        portfolio_value: float,
        current_positions: dict[str, Any] | None = None,
    ) -> list[ValidationResult]:
        """
        批量驗證交易

        Args:
            trades: 交易列表
            portfolio_value: 投資組合總值
            current_positions: 當前持倉

        Returns:
            驗證結果列表
        """
        results = []
        simulated_positions = (current_positions or {}).copy()
        daily_trade_count = 0

        for trade in trades:
            result = await self.validate_trade_parameters(
                symbol=trade["symbol"],
                action=trade["action"],
                quantity=trade["quantity"],
                price=trade.get("price"),
                portfolio_value=portfolio_value,
                current_positions=simulated_positions,
                daily_trade_count=daily_trade_count,
            )

            results.append(result)

            # 更新模擬持倉（如果驗證通過）
            if result.is_valid:
                daily_trade_count += 1
                symbol = trade["symbol"]
                action = trade["action"]
                quantity = trade["quantity"]

                if action == "buy":
                    if symbol in simulated_positions:
                        simulated_positions[symbol]["quantity"] += quantity
                    else:
                        simulated_positions[symbol] = {
                            "quantity": quantity,
                            "purchase_price": trade.get("price", 100),
                        }
                elif action == "sell" and symbol in simulated_positions:
                    simulated_positions[symbol]["quantity"] -= quantity
                    if simulated_positions[symbol]["quantity"] <= 0:
                        del simulated_positions[symbol]

        return results

    def as_tool(self) -> dict[str, Any]:
        """
        將 TradingValidator 轉換為可供 OpenAI Agent 使用的工具

        Returns:
            工具配置字典
        """
        return {
            "type": "function",
            "function": {
                "name": "validate_trade_parameters",
                "description": "驗證交易參數的合理性和合規性",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "股票代碼 (例如: 2330)",
                        },
                        "action": {
                            "type": "string",
                            "enum": ["buy", "sell"],
                            "description": "交易動作",
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "交易數量 (股數)",
                            "minimum": 1000,
                        },
                        "price": {
                            "type": "number",
                            "description": "交易價格 (可選，市價單時不需要)",
                        },
                        "portfolio_data": {
                            "type": "object",
                            "description": "投資組合數據 (用於驗證)",
                        },
                    },
                    "required": ["symbol", "action", "quantity"],
                },
            },
            "implementation": self.validate_trade_parameters,
        }
