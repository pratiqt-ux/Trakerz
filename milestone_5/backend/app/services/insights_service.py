"""
Financial Insights & Chart Analytics Service Layer for Milestone 4.
Calculates Month-over-Month (MoM) metrics, weekday spending tendencies,
daily chart data, and dashboard overview metrics using deterministic Python algorithms.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.database.base import BaseExpenseDatabase
from app.models.insights import (
    DailySpendingPoint,
    MonthlyTrendPoint,
    InsightCard,
    DashboardOverview
)
from app.services.budget_service import BudgetService


class InsightsService:
    def __init__(self, db: BaseExpenseDatabase):
        self.db = db
        self.budget_service = BudgetService(db)

    def get_daily_chart(self, month: Optional[str] = None) -> List[DailySpendingPoint]:
        if not month:
            month = datetime.now().strftime("%Y-%m")
        rows = self.db.get_daily_spending(month)
        return [DailySpendingPoint(**r) for r in rows]

    def get_monthly_trend_chart(self, limit: int = 12) -> List[MonthlyTrendPoint]:
        rows = self.db.get_monthly_trend(limit=limit)
        return [MonthlyTrendPoint(**r) for r in rows]

    def get_category_spending_chart(self, month: Optional[str] = None) -> List[Dict[str, Any]]:
        if not month:
            month = datetime.now().strftime("%Y-%m")
        return self.db.get_category_totals_for_month(month)

    def generate_mom_insights(self, target_month: Optional[str] = None) -> List[InsightCard]:
        """
        Generates automatic financial insights comparing current month to previous month:
        - Overall spending change (increased / decreased / identical)
        - Category-specific spending changes
        - Highest spending day / peak day
        - Dominant spending category percentage
        - Budget alerts / overspending warnings
        """
        now = datetime.now()
        if not target_month:
            target_month = now.strftime("%Y-%m")

        # Parse target month to calculate previous month
        try:
            cur_dt = datetime.strptime(target_month, "%Y-%m")
        except ValueError:
            cur_dt = now

        # Previous month
        first_of_cur = cur_dt.replace(day=1)
        prev_dt = first_of_cur - timedelta(days=1)
        prev_month = prev_dt.strftime("%Y-%m")

        cur_cats = {r["category"]: r["total"] for r in self.db.get_category_totals_for_month(target_month)}
        prev_cats = {r["category"]: r["total"] for r in self.db.get_category_totals_for_month(prev_month)}

        cur_total = sum(cur_cats.values())
        prev_total = sum(prev_cats.values())

        insights: List[InsightCard] = []

        # 1. Overall MoM Spending Insight
        if prev_total > 0:
            diff = cur_total - prev_total
            pct_change = round((abs(diff) / prev_total) * 100, 1)
            if diff > 0:
                insights.append(InsightCard(
                    id="mom-total-increase",
                    type="increase",
                    severity="warning",
                    title="Spending Higher than Last Month",
                    description=f"Your total spending in {cur_dt.strftime('%B')} (₹{cur_total:,.2f}) is {pct_change}% higher than {prev_dt.strftime('%B')} (₹{prev_total:,.2f}).",
                    metric=f"+{pct_change}%"
                ))
            elif diff < 0:
                insights.append(InsightCard(
                    id="mom-total-decrease",
                    type="decrease",
                    severity="success",
                    title="Great Job! Lower Spending",
                    description=f"You have spent {pct_change}% less this month (₹{cur_total:,.2f}) compared to {prev_dt.strftime('%B')} (₹{prev_total:,.2f}).",
                    metric=f"-{pct_change}%"
                ))
            else:
                insights.append(InsightCard(
                    id="mom-total-flat",
                    type="info",
                    severity="info",
                    title="Steady Spending Pace",
                    description=f"Your spending is identical to last month at ₹{cur_total:,.2f}.",
                    metric="0.0%"
                ))
        elif cur_total > 0:
            insights.append(InsightCard(
                id="mom-first-month",
                type="info",
                severity="info",
                title=f"Total Spending for {cur_dt.strftime('%B')}",
                description=f"You have recorded ₹{cur_total:,.2f} in total expenses for this month.",
                metric=f"₹{cur_total:,.2f}"
            ))

        # 2. Category Level MoM shifts
        for cat, c_amt in cur_cats.items():
            p_amt = prev_cats.get(cat, 0.0)
            if p_amt > 0:
                cat_diff = c_amt - p_amt
                cat_pct = round((abs(cat_diff) / p_amt) * 100, 1)
                if cat_diff > 0 and cat_pct >= 15.0:
                    insights.append(InsightCard(
                        id=f"mom-cat-inc-{cat}",
                        type="increase",
                        severity="warning",
                        title=f"{cat} Spending Increased",
                        description=f"{cat} spending increased by {cat_pct}% (from ₹{p_amt:,.2f} to ₹{c_amt:,.2f}) compared to last month.",
                        metric=f"+{cat_pct}%"
                    ))
                elif cat_diff < 0 and cat_pct >= 15.0:
                    insights.append(InsightCard(
                        id=f"mom-cat-dec-{cat}",
                        type="decrease",
                        severity="success",
                        title=f"{cat} Spending Decreased",
                        description=f"{cat} spending decreased by {cat_pct}% (from ₹{p_amt:,.2f} down to ₹{c_amt:,.2f}).",
                        metric=f"-{cat_pct}%"
                    ))
            elif c_amt > 0 and prev_total > 0:
                insights.append(InsightCard(
                    id=f"mom-cat-new-{cat}",
                    type="highlight",
                    severity="info",
                    title=f"New Category: {cat}",
                    description=f"You recorded ₹{c_amt:,.2f} in {cat}, which had no expenses last month.",
                    metric=f"₹{c_amt:,.2f}"
                ))

        # 3. Dominant Category Proportion
        if cur_total > 0:
            top_cat = max(cur_cats.items(), key=lambda x: x[1])
            top_pct = round((top_cat[1] / cur_total) * 100, 1)
            if top_pct >= 30.0:
                insights.append(InsightCard(
                    id="dominant-category",
                    type="highlight",
                    severity="info",
                    title=f"Top Category: {top_cat[0]}",
                    description=f"{top_cat[0]} accounts for {top_pct}% of your total spending this month (₹{top_cat[1]:,.2f}).",
                    metric=f"{top_pct}%"
                ))

        # 4. Highest Spending Day of the Week
        daily_pts = self.db.get_daily_spending(target_month)
        weekday_map: Dict[str, float] = {}
        for d in daily_pts:
            w = d["day_name"]
            if w:
                weekday_map[w] = weekday_map.get(w, 0.0) + d["amount"]

        if weekday_map and max(weekday_map.values()) > 0:
            top_day, top_day_amt = max(weekday_map.items(), key=lambda x: x[1])
            insights.append(InsightCard(
                id="highest-spending-day",
                type="highlight",
                severity="info",
                title=f"Peak Day: {top_day}",
                description=f"Your highest spending day of the week is {top_day}, with ₹{top_day_amt:,.2f} spent in total.",
                metric=top_day
            ))

        # 5. Budget Warnings as Insights
        alerts = self.budget_service.get_budget_alerts(month=target_month)
        for a in alerts:
            insights.append(InsightCard(
                id=f"budget-alert-{a.category}",
                type="budget",
                severity="alert" if a.alert_type == "exceeded" else "warning",
                title=f"Budget Alert: {a.category}",
                description=a.message,
                metric=f"{a.percentage_used}%"
            ))

        # 6. Savings Goals Progress Insight
        goals = self.db.get_savings_goals()
        active_goals = [g for g in goals if not g.get("is_completed") and g.get("saved_amount", 0) > 0]
        if active_goals:
            top_goal = max(active_goals, key=lambda g: g.get("progress_percentage", 0))
            insights.append(InsightCard(
                id=f"savings-progress-{top_goal['id']}",
                type="decrease",
                severity="success",
                title=f"Savings Momentum: {top_goal['title']}",
                description=f"You have saved ₹{top_goal['saved_amount']:,.2f} ({top_goal['progress_percentage']}%) toward your '{top_goal['title']}' goal.",
                metric=f"{top_goal['progress_percentage']}%"
            ))

        # 7. Forecast vs Total Monthly Budget Insight
        budgets = self.budget_service.list_budgets(month=target_month)
        total_budget = sum(b.amount for b in budgets)
        if total_budget > 0 and cur_total > 0 and target_month == now.strftime("%Y-%m"):
            days_elapsed = max(1, now.day)
            import calendar
            total_days = calendar.monthrange(now.year, now.month)[1]
            est_month_end = round((cur_total / days_elapsed) * total_days, 2)
            if est_month_end > total_budget and cur_total <= total_budget:
                insights.append(InsightCard(
                    id="forecast-budget-pace",
                    type="increase",
                    severity="warning",
                    title="Spending Pace Above Budget",
                    description=f"At your current rate (₹{cur_total / days_elapsed:,.2f}/day), your estimated month-end spend (₹{est_month_end:,.2f}) may exceed your total monthly budget (₹{total_budget:,.2f}).",
                    metric="Pace Alert"
                ))

        if not insights:
            insights.append(InsightCard(
                id="empty-insight",
                type="info",
                severity="info",
                title="Building Your Financial Profile",
                description="Keep recording your daily expenses to unlock smart month-over-month comparisons and insights!",
                metric="Info"
            ))

        return insights

    def get_dashboard_overview(self) -> DashboardOverview:
        now = datetime.now()
        cur_month = now.strftime("%Y-%m")
        today_str = now.strftime("%Y-%m-%d")

        # Today's spending
        with self.db._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(SUM(amount), 0.0) FROM expenses WHERE date = ?", (today_str,))
            today_spent = round(float(cur.fetchone()[0]), 2)

            cur.execute("SELECT COALESCE(SUM(amount), 0.0), COUNT(id) FROM expenses WHERE substr(date, 1, 7) = ?", (cur_month,))
            row = cur.fetchone()
            cur_month_spent = round(float(row[0]), 2)
            trans_count = int(row[1])

        # Budgets calculation
        budgets = self.budget_service.list_budgets(month=cur_month)
        total_budget = round(sum(b.amount for b in budgets), 2)
        total_spent_on_budgeted = round(sum(b.spent_amount for b in budgets), 2)
        remaining_budget = round(max(0.0, total_budget - total_spent_on_budgeted), 2)
        budget_pct = round((total_spent_on_budgeted / total_budget * 100), 1) if total_budget > 0 else 0.0

        # Recent transactions
        recent_expenses = self.db.get_expenses(limit=6)

        # Active Alerts
        active_alerts = [a.model_dump() for a in self.budget_service.get_budget_alerts(month=cur_month)]

        # Top Insights
        insights = self.generate_mom_insights(target_month=cur_month)[:4]

        return DashboardOverview(
            this_month_spending=cur_month_spent,
            today_spending=today_spent,
            total_budget_amount=total_budget,
            remaining_monthly_budget=remaining_budget,
            budget_usage_percentage=budget_pct,
            transaction_count=trans_count,
            recent_transactions=recent_expenses,
            active_alerts=active_alerts,
            top_insights=insights
        )
