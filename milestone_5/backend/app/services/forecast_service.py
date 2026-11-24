"""
Monthly Spending Forecast Service for Milestone 5.
Estimates month-end spending from current month run-rate and historical context.
Always labels forecasts clearly as estimates.
"""
import calendar
from datetime import datetime, timedelta
from typing import Optional, List
from app.database.base import BaseExpenseDatabase
from app.models.ai import MonthlyForecast, ForecastPoint


class ForecastService:
    def __init__(self, db: BaseExpenseDatabase):
        self.db = db

    def compute_monthly_forecast(self, target_month: Optional[str] = None, reference_date: Optional[str] = None) -> MonthlyForecast:
        now = datetime.strptime(reference_date, "%Y-%m-%d") if reference_date else datetime.now()
        if not target_month:
            target_month = now.strftime("%Y-%m")

        try:
            year, month_num = map(int, target_month.split("-"))
            total_days = calendar.monthrange(year, month_num)[1]
        except Exception:
            year, month_num = now.year, now.month
            total_days = calendar.monthrange(year, month_num)[1]

        current_ym = now.strftime("%Y-%m")
        if target_month == current_ym:
            days_elapsed = now.day
        elif target_month < current_ym:
            days_elapsed = total_days
        else:
            days_elapsed = 0

        remaining_days = max(0, total_days - days_elapsed)

        # Previous month total for comparison
        first_day = datetime(year, month_num, 1)
        prev_month_dt = first_day - timedelta(days=1)
        prev_month_ym = prev_month_dt.strftime("%Y-%m")

        daily_rows = self.db.get_daily_spending(target_month)
        prev_daily_rows = self.db.get_daily_spending(prev_month_ym)

        current_spending = round(sum(d["amount"] for d in daily_rows), 2)
        previous_month_spending = round(sum(d["amount"] for d in prev_daily_rows), 2)

        if days_elapsed == 0 or current_spending == 0:
            return MonthlyForecast(
                month=target_month,
                current_spending=current_spending,
                days_elapsed=days_elapsed,
                total_days_in_month=total_days,
                remaining_days=remaining_days,
                average_daily_spending=0.0,
                estimated_month_end_spending=0.0,
                previous_month_spending=previous_month_spending,
                previous_month_diff_pct=None,
                confidence_level="insufficient_data",
                is_estimate=True,
                note="Not enough expenses recorded in this month to generate a spending forecast yet.",
                projected_series=[]
            )

        avg_daily = round(current_spending / days_elapsed, 2)
        linear_estimate = avg_daily * total_days

        # If past month, final spending is already known
        if target_month < current_ym:
            estimated_total = current_spending
            confidence = "high"
            note = "Month completed — actual total spending is shown."
        elif days_elapsed < 3:
            estimated_total = round(linear_estimate, 2)
            confidence = "low"
            note = f"Early estimate based on only {days_elapsed} day(s) of spending. Accuracy improves as more days are recorded."
        else:
            # Blend current run-rate with previous month pace if available
            if previous_month_spending > 0 and days_elapsed < 20:
                prev_daily_avg = previous_month_spending / len(prev_daily_rows)
                weight_current = min(0.85, 0.5 + (days_elapsed / total_days) * 0.5)
                blended_daily = (avg_daily * weight_current) + (prev_daily_avg * (1 - weight_current))
                estimated_total = round(current_spending + (blended_daily * remaining_days), 2)
                confidence = "moderate" if days_elapsed < 14 else "high"
                note = f"Estimate based on your ₹{avg_daily:,.2f}/day pace blended with last month's pattern."
            else:
                estimated_total = round(linear_estimate, 2)
                confidence = "moderate" if days_elapsed < 12 else "high"
                note = f"Estimate projected from your current average of ₹{avg_daily:,.2f}/day across {days_elapsed} elapsed days."

        # Previous month comparison %
        prev_diff_pct = None
        if previous_month_spending > 0:
            prev_diff_pct = round(((estimated_total - previous_month_spending) / previous_month_spending) * 100, 1)

        # Build cumulative actual + projected series for Chart.js
        series: List[ForecastPoint] = []
        running_actual = 0.0
        daily_proj_step = (estimated_total - current_spending) / remaining_days if remaining_days > 0 else 0.0

        for d in daily_rows:
            day_num = d["day"]
            if day_num <= days_elapsed:
                running_actual += d["amount"]
                series.append(ForecastPoint(
                    day=day_num,
                    date=d["date"],
                    actual_cumulative=round(running_actual, 2),
                    projected_cumulative=round(running_actual, 2)
                ))
            else:
                days_ahead = day_num - days_elapsed
                proj_val = current_spending + (daily_proj_step * days_ahead)
                series.append(ForecastPoint(
                    day=day_num,
                    date=d["date"],
                    actual_cumulative=None,
                    projected_cumulative=round(proj_val, 2)
                ))

        return MonthlyForecast(
            month=target_month,
            current_spending=current_spending,
            days_elapsed=days_elapsed,
            total_days_in_month=total_days,
            remaining_days=remaining_days,
            average_daily_spending=avg_daily,
            estimated_month_end_spending=estimated_total,
            previous_month_spending=previous_month_spending,
            previous_month_diff_pct=prev_diff_pct,
            confidence_level=confidence,
            is_estimate=True,
            note=note,
            projected_series=series
        )
