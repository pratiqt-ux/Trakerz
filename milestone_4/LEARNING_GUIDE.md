# Trakerz Milestone 4 — First-Year CSE Student Learning Guide

Welcome to the **Milestone 4 Learning Guide**! In Milestone 3, you learned how frontends and backends communicate over HTTP using JSON. 

In **Milestone 4**, we upgraded Trakerz into a real **Fintech Dashboard** with charts, category budgets, and savings goals. This guide explains how these advanced features work in simple, relatable terms.

---

## 1. How Chart.js Works With FastAPI and HTML5 Canvas

Have you ever wondered how websites draw pie charts and line graphs from numbers?

```
[ FastAPI Backend ] ---- (JSON Array) ----> [ JavaScript (app.js) ] ----> [ HTML5 <canvas> ]
  Calculates sums:                            Passes labels & data          Draws pixels with
  Food: ₹1,200, Travel: ₹450                  into new Chart(canvas, ...)   smooth animations
```

### The 3 Steps of Web Charting:
1. **The HTML Canvas (`<canvas id="categoryChartCanvas"></canvas>`):**
   * Think of `<canvas>` as a blank digital chalkboard on your webpage. By itself, it has no drawings.
2. **The JSON Data from FastAPI:**
   * Your Python backend executes a SQL `GROUP BY` query:
     ```python
     SELECT category, SUM(amount) FROM expenses GROUP BY category
     ```
   * It sends a clean JSON array to the browser:
     ```json
     [
       {"category": "Food", "total": 1200.0},
       {"category": "Travel", "total": 450.0}
     ]
     ```
3. **Chart.js Renders the Graphic:**
   * JavaScript extracts the categories for the `labels` and the totals for the `data`:
     ```javascript
     new Chart(canvas, {
       type: "doughnut",
       data: {
         labels: ["Food", "Travel"],
         datasets: [{ data: [1200, 450], backgroundColor: ["#6366f1", "#10b981"] }]
       }
     });
     ```
   * Chart.js calculates the angles, paints the colors, and hooks up touch tooltips!

---

## 2. How the Smart Financial Insights Algorithm Works (Without AI)

Many people assume "Smart Insights" requires an expensive external AI model. In reality, modern financial apps use **Deterministic Rule-Based Algorithms**.

Here is how our Python function in `services/insights_service.py` calculates insights:

```python
# 1. Fetch current month total vs previous month total
cur_total = sum(current_month_expenses)
prev_total = sum(previous_month_expenses)

# 2. Compute percentage change
diff = cur_total - prev_total
pct_change = round((abs(diff) / prev_total) * 100, 1)

# 3. Apply Decision Logic
if diff > 0 and pct_change >= 10:
    return "Spending Higher: You spent 18% more this month compared to last month."
elif diff < 0 and pct_change >= 10:
    return "Great Job: You spent 12% less this month compared to last month!"
```

### Why this is better than an external AI API:
* **Instant Speed:** Runs in less than 2 milliseconds.
* **100% Reliable:** Math doesn't hallucinate or make arithmetic errors.
* **Completely Free:** No API keys, subscriptions, or credit cards needed.

---

## 3. SQL Relational Modeling: Foreign Keys & CASCADE

In Milestone 2 & 3, we had a single `expenses` table. In Milestone 4, we introduced a **One-to-Many Relationship** between **Savings Goals** and **Contributions**:

```
[ savings_goals ] (Parent Table)
  id: 1, title: "New Laptop", target_amount: 50000
    │
    ├── [ savings_contributions ] (Child Table)
    │     id: 101, goal_id: 1, amount: 15000, date: "2026-11-20"
    └── [ savings_contributions ]
          id: 102, goal_id: 1, amount: 20000, date: "2026-11-24"
```

In SQL, we declare this relationship using a **Foreign Key**:
```sql
CREATE TABLE savings_contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    FOREIGN KEY(goal_id) REFERENCES savings_goals(id) ON DELETE CASCADE
);
```

### What does `ON DELETE CASCADE` do?
If you delete the "New Laptop" goal, SQLite **automatically deletes all related contribution rows** linked to that goal ID. This prevents "orphan rows" from cluttering your database!

---

## 4. Responsive CSS: Desktop Sidebar vs Mobile Bottom Bar

How does the app look like a desktop software on laptops but like a native mobile app on phones?

We use **CSS Media Queries** (`@media (max-width: 768px)`):

```css
/* By Default (Desktop & Laptop screens > 768px): */
.app-sidebar {
  display: flex; /* Sidebar visible on the left */
  width: 250px;
}
.mobile-nav-bar {
  display: none; /* Mobile bottom bar hidden */
}

/* On Mobile Screens (<= 768px): */
@media (max-width: 768px) {
  .app-sidebar {
    display: none; /* Hide sidebar to save screen space */
  }
  .mobile-nav-bar {
    display: flex; /* Show comfortable bottom navigation bar */
  }
}
```

---

## 5. Guided Practice Exercises (Try These Yourself!)

### Exercise 1: Customize the Doughnut Chart Colors
* **Goal:** Change the colors of the Category Spending chart.
* **Steps:**
  1. Open `C:\Trakerz\milestone_4\mobile\js\app.js`.
  2. Locate `const CHART_COLORS = [...]` near line 70.
  3. Change the hex color codes to your favorite color scheme (e.g., `#ff5722`, `#4caf50`).
  4. Refresh your browser and check the Analytics view!

### Exercise 2: Add an Alert Threshold Setting
* **Goal:** Understand where the 80% warning logic lives.
* **Steps:**
  1. Open `C:\Trakerz\milestone_4\backend\app\services\budget_service.py`.
  2. Notice the check: `elif b.status == "warning":` which triggers when `pct >= 80.0`.
  3. Try changing it to `75.0` so warnings appear earlier.

### Exercise 3: Add an Emergency Fund Shortcut
* **Goal:** Add a button that creates a pre-filled "Emergency Fund" savings goal with 1 click.
* **Steps:**
  1. In `mobile/index.html`, add a button next to "+ New Savings Goal".
  2. In `mobile/js/app.js`, attach a click event that sends a `POST /api/savings-goals` request with `{ title: "Emergency Fund", target_amount: 25000, category: "Safety" }`.
