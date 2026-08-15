"""
Yahoo Finance MCP Action Collection

This module provides Yahoo Finance data access through the ActionCollection framework.
It supports stock quotes, historical data, company information, financial statements,
news search, and market summaries with LLM-optimized output formatting.

Key features:
- Real-time stock quotes and market data
- Historical price data with configurable intervals
- Company information and financial statements
- Financial news search
- Market indices summaries
- LLM-friendly data formatting
- Comprehensive error handling

Main functions:
- mcp_get_stock_quote: Get current stock quote information
- mcp_get_historical_data: Retrieve historical OHLCV data
- mcp_get_company_info: Fetch company details and business information
- mcp_get_financial_statements: Access income statements, balance sheets, cash flow
"""

import os
import time
import traceback
from datetime import datetime
from typing import Any

import yfinance as yf
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

from aworld.logs.util import Color
from examples.gaia.mcp_collections.base import ActionArguments, ActionCollection, ActionResponse


class YFinanceMetadata(BaseModel):
    """Metadata for Yahoo Finance operation results."""

    symbol: str
    operation: str
    execution_time: float | None = None
    data_points: int | None = None
    error_type: str | None = None
    timestamp: str | None = None


class YahooFinanceActionCollection(ActionCollection):
    """Yahoo Finance MCP service for financial data access.

    Provides comprehensive financial data capabilities including:
    - Real-time stock quotes and market data
    - Historical price data with flexible time ranges
    - Company information and business details
    - Financial statements (income, balance sheet, cash flow)
    - Financial news search and aggregation
    - Market indices summaries and overviews
    - LLM-optimized data formatting
    - Error handling and validation
    """

    def _format_financial_data(self, data: Any, data_type: str) -> str:
        """Format financial data for LLM consumption.

        Args:
            data: Raw financial data
            data_type: Type of data for context

        Returns:
            LLM-friendly formatted string
        """
        if isinstance(data, dict):
            if data_type == "quote":
                return self._format_quote_data(data)
            elif data_type == "company":
                return self._format_company_data(data)
        elif isinstance(data, list):
            if data_type == "historical":
                return self._format_historical_data(data)
            elif data_type == "market_summary":
                return self._format_market_summary_data(data)
            elif data_type == "news":
                return self._format_news_list_data(data)

        return str(data)

    def _format_quote_data(self, quote: dict[str, Any]) -> str:
        """Format stock quote data for LLM."""
        lines = [f"# Stock Quote: {quote.get('symbol', 'N/A')}"]

        if quote.get("companyName"):
            lines.append(f"**Company:** {quote['companyName']}")

        if quote.get("currentPrice"):
            lines.append(f"**Current Price:** ${quote['currentPrice']:.2f} {quote.get('currency', '')}")

        if quote.get("previousClose"):
            change = quote.get("currentPrice", 0) - quote.get("previousClose", 0)
            change_pct = (change / quote["previousClose"]) * 100 if quote.get("previousClose") else 0
            direction = "📈" if change >= 0 else "📉"
            lines.append(f"**Change:** {direction} ${change:.2f} ({change_pct:.2f}%)")

        if quote.get("dayHigh") and quote.get("dayLow"):
            lines.append(f"**Day Range:** ${quote['dayLow']:.2f} - ${quote['dayHigh']:.2f}")

        if quote.get("volume"):
            lines.append(f"**Volume:** {quote['volume']:,}")

        if quote.get("marketCap"):
            lines.append(f"**Market Cap:** ${quote['marketCap']:,}")

        return "\n".join(lines)

    def _format_company_data(self, company: dict[str, Any]) -> str:
        """Format company information for LLM."""
        lines = [f"# Company Information: {company.get('symbol', 'N/A')}"]

        if company.get("longName"):
            lines.append(f"**Company Name:** {company['longName']}")

        if company.get("sector"):
            lines.append(f"**Sector:** {company['sector']}")

        if company.get("industry"):
            lines.append(f"**Industry:** {company['industry']}")

        if company.get("fullTimeEmployees"):
            lines.append(f"**Employees:** {company['fullTimeEmployees']:,}")

        if company.get("city") and company.get("country"):
            location = f"{company['city']}, {company['country']}"
            if company.get("state"):
                location = f"{company['city']}, {company['state']}, {company['country']}"
            lines.append(f"**Location:** {location}")

        if company.get("website"):
            lines.append(f"**Website:** {company['website']}")

        if company.get("longBusinessSummary"):
            summary = (
                company["longBusinessSummary"][:500] + "..."
                if len(company["longBusinessSummary"]) > 500
                else company["longBusinessSummary"]
            )
            lines.extend(["\n**Business Summary:**", summary])

        return "\n".join(lines)

    def _format_historical_data(self, data: list[dict[str, Any]]) -> str:
        """Format historical data for LLM."""
        if not data:
            return "No historical data available."

        lines = [f"# Historical Data ({len(data)} records)"]

        # Show first few and last few records
        preview_count = min(3, len(data))

        lines.append("\n**Recent Data:**")
        for record in data[-preview_count:]:
            date = record.get("Date", record.get("Datetime", "N/A"))
            close = record.get("Close", 0)
            volume = record.get("Volume", 0)
            lines.append(f"- {date}: Close ${close:.2f}, Volume {volume:,}")

        if len(data) > preview_count * 2:
            lines.append(f"\n... {len(data) - preview_count * 2} more records ...")

        if len(data) > preview_count:
            lines.append("\n**Earliest Data:**")
            for record in data[:preview_count]:
                date = record.get("Date", record.get("Datetime", "N/A"))
                close = record.get("Close", 0)
                volume = record.get("Volume", 0)
                lines.append(f"- {date}: Close ${close:.2f}, Volume {volume:,}")

        return "\n".join(lines)

    def _format_news_list_data(self, news_list: list[dict[str, Any]]) -> str:
        """Format news list for LLM."""
        if not news_list:
            return "No news articles found."

        lines = [f"# Financial News ({len(news_list)} articles)"]

        for i, article in enumerate(news_list, 1):
            lines.append(f"\n## {i}. {article.get('title', 'No Title')}")
            if article.get("publisher"):
                lines.append(f"**Publisher:** {article['publisher']}")
            if article.get("providerPublishTime"):
                lines.append(f"**Published:** {article['providerPublishTime']}")
            if article.get("link"):
                lines.append(f"**Link:** {article['link']}")

        return "\n".join(lines)

    def _format_market_summary_data(self, summaries: list[dict[str, Any]]) -> str:
        """Format market summary for LLM."""
        if not summaries:
            return "No market data available."

        lines = ["# Market Summary"]

        for summary in summaries:
            symbol = summary.get("symbol", "N/A")
            name = summary.get("name", symbol)
            price = summary.get("currentPrice", 0)
            change = summary.get("change", 0)
            change_pct = summary.get("percentChange", 0)

            direction = "📈" if change >= 0 else "📉"
            lines.append(f"\n**{name} ({symbol})**")
            lines.append(f"Price: ${price:.2f} {direction} {change:+.2f} ({change_pct:+.2f}%)")

        return "\n".join(lines)

    async def mcp_get_stock_quote(
        self,
        symbol: str = Field(description="Stock ticker symbol (e.g., AAPL, MSFT)"),
    ) -> ActionResponse:
        """Get current stock quote information.

        Fetches real-time stock quote data including current price, daily changes,
        volume, market cap, and other key metrics for the specified ticker symbol.

        Args:
            symbol: The stock ticker symbol to fetch quote for

        Returns:
            ActionResponse with formatted quote data and metadata
        """
        # Handle FieldInfo objects
        if isinstance(symbol, FieldInfo):
            symbol = symbol.default

        try:
            start_time = time.time()
            self._color_log(f"📊 Fetching stock quote for: {symbol}", Color.cyan)

            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or (info.get("regularMarketPrice") is None and info.get("currentPrice") is None):
                # Try to get basic history to validate symbol
                hist = ticker.history(period="1d")
                if hist.empty:
                    raise ValueError(f"No data found for symbol: {symbol}. It might be invalid or delisted.")
                raise ValueError(f"Could not retrieve detailed quote for symbol: {symbol}. Limited data available.")

            # Extract key quote information
            quote_data = {
                "symbol": symbol.upper(),
                "companyName": info.get("shortName", info.get("longName")),
                "currentPrice": info.get("regularMarketPrice", info.get("currentPrice")),
                "previousClose": info.get("previousClose"),
                "open": info.get("regularMarketOpen", info.get("open")),
                "dayHigh": info.get("regularMarketDayHigh", info.get("dayHigh")),
                "dayLow": info.get("regularMarketDayLow", info.get("dayLow")),
                "volume": info.get("regularMarketVolume", info.get("volume")),
                "averageVolume": info.get("averageVolume"),
                "marketCap": info.get("marketCap"),
                "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
                "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
                "currency": info.get("currency"),
                "exchange": info.get("exchange"),
            }

            # Filter out None values
            quote_data = {k: v for k, v in quote_data.items() if v is not None}

            execution_time = time.time() - start_time
            formatted_message = self._format_financial_data(quote_data, "quote")

            metadata = YFinanceMetadata(
                symbol=symbol.upper(),
                operation="get_stock_quote",
                execution_time=execution_time,
                data_points=len(quote_data),
                yfinance_available=True,
                timestamp=datetime.now().isoformat(),
            )

            self._color_log("✅ Stock quote retrieved successfully", Color.green)

            return ActionResponse(success=True, message=formatted_message, metadata=metadata.model_dump())

        except Exception as e:
            error_msg = f"Failed to fetch stock quote for {symbol}: {str(e)}"
            self.logger.error(f"Stock quote error: {traceback.format_exc()}")

            metadata = YFinanceMetadata(
                symbol=symbol.upper(),
                operation="get_stock_quote",
                error_type=type(e).__name__,
                timestamp=datetime.now().isoformat(),
            )

            return ActionResponse(success=False, message=error_msg, metadata=metadata.model_dump())

    async def mcp_get_historical_data(
        self,
        symbol: str = Field(description="Stock ticker symbol (e.g., AAPL, MSFT)"),
        start: str = Field(description="Start date (YYYY-MM-DD)"),
        end: str = Field(description="End date (YYYY-MM-DD)"),
        interval: str = Field(default="1d", description="Data interval (1d, 1wk, 1mo, etc.)"),
        max_rows_preview: int = Field(default=10, description="Max rows for preview (0 for all data)"),
    ) -> ActionResponse:
        """Retrieve historical stock data.

        Fetches historical OHLCV (Open, High, Low, Close, Volume) data for the
        specified ticker symbol within the given date range and interval.

        Args:
            symbol: Stock ticker symbol
            start: Start date in YYYY-MM-DD format
            end: End date in YYYY-MM-DD format
            interval: Data interval (1d, 1wk, 1mo, etc.)
            max_rows_preview: Maximum rows to show in preview

        Returns:
            ActionResponse with historical data and metadata
        """
        # Handle FieldInfo objects
        if isinstance(symbol, FieldInfo):
            symbol = symbol.default
        if isinstance(start, FieldInfo):
            start = start.default
        if isinstance(end, FieldInfo):
            end = end.default
        if isinstance(interval, FieldInfo):
            interval = interval.default
        if isinstance(max_rows_preview, FieldInfo):
            max_rows_preview = max_rows_preview.default

        try:
            start_time = time.time()
            self._color_log(f"📈 Fetching historical data for: {symbol} ({start} to {end})", Color.cyan)

            ticker = yf.Ticker(symbol)
            hist_df = ticker.history(start=start, end=end, interval=interval)

            if hist_df.empty:
                raise ValueError(
                    f"No historical data found for {symbol} with start={start}, end={end}, interval={interval}"
                )

            # Convert DataFrame to list of dictionaries
            hist_df.reset_index(inplace=True)

            # Ensure date columns are strings for JSON serialization
            if "Date" in hist_df.columns:
                hist_df["Date"] = hist_df["Date"].astype(str)
            if "Datetime" in hist_df.columns:
                hist_df["Datetime"] = hist_df["Datetime"].astype(str)

            # Clean column names
            hist_df.columns = hist_df.columns.str.replace(" ", "")

            historical_data = hist_df.to_dict(orient="records")
            execution_time = time.time() - start_time

            # Format message based on data size
            if max_rows_preview > 0 and len(historical_data) > max_rows_preview:
                preview_count = max_rows_preview // 2
                preview_count = max(1, preview_count)

                preview_data = historical_data[:preview_count] + historical_data[-preview_count:]
                formatted_message = self._format_financial_data(preview_data, "historical")
                formatted_message += (
                    f"\n\n*Note: Showing preview of {len(preview_data)} out of {len(historical_data)} total records*"
                )
            else:
                formatted_message = self._format_financial_data(historical_data, "historical")

            metadata = YFinanceMetadata(
                symbol=symbol.upper(),
                operation="get_historical_data",
                execution_time=execution_time,
                data_points=len(historical_data),
                yfinance_available=True,
                timestamp=datetime.now().isoformat(),
            )

            self._color_log(f"✅ Historical data retrieved: {len(historical_data)} records", Color.green)

            return ActionResponse(success=True, message=formatted_message, metadata=metadata.model_dump())

        except Exception as e:
            error_msg = f"Failed to fetch historical data for {symbol}: {str(e)}"
            self.logger.error(f"Historical data error: {traceback.format_exc()}")

            metadata = YFinanceMetadata(
                symbol=symbol.upper(),
                operation="get_historical_data",
                error_type=type(e).__name__,
                timestamp=datetime.now().isoformat(),
            )

            return ActionResponse(success=False, message=error_msg, metadata=metadata.model_dump())

    async def mcp_get_company_info(
        self,
        symbol: str = Field(description="Stock ticker symbol (e.g., AAPL, MSFT)"),
    ) -> ActionResponse:
        """Get company information and business details.

        Fetches comprehensive company information including sector, industry,
        employee count, business summary, location, and other key details.

        Args:
            symbol: Stock ticker symbol

        Returns:
            ActionResponse with company information and metadata
        """
        # Handle FieldInfo objects
        if isinstance(symbol, FieldInfo):
            symbol = symbol.default

        try:
            start_time = time.time()
            self._color_log(f"🏢 Fetching company info for: {symbol}", Color.cyan)

            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or not info.get("symbol"):
                raise ValueError(f"No company information found for symbol: {symbol}. It might be invalid.")

            # Extract key company information
            company_data = {
                "symbol": info.get("symbol"),
                "shortName": info.get("shortName"),
                "longName": info.get("longName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "fullTimeEmployees": info.get("fullTimeEmployees"),
                "longBusinessSummary": info.get("longBusinessSummary"),
                "city": info.get("city"),
                "state": info.get("state"),
                "country": info.get("country"),
                "website": info.get("website"),
                "exchange": info.get("exchange"),
                "currency": info.get("currency"),
                "marketCap": info.get("marketCap"),
            }

            # Filter out None values
            company_data = {k: v for k, v in company_data.items() if v is not None}

            execution_time = time.time() - start_time
            formatted_message = self._format_financial_data(company_data, "company")

            metadata = YFinanceMetadata(
                symbol=symbol.upper(),
                operation="get_company_info",
                execution_time=execution_time,
                data_points=len(company_data),
                yfinance_available=True,
                timestamp=datetime.now().isoformat(),
            )

            self._color_log("✅ Company information retrieved successfully", Color.green)

            return ActionResponse(success=True, message=formatted_message, metadata=metadata.model_dump())

        except Exception as e:
            error_msg = f"Failed to fetch company info for {symbol}: {str(e)}"
            self.logger.error(f"Company info error: {traceback.format_exc()}")

            metadata = YFinanceMetadata(
                symbol=symbol.upper(),
                operation="get_company_info",
                error_type=type(e).__name__,
                timestamp=datetime.now().isoformat(),
            )

            return ActionResponse(success=False, message=error_msg, metadata=metadata.model_dump())

    async def mcp_get_financial_statements(
        self,
        symbol: str = Field(description="Stock ticker symbol (e.g., AAPL, MSFT)"),
        statement_type: str = Field(description="Statement type: income_statement, balance_sheet, or cash_flow"),
        period_type: str = Field(default="annual", description="Period type: annual or quarterly"),
        max_columns_preview: int = Field(default=4, description="Max periods to show (0 for all)"),
    ) -> ActionResponse:
        """Get financial statements for a company.

        Fetches financial statements including income statement, balance sheet,
        or cash flow statement for the specified company and period.

        Args:
            symbol: Stock ticker symbol
            statement_type: Type of statement (income_statement, balance_sheet, cash_flow)
            period_type: Period type (annual or quarterly)
            max_columns_preview: Maximum periods to show in preview

        Returns:
            ActionResponse with financial statement data and metadata
        """
        # Handle FieldInfo objects
        if isinstance(symbol, FieldInfo):
            symbol = symbol.default
        if isinstance(statement_type, FieldInfo):
            statement_type = statement_type.default
        if isinstance(period_type, FieldInfo):
            period_type = period_type.default
        if isinstance(max_columns_preview, FieldInfo):
            max_columns_preview = max_columns_preview.default

        try:
            start_time = time.time()
            self._color_log(f"📋 Fetching {statement_type} for: {symbol} ({period_type})", Color.cyan)

            ticker = yf.Ticker(symbol)
            statement_df = None

            # Get appropriate statement
            if statement_type == "income_statement":
                statement_df = ticker.income_stmt if period_type == "annual" else ticker.quarterly_income_stmt
            elif statement_type == "balance_sheet":
                statement_df = ticker.balance_sheet if period_type == "annual" else ticker.quarterly_balance_sheet
            elif statement_type == "cash_flow":
                statement_df = ticker.cashflow if period_type == "annual" else ticker.quarterly_cashflow
            else:
                raise ValueError(
                    f"Invalid statement_type: {statement_type}. "
                    "Must be one of: income_statement, balance_sheet, cash_flow"
                )

            if statement_df is None or statement_df.empty:
                raise ValueError(f"No {period_type} {statement_type} data found for symbol {symbol}")

            # Process DataFrame
            statement_df.reset_index(inplace=True)
            statement_df.rename(columns={"index": "Item"}, inplace=True)

            # Convert date columns to strings
            for col in statement_df.columns:
                if col != "Item":
                    try:
                        if hasattr(col, "strftime"):
                            statement_df.rename(columns={col: col.strftime("%Y-%m-%d")}, inplace=True)
                    except Exception:
                        pass

            statement_data = statement_df.to_dict(orient="records")
            execution_time = time.time() - start_time

            # Format message
            if max_columns_preview > 0 and len(statement_df.columns) > (max_columns_preview + 1):
                columns_to_keep = ["Item"] + list(statement_df.columns[1 : max_columns_preview + 1])
                preview_df = statement_df[columns_to_keep]
                preview_data = preview_df.to_dict(orient="records")

                formatted_message = f"# {statement_type.replace('_', ' ').title()} ({period_type.title()})\n\n"
                formatted_message += (
                    f"Showing preview of most recent {max_columns_preview} periods "
                    f"out of {len(statement_df.columns) - 1} available.\n\n"
                )

                # Show key financial items
                for item in preview_data[:10]:  # Show first 10 items
                    item_name = item.get("Item", "N/A")
                    formatted_message += f"**{item_name}:**\n"
                    for col, value in item.items():
                        if col != "Item" and value is not None:
                            formatted_message += (
                                f"  - {col}: {value:,}\n"
                                if isinstance(value, (int, float))
                                else f"  - {col}: {value}\n"
                            )
                    formatted_message += "\n"
            else:
                formatted_message = f"# {statement_type.replace('_', ' ').title()} ({period_type.title()})\n\n"
                formatted_message += f"Complete financial statement with {len(statement_data)} line items.\n"

            metadata = YFinanceMetadata(
                symbol=symbol.upper(),
                operation="get_financial_statements",
                execution_time=execution_time,
                data_points=len(statement_data),
                yfinance_available=True,
                timestamp=datetime.now().isoformat(),
            )

            self._color_log(f"✅ Financial statements retrieved: {len(statement_data)} items", Color.green)

            return ActionResponse(success=True, message=formatted_message, metadata=metadata.model_dump())

        except Exception as e:
            error_msg = f"Failed to fetch {statement_type} for {symbol}: {str(e)}"
            self.logger.error(f"Financial statements error: {traceback.format_exc()}")

            metadata = YFinanceMetadata(
                symbol=symbol.upper(),
                operation="get_financial_statements",
                error_type=type(e).__name__,
                timestamp=datetime.now().isoformat(),
            )

            return ActionResponse(success=False, message=error_msg, metadata=metadata.model_dump())


# Default arguments for testing
if __name__ == "__main__":
    load_dotenv()

    arguments = ActionArguments(
        name="yahoo-finance",
        transport="stdio",
        workspace=os.getenv("AWORLD_WORKSPACE", "~"),
    )

    try:
        service = YahooFinanceActionCollection(arguments)
        service.run()
    except Exception as e:
        print(f"Error: {e}")
