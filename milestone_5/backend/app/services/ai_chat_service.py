"""
AI Financial Chat Assistant Service for Milestone 5.
Connects to Google Gemini REST API using summarized user financial data.
Strictly protects privacy (sends only summarized data, never logs keys,
and gracefully handles missing/invalid keys, rate limits, and network errors).
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
import httpx
from app.database.base import BaseExpenseDatabase
from app.config import settings
from app.models.ai import ChatRequest, ChatResponse, AIStatusResponse
from app.services.budget_service import BudgetService
from app.services.savings_service import SavingsService
from app.services.forecast_service import ForecastService
from app.services.anomaly_service import AnomalyDetectionService
from app.services.insights_service import InsightsService


class AIChatService:
    def __init__(self, db: BaseExpenseDatabase):
        self.db = db
        self.budget_service = BudgetService(db)
        self.savings_service = SavingsService(db)
        self.forecast_service = ForecastService(db)
        self.anomaly_service = AnomalyDetectionService(db)
        self.insights_service = InsightsService(db)

    def is_configured(self) -> bool:
        key = settings.GEMINI_API_KEY
        return bool(key and key != "your_gemini_api_key_here" and len(key) > 10)

    def get_status(self) -> AIStatusResponse:
        configured = self.is_configured()
        return AIStatusResponse(
            ai_configured=configured,
            provider=settings.AI_PROVIDER,
            model=settings.GEMINI_MODEL,
            message=(
                f"AI Assistant ready ({settings.GEMINI_MODEL})"
                if configured
                else "Gemini API key not configured. Add GEMINI_API_KEY to backend/.env to enable AI chat."
            )
        )

    def _build_financial_context(self) -> Dict[str, Any]:
        """
        Builds a compact, privacy-safe summary of the user's Trakerz data.
        Avoids dumping the entire raw database; includes totals, categories,
        budgets, savings goals, forecast, anomalies, and recent 20 transactions.
        """
        now = datetime.now()
        cur_month = now.strftime("%Y-%m")
        prev_month = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        week_start = (now - timedelta(days=6)).strftime("%Y-%m-%d")
        today_str = now.strftime("%Y-%m-%d")

        all_expenses = self.db.get_expenses()
        cur_month_cats = self.db.get_category_totals_for_month(cur_month)
        prev_month_cats = self.db.get_category_totals_for_month(prev_month)

        # Weekly spending by category
        week_by_cat: Dict[str, float] = {}
        for e in all_expenses:
            dt = str(e.get("date", ""))
            if week_start <= dt <= today_str:
                cat = e.get("category", "Other")
                week_by_cat[cat] = round(week_by_cat.get(cat, 0.0) + float(e.get("amount", 0.0)), 2)

        budgets = [
            {
                "category": b.category,
                "limit_inr": b.amount,
                "spent_inr": b.spent_amount,
                "remaining_inr": b.remaining_amount,
                "used_pct": b.percentage_used,
                "status": b.status
            }
            for b in self.budget_service.list_budgets(cur_month)
        ]

        goals = [
            {
                "title": g.title,
                "target_inr": g.target_amount,
                "saved_inr": g.saved_amount,
                "remaining_inr": g.remaining_amount,
                "progress_pct": g.progress_percentage,
                "completed": g.is_completed,
                "deadline": g.deadline
            }
            for g in self.savings_service.list_goals()
        ]

        forecast = self.forecast_service.compute_monthly_forecast(cur_month)
        anomalies = [a.message for a in self.anomaly_service.detect_anomalies()]
        insights = [i.description for i in self.insights_service.generate_mom_insights(cur_month)]

        recent_txs = [
            {
                "date": e["date"],
                "category": e["category"],
                "amount_inr": e["amount"],
                "description": e.get("description", "")
            }
            for e in all_expenses[:20]
        ]

        return {
            "today": today_str,
            "current_month": cur_month,
            "previous_month": prev_month,
            "total_all_time_expenses_count": len(all_expenses),
            "total_all_time_inr": self.db.get_total_expense(),
            "current_month_total_inr": round(sum(c["total"] for c in cur_month_cats), 2),
            "current_month_by_category": cur_month_cats,
            "previous_month_total_inr": round(sum(c["total"] for c in prev_month_cats), 2),
            "previous_month_by_category": prev_month_cats,
            "last_7_days_by_category": week_by_cat,
            "monthly_budgets": budgets,
            "savings_goals": goals,
            "monthly_forecast_estimate": {
                "estimated_month_end_inr": forecast.estimated_month_end_spending,
                "average_daily_inr": forecast.average_daily_spending,
                "days_elapsed": forecast.days_elapsed,
                "remaining_days": forecast.remaining_days,
                "confidence": forecast.confidence_level
            },
            "unusual_spending_alerts": anomalies,
            "key_insights": insights,
            "recent_20_transactions": recent_txs
        }

    async def chat(self, req: ChatRequest) -> ChatResponse:
        if not self.is_configured():
            return ChatResponse(
                reply=(
                    "The AI Assistant is currently not configured because no Gemini API key was found. "
                    "To enable it, add your `GEMINI_API_KEY` to `milestone_5/backend/.env` and restart the server. "
                    "All other Trakerz features (tracking, budgets, forecasts, charts, and insights) continue to work normally."
                ),
                ai_available=False,
                provider=settings.AI_PROVIDER,
                model=settings.GEMINI_MODEL,
                error_type="not_configured"
            )

        context_summary = self._build_financial_context()

        system_prompt = (
            "You are Trakerz AI, a helpful, honest, and concise personal finance assistant built into the Trakerz expense tracker.\n"
            "STRICT RULES:\n"
            "1. Answer using ONLY the user's real Trakerz financial data provided below. Currency is Indian Rupees (₹).\n"
            "2. NEVER invent expenses, amounts, dates, budgets, or savings goals.\n"
            "3. If the user asks about something not present in the data (or if there are 0 expenses), clearly say there is insufficient data.\n"
            "4. Never claim you added, edited, or deleted an expense—you are a read-only analytical assistant.\n"
            "5. Clearly label month-end forecasts as estimates, never guaranteed outcomes.\n"
            "6. Keep answers clear, structured, and easy for a college student to understand.\n\n"
            f"USER FINANCIAL DATA SUMMARY (JSON):\n{context_summary}"
        )

        # Build Gemini conversation contents
        contents = []
        for msg in req.history[-8:]:
            gemini_role = "user" if msg.role == "user" else "model"
            contents.append({"role": gemini_role, "parts": [{"text": msg.content}]})
        contents.append({"role": "user", "parts": [{"text": req.message}]})

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 700
            }
        }

        try:
            async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
                res = await client.post(
                    url,
                    headers={
                        "x-goog-api-key": settings.GEMINI_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json=payload
                )

            if res.status_code == 200:
                data = res.json()
                candidates = data.get("candidates", [])
                if candidates and candidates[0].get("content", {}).get("parts"):
                    reply_text = candidates[0]["content"]["parts"][0].get("text", "").strip()
                    return ChatResponse(
                        reply=reply_text,
                        ai_available=True,
                        provider=settings.AI_PROVIDER,
                        model=settings.GEMINI_MODEL,
                        data_context_used={
                            "expenses_count": context_summary["total_all_time_expenses_count"],
                            "current_month_total": context_summary["current_month_total_inr"]
                        }
                    )
                return ChatResponse(
                    reply="The AI model returned an empty response. Please try rephrasing your question.",
                    ai_available=True,
                    provider=settings.AI_PROVIDER,
                    model=settings.GEMINI_MODEL,
                    error_type="api_error"
                )

            elif res.status_code in (400, 401, 403):
                return ChatResponse(
                    reply="Authentication failed: Your Gemini API key appears invalid or lacks permission. Please verify `GEMINI_API_KEY` in `backend/.env`.",
                    ai_available=False,
                    provider=settings.AI_PROVIDER,
                    model=settings.GEMINI_MODEL,
                    error_type="invalid_key"
                )
            elif res.status_code == 429:
                return ChatResponse(
                    reply="AI rate limit reached. Please wait a few moments and try asking again.",
                    ai_available=True,
                    provider=settings.AI_PROVIDER,
                    model=settings.GEMINI_MODEL,
                    error_type="rate_limit"
                )
            else:
                return ChatResponse(
                    reply=f"The AI service returned an unexpected error (HTTP {res.status_code}). Please try again later.",
                    ai_available=False,
                    provider=settings.AI_PROVIDER,
                    model=settings.GEMINI_MODEL,
                    error_type="api_error"
                )

        except httpx.TimeoutException:
            return ChatResponse(
                reply="The AI request timed out. Please check your internet connection and try again.",
                ai_available=False,
                provider=settings.AI_PROVIDER,
                model=settings.GEMINI_MODEL,
                error_type="timeout"
            )
        except httpx.RequestError:
            return ChatResponse(
                reply="Could not reach the Gemini AI service. Please check your internet connection—your local Trakerz features still work offline.",
                ai_available=False,
                provider=settings.AI_PROVIDER,
                model=settings.GEMINI_MODEL,
                error_type="network_error"
            )
        except Exception:
            return ChatResponse(
                reply="An unexpected error occurred while contacting the AI assistant.",
                ai_available=False,
                provider=settings.AI_PROVIDER,
                model=settings.GEMINI_MODEL,
                error_type="api_error"
            )
