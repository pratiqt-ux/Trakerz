"""
Unusual Spending Detection Service for Milestone 5.
Analyzes historical expenses to flag genuine spending spikes and anomalies
while avoiding false positives on insufficient data.
"""
from datetime import datetime, timedelta
from typing import List, Dict
from collections import defaultdict
from app.database.base import BaseExpenseDatabase
from app.models.ai import SpendingAnomaly


class AnomalyDetectionService:
    def __init__(self, db: BaseExpenseDatabase):
        self.db = db

    def detect_anomalies(self, reference_date: str = None) -> List[SpendingAnomaly]:
        expenses = self.db.get_expenses()
        if not expenses or len(expenses) < 5:
            # Insufficient historical data to establish a baseline
            return []

        now = datetime.strptime(reference_date, "%Y-%m-%d") if reference_date else datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        week_start = (now - timedelta(days=6)).strftime("%Y-%m-%d")
        prev_window_start = (now - timedelta(days=34)).strftime("%Y-%m-%d")
        prev_window_end = (now - timedelta(days=7)).strftime("%Y-%m-%d")

        # Group expenses by date and category
        distinct_days = set()
        today_by_cat: Dict[str, float] = defaultdict(float)
        hist_cat_days: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        cat_all_amounts: Dict[str, List[float]] = defaultdict(list)

        this_week_cat: Dict[str, float] = defaultdict(float)
        prev_4weeks_cat: Dict[str, float] = defaultdict(float)
        prev_window_days = set()

        for e in expenses:
            dt = str(e.get("date", ""))
            cat = str(e.get("category", "Other"))
            amt = float(e.get("amount", 0.0))
            if not dt or amt <= 0:
                continue

            distinct_days.add(dt)
            cat_all_amounts[cat].append(amt)

            if dt == today_str:
                today_by_cat[cat] += amt
            else:
                hist_cat_days[cat][dt] += amt

            if week_start <= dt <= today_str:
                this_week_cat[cat] += amt
            elif prev_window_start <= dt <= prev_window_end:
                prev_4weeks_cat[cat] += amt
                prev_window_days.add(dt)

        if len(distinct_days) < 3:
            return []

        anomalies: List[SpendingAnomaly] = []

        # 1. Today's Category Daily Spike (e.g. Food spending today is 2.1x usual)
        for cat, today_amt in today_by_cat.items():
            past_days_map = hist_cat_days.get(cat, {})
            if len(past_days_map) >= 3:
                usual_daily_avg = sum(past_days_map.values()) / len(past_days_map)
                if usual_daily_avg > 0 and today_amt >= 200:
                    ratio = round(today_amt / usual_daily_avg, 1)
                    if ratio >= 1.8:
                        anomalies.append(SpendingAnomaly(
                            id=f"daily-spike-{cat.lower()}-{today_str}",
                            anomaly_type="daily_category_spike",
                            severity="warning" if ratio >= 2.5 else "info",
                            category=cat,
                            title=f"Unusual {cat} Spending Today",
                            message=f"Your {cat} spending today (₹{today_amt:,.2f}) is {ratio}× your usual daily {cat} spending.",
                            explanation=f"Calculated from {len(past_days_map)} previous active {cat} days averaging ₹{usual_daily_avg:,.2f}/day.",
                            ratio=ratio
                        ))

        # 2. Weekly Category Surge (requires at least 7 days in previous window)
        if len(prev_window_days) >= 5:
            # Normalize previous window to weekly average
            span_weeks = max(1.0, len(prev_window_days) / 7.0)
            # Use 4 weeks if full history, otherwise actual active weeks
            for cat, week_amt in this_week_cat.items():
                prev_total = prev_4weeks_cat.get(cat, 0.0)
                if prev_total > 0:
                    prev_weekly_avg = prev_total / min(4.0, span_weeks)
                    if prev_weekly_avg > 0 and (week_amt - prev_weekly_avg) >= 200:
                        pct_inc = round(((week_amt - prev_weekly_avg) / prev_weekly_avg) * 100, 1)
                        if pct_inc >= 25.0:
                            anomalies.append(SpendingAnomaly(
                                id=f"weekly-surge-{cat.lower()}-{week_start}",
                                anomaly_type="weekly_category_surge",
                                severity="warning" if pct_inc >= 50 else "info",
                                category=cat,
                                title=f"{cat} Weekly Surge",
                                message=f"Your {cat} spending this week (₹{week_amt:,.2f}) is {pct_inc}% higher than your previous weekly average.",
                                explanation=f"Compared last 7 days (₹{week_amt:,.2f}) against prior weekly average (₹{prev_weekly_avg:,.2f}).",
                                ratio=round(week_amt / prev_weekly_avg, 2)
                            ))

        # 3. Unusually Large Single Transaction (recent 7 days)
        for e in expenses:
            dt = str(e.get("date", ""))
            if not (week_start <= dt <= today_str):
                continue
            cat = str(e.get("category", "Other"))
            amt = float(e.get("amount", 0.0))
            all_cat_txs = cat_all_amounts.get(cat, [])
            if len(all_cat_txs) >= 4 and amt >= 500:
                other_txs = [x for x in all_cat_txs if x != amt]
                if not other_txs:
                    continue
                cat_avg = sum(other_txs) / len(other_txs)
                if cat_avg > 0:
                    ratio = round(amt / cat_avg, 1)
                    if ratio >= 2.5:
                        desc_label = e.get("description") or cat
                        anomalies.append(SpendingAnomaly(
                            id=f"large-tx-{e.get('id')}",
                            anomaly_type="large_transaction",
                            severity="info",
                            category=cat,
                            title=f"Large {cat} Expense Detected",
                            message=f"'{desc_label}' (₹{amt:,.2f} on {dt}) is {ratio}× your typical {cat} transaction.",
                            explanation=f"Your average {cat} transaction is ₹{cat_avg:,.2f} across {len(other_txs)} other records.",
                            ratio=ratio
                        ))
                        break  # Limit to most recent large transaction to avoid clutter

        return anomalies[:5]
