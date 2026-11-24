/**
 * Trakerz Milestone 4: Modern Fintech Dashboard & Smart Analytics Client
 * Complete state management, Chart.js visualizations, budgets, and savings goals.
 */

// Global Application State
const state = {
  currentView: "dashboard",
  selectedMonth: new Date().toISOString().slice(0, 7), // YYYY-MM
  systemStatus: null,
  dashboardData: null,
  expenses: [],
  budgets: [],
  budgetAlerts: [],
  savingsGoals: [],
  charts: {
    category: null,
    monthly: null,
    daily: null
  },
  dismissedAlerts: new Set(JSON.parse(sessionStorage.getItem("trakerz_dismissed_alerts") || "[]")),
  deleteTarget: null // { type: 'expense'|'budget'|'goal'|'contribution', id: string, summary: string }
};

// Indian Rupee currency formatter
function formatINR(amount) {
  const num = Number(amount) || 0;
  return num.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  try {
    const today = new Date().toISOString().split("T")[0];
    if (dateStr === today) return "Today";

    const d = new Date(dateStr + "T00:00:00");
    return d.toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric"
    });
  } catch (e) {
    return dateStr;
  }
}

function escapeHTML(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Category Emoji Map for instant visual recognition
const CATEGORY_EMOJIS = {
  food: "🍔",
  dining: "🍽️",
  travel: "🚕",
  transport: "🚌",
  commute: "🚆",
  shopping: "🛒",
  bills: "💡",
  utilities: "⚡",
  entertainment: "🍿",
  movies: "🎬",
  health: "💊",
  medical: "🏥",
  groceries: "🥦",
  education: "📚",
  college: "🎓",
  other: "🏷️"
};

function getCategoryEmoji(category) {
  if (!category) return "🏷️";
  const lower = category.toLowerCase().trim();
  for (const [key, emoji] of Object.entries(CATEGORY_EMOJIS)) {
    if (lower.includes(key)) return emoji;
  }
  return "🏷️";
}

// Chart Palette
const CHART_COLORS = [
  "#6366f1", "#10b981", "#f59e0b", "#0ea5e9", "#ec4899",
  "#8b5cf6", "#14b8a6", "#f97316", "#06b6d4", "#84cc16"
];

// ==============================================================
// API Client
// ==============================================================

async function fetchAPI(endpoint, options = {}) {
  try {
    const res = await fetch(`/api${endpoint}`, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers
      },
      ...options
    });

    if (!res.ok) {
      let errorMsg = `Server error (${res.status})`;
      try {
        const errJson = await res.json();
        if (errJson.detail) {
          errorMsg = Array.isArray(errJson.detail)
            ? errJson.detail.map(d => d.msg || d).join(", ")
            : errJson.detail;
        }
      } catch (_) {}
      throw new Error(errorMsg);
    }

    return await res.json();
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${type === "success" ? "✓" : type === "danger" ? "⚠️" : type === "warning" ? "⚡" : "ℹ️"}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

// ==============================================================
// Navigation View Switching
// ==============================================================

function switchView(viewName) {
  state.currentView = viewName;

  // Update desktop navigation links
  document.querySelectorAll(".sidebar-nav .nav-link").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-view") === viewName);
  });

  // Update mobile bottom nav items
  document.querySelectorAll(".mobile-nav-bar .mobile-nav-item").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-view") === viewName);
  });

  // Update views
  document.querySelectorAll(".view-section").forEach(sec => {
    sec.classList.remove("active");
  });
  const targetView = document.getElementById(`view-${viewName}`);
  if (targetView) targetView.classList.add("active");

  // Title update
  const titleMap = {
    dashboard: "Dashboard",
    transactions: "Transactions & Records",
    budgets: "Monthly Category Budgets",
    analytics: "Smart Financial Analytics",
    savings: "Savings Goals"
  };
  document.getElementById("topPageTitle").textContent = titleMap[viewName] || "Dashboard";

  // Trigger relevant view data load
  if (viewName === "dashboard") loadDashboard();
  else if (viewName === "transactions") loadTransactions();
  else if (viewName === "budgets") loadBudgets();
  else if (viewName === "analytics") loadAnalytics();
  else if (viewName === "savings") loadSavingsGoals();
}

// ==============================================================
// VIEW 1: DASHBOARD
// ==============================================================

async function loadDashboard() {
  try {
    const overview = await fetchAPI("/analytics/dashboard-overview");
    state.dashboardData = overview;

    // KPI Cards
    document.getElementById("kpiThisMonthAmount").textContent = formatINR(overview.this_month_spending);
    document.getElementById("kpiThisMonthSub").textContent = `${overview.transaction_count} transactions this month`;

    document.getElementById("kpiTodayAmount").textContent = formatINR(overview.today_spending);
    document.getElementById("kpiRemainingBudget").textContent = formatINR(overview.remaining_monthly_budget);
    document.getElementById("kpiBudgetSub").textContent = `${overview.budget_usage_percentage}% of total budget used`;

    // Total records count
    const totalAnalytics = await fetchAPI("/analytics/total");
    document.getElementById("kpiTotalRecords").textContent = totalAnalytics.expense_count;

    // Render Alerts Banner
    renderAlertsBanner(overview.active_alerts);

    // Render Budgets Preview (Left column)
    renderDashboardBudgets();

    // Render Insights (Right column)
    renderDashboardInsights(overview.top_insights);

    // Render Recent Transactions
    renderDashboardRecentTx(overview.recent_transactions);
  } catch (err) {
    showToast(err.message || "Failed to load dashboard data", "danger");
  }
}

function renderAlertsBanner(alerts) {
  const container = document.getElementById("alertsBannerContainer");
  container.innerHTML = "";

  if (!alerts || alerts.length === 0) return;

  alerts.forEach(a => {
    const alertId = `${a.category}-${a.alert_type}-${state.selectedMonth}`;
    if (state.dismissedAlerts.has(alertId)) return;

    const banner = document.createElement("div");
    banner.className = `alert-card ${a.alert_type}`;
    banner.innerHTML = `
      <div class="alert-content">
        <span class="alert-icon">${a.alert_type === "exceeded" ? "🚨" : "⚠️"}</span>
        <span>${escapeHTML(a.message)}</span>
      </div>
      <button class="alert-close" title="Dismiss">&times;</button>
    `;

    banner.querySelector(".alert-close").addEventListener("click", () => {
      state.dismissedAlerts.add(alertId);
      sessionStorage.setItem("trakerz_dismissed_alerts", JSON.stringify([...state.dismissedAlerts]));
      banner.remove();
    });

    container.appendChild(banner);
  });
}

async function renderDashboardBudgets() {
  const list = document.getElementById("dashBudgetsList");
  list.innerHTML = "";

  try {
    const budgets = await fetchAPI(`/budgets?month=${state.selectedMonth}`);
    state.budgets = budgets;

    if (!budgets || budgets.length === 0) {
      list.innerHTML = `
        <div style="color: var(--text-tertiary); font-size: 13px; text-align: center; padding: 16px 0;">
          No category budgets set for ${state.selectedMonth}.
          <br><a class="panel-link" data-switch-view="budgets" style="display: inline-block; margin-top: 6px;">+ Set First Budget</a>
        </div>
      `;
      setupPanelLinks();
      return;
    }

    budgets.slice(0, 5).forEach(b => {
      const emoji = getCategoryEmoji(b.category);
      const row = document.createElement("div");
      row.className = "budget-row-compact";

      const pct = Math.min(b.percentage_used, 100);
      const statusClass = b.status; // normal, warning, exceeded

      row.innerHTML = `
        <div class="budget-row-meta">
          <span class="budget-cat-name">${emoji} ${escapeHTML(b.category)}</span>
          <span class="budget-spent-ratio">₹${formatINR(b.spent_amount)} / ₹${formatINR(b.amount)} (${b.percentage_used}%)</span>
        </div>
        <div class="progress-bar-wrap">
          <div class="progress-bar-fill ${statusClass}" style="width: ${pct}%;"></div>
        </div>
      `;
      list.appendChild(row);
    });
  } catch (err) {
    list.innerHTML = `<div style="color: var(--danger); font-size: 12px;">Failed to load budgets</div>`;
  }
}

function renderDashboardInsights(insights) {
  const list = document.getElementById("dashInsightsList");
  list.innerHTML = "";

  if (!insights || insights.length === 0) {
    list.innerHTML = `<div style="color: var(--text-tertiary); font-size: 13px; text-align: center; padding: 16px 0;">Add expenses to see financial insights.</div>`;
    return;
  }

  insights.forEach(item => {
    const card = document.createElement("div");
    card.className = "insight-item";
    const icon = item.type === "increase" ? "📈" : item.type === "decrease" ? "📉" : item.type === "budget" ? "⚠️" : "💡";
    card.innerHTML = `
      <div class="insight-icon-box ${item.type}">
        ${icon}
      </div>
      <div class="insight-body">
        <h4>${escapeHTML(item.title)}</h4>
        <p>${escapeHTML(item.description)}</p>
      </div>
    `;
    list.appendChild(card);
  });
}

function renderDashboardRecentTx(transactions) {
  const tbody = document.getElementById("dashRecentTxBody");
  tbody.innerHTML = "";

  if (!transactions || transactions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-tertiary); padding: 24px;">No recent transactions recorded.</td></tr>`;
    return;
  }

  transactions.forEach(tx => {
    const emoji = getCategoryEmoji(tx.category);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <span class="tx-category-badge">${emoji} ${escapeHTML(tx.category)}</span>
      </td>
      <td>${escapeHTML(tx.description || "-")}</td>
      <td>${formatDate(tx.date)}</td>
      <td class="tx-amount">₹${formatINR(tx.amount)}</td>
      <td>
        <button class="action-delete-btn" title="Delete Expense" data-delete-type="expense" data-id="${tx.id}" data-summary="${escapeHTML(tx.category)}: ₹${formatINR(tx.amount)}">
          ✕
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  hookDeleteButtons();
}

// ==============================================================
// VIEW 2: TRANSACTIONS
// ==============================================================

async function loadTransactions() {
  try {
    const expenses = await fetchAPI("/expenses");
    state.expenses = expenses;

    // Populate category dropdown
    const select = document.getElementById("txCategoryFilter");
    const currentVal = select.value;
    const categories = ["ALL", ...new Set(expenses.map(e => e.category))];

    select.innerHTML = "";
    categories.forEach(cat => {
      const opt = document.createElement("option");
      opt.value = cat;
      opt.textContent = cat === "ALL" ? "All Categories" : `${getCategoryEmoji(cat)} ${cat}`;
      select.appendChild(opt);
    });
    if (categories.includes(currentVal)) select.value = currentVal;

    filterAndRenderTransactions();
  } catch (err) {
    showToast(err.message || "Failed to load transactions", "danger");
  }
}

function filterAndRenderTransactions() {
  const query = (document.getElementById("txSearchInput").value || "").toLowerCase().trim();
  const catFilter = document.getElementById("txCategoryFilter").value;
  const tbody = document.getElementById("fullTxTableBody");
  const emptyBox = document.getElementById("txEmptyState");

  tbody.innerHTML = "";

  const filtered = state.expenses.filter(tx => {
    const matchCat = catFilter === "ALL" || tx.category.toLowerCase() === catFilter.toLowerCase();
    const matchSearch = !query ||
      tx.category.toLowerCase().includes(query) ||
      (tx.description && tx.description.toLowerCase().includes(query)) ||
      String(tx.amount).includes(query);
    return matchCat && matchSearch;
  });

  if (filtered.length === 0) {
    emptyBox.style.display = "block";
    return;
  }
  emptyBox.style.display = "none";

  filtered.forEach(tx => {
    const emoji = getCategoryEmoji(tx.category);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <span class="tx-category-badge">${emoji} ${escapeHTML(tx.category)}</span>
      </td>
      <td>${escapeHTML(tx.description || "-")}</td>
      <td>${formatDate(tx.date)}</td>
      <td class="tx-amount">₹${formatINR(tx.amount)}</td>
      <td>
        <button class="action-delete-btn" title="Delete" data-delete-type="expense" data-id="${tx.id}" data-summary="${escapeHTML(tx.category)}: ₹${formatINR(tx.amount)}">
          ✕
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  hookDeleteButtons();
}

// ==============================================================
// VIEW 3: MONTHLY BUDGETS
// ==============================================================

async function loadBudgets() {
  try {
    const budgets = await fetchAPI(`/budgets?month=${state.selectedMonth}`);
    state.budgets = budgets;
    renderBudgetsGrid(budgets);
  } catch (err) {
    showToast(err.message || "Failed to load category budgets", "danger");
  }
}

function renderBudgetsGrid(budgets) {
  const grid = document.getElementById("budgetsGrid");
  const emptyBox = document.getElementById("budgetsEmptyState");
  grid.innerHTML = "";

  if (!budgets || budgets.length === 0) {
    emptyBox.style.display = "block";
    return;
  }
  emptyBox.style.display = "none";

  budgets.forEach(b => {
    const emoji = getCategoryEmoji(b.category);
    const card = document.createElement("div");
    card.className = "budget-card";

    let badgeText = "On Track";
    let badgeClass = "success";
    if (b.status === "exceeded") {
      badgeText = `Exceeded by ₹${formatINR(b.overspent_amount)}`;
      badgeClass = "danger";
    } else if (b.status === "warning") {
      badgeText = `${b.percentage_used}% (Near Limit)`;
      badgeClass = "warning";
    }

    const pctWidth = Math.min(b.percentage_used, 100);

    card.innerHTML = `
      <div class="budget-card-top">
        <div>
          <div class="budget-card-title">${emoji} ${escapeHTML(b.category)}</div>
          <span style="font-size: 11px; color: var(--text-tertiary);">Month: ${b.month}</span>
        </div>
        <span class="kpi-badge ${badgeClass}">${badgeText}</span>
      </div>

      <div class="progress-bar-wrap" style="height: 10px;">
        <div class="progress-bar-fill ${b.status}" style="width: ${pctWidth}%;"></div>
      </div>

      <div class="budget-card-stats">
        <div class="stat-col">
          <span class="stat-col-label">Budget Limit</span>
          <span class="stat-col-val">₹${formatINR(b.amount)}</span>
        </div>
        <div class="stat-col">
          <span class="stat-col-label">Actual Spent</span>
          <span class="stat-col-val" style="color: ${b.status === 'exceeded' ? 'var(--danger)' : '#fff'};">₹${formatINR(b.spent_amount)}</span>
        </div>
        <div class="stat-col">
          <span class="stat-col-label">Remaining</span>
          <span class="stat-col-val">₹${formatINR(b.remaining_amount)}</span>
        </div>
        <div class="stat-col">
          <span class="stat-col-label">Usage</span>
          <span class="stat-col-val">${b.percentage_used}%</span>
        </div>
      </div>

      <div class="budget-card-actions">
        <button class="btn-secondary" style="padding: 6px 12px; font-size: 12px;" data-edit-budget-id="${b.id}" data-cat="${escapeHTML(b.category)}" data-amt="${b.amount}" data-month="${b.month}">
          Edit Limit
        </button>
        <button class="action-delete-btn" title="Delete Budget" data-delete-type="budget" data-id="${b.id}" data-summary="${escapeHTML(b.category)} Budget (₹${formatINR(b.amount)})">
          ✕
        </button>
      </div>
    `;

    // Hook edit button
    const editBtn = card.querySelector("[data-edit-budget-id]");
    editBtn.addEventListener("click", () => {
      openSetBudgetModal(editBtn.getAttribute("data-cat"), editBtn.getAttribute("data-amt"), editBtn.getAttribute("data-month"));
    });

    grid.appendChild(card);
  });

  hookDeleteButtons();
}

// ==============================================================
// VIEW 4: ANALYTICS & CHARTS (Chart.js)
// ==============================================================

async function loadAnalytics() {
  try {
    const [catData, monthlyData, dailyData, insights] = await Promise.all([
      fetchAPI(`/analytics/category-month?month=${state.selectedMonth}`),
      fetchAPI("/analytics/monthly-trend"),
      fetchAPI(`/analytics/daily?month=${state.selectedMonth}`),
      fetchAPI(`/analytics/insights?month=${state.selectedMonth}`)
    ]);

    renderCategoryChart(catData);
    renderMonthlyTrendChart(monthlyData);
    renderDailySpendingChart(dailyData);
    renderAnalyticsInsights(insights);
  } catch (err) {
    showToast(err.message || "Failed to load analytics data", "danger");
  }
}

function renderCategoryChart(data) {
  const canvas = document.getElementById("categoryChartCanvas");
  if (!canvas || typeof Chart === "undefined") return;

  if (state.charts.category) {
    state.charts.category.destroy();
  }

  const labels = data.map(d => d.category);
  const values = data.map(d => d.total);

  if (labels.length === 0) {
    labels.push("No Expenses Yet");
    values.push(1);
  }

  state.charts.category = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: labels[0] === "No Expenses Yet" ? ["#334155"] : CHART_COLORS.slice(0, labels.length),
        borderWidth: 2,
        borderColor: "#131d31"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
          labels: { color: "#94a3b8", font: { size: 12, family: "-apple-system, sans-serif" } }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              if (context.label === "No Expenses Yet") return "No data recorded";
              return ` ${context.label}: ₹${formatINR(context.raw)}`;
            }
          }
        }
      },
      cutout: "65%"
    }
  });
}

function renderMonthlyTrendChart(data) {
  const canvas = document.getElementById("monthlyTrendChartCanvas");
  if (!canvas || typeof Chart === "undefined") return;

  if (state.charts.monthly) {
    state.charts.monthly.destroy();
  }

  const labels = data.map(d => d.display_name);
  const values = data.map(d => d.amount);

  state.charts.monthly = new Chart(canvas, {
    type: "line",
    data: {
      labels: labels.length ? labels : ["No data"],
      datasets: [{
        label: "Spending (INR)",
        data: values.length ? values : [0],
        borderColor: "#6366f1",
        backgroundColor: "rgba(99, 102, 241, 0.15)",
        fill: true,
        tension: 0.35,
        pointBackgroundColor: "#818cf8",
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { color: "rgba(255, 255, 255, 0.05)" }, ticks: { color: "#94a3b8" } },
        y: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: {
            color: "#94a3b8",
            callback: value => "₹" + value.toLocaleString("en-IN")
          }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` Spending: ₹${formatINR(ctx.raw)}`
          }
        }
      }
    }
  });
}

function renderDailySpendingChart(data) {
  const canvas = document.getElementById("dailyChartCanvas");
  if (!canvas || typeof Chart === "undefined") return;

  if (state.charts.daily) {
    state.charts.daily.destroy();
  }

  const labels = data.map(d => `${d.day} (${d.day_name})`);
  const values = data.map(d => d.amount);
  const todayStr = new Date().toISOString().split("T")[0];

  const barColors = data.map(d => {
    if (d.date === todayStr) return "#10b981"; // Highlight today in Emerald Green
    return "#3b82f6";
  });

  state.charts.daily = new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Daily Spend",
        data: values,
        backgroundColor: barColors,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { display: false }, ticks: { color: "#94a3b8", maxRotation: 45, autoSkip: true, maxTicksLimit: 16 } },
        y: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: {
            color: "#94a3b8",
            callback: value => "₹" + value.toLocaleString("en-IN")
          }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: ctx => data[ctx[0].dataIndex].date,
            label: ctx => ` Spent: ₹${formatINR(ctx.raw)} (${data[ctx.dataIndex].transaction_count} items)`
          }
        }
      }
    }
  });
}

function renderAnalyticsInsights(insights) {
  const grid = document.getElementById("analyticsInsightsGrid");
  grid.innerHTML = "";

  insights.forEach(item => {
    const card = document.createElement("div");
    card.className = "insight-item";
    const icon = item.type === "increase" ? "📈" : item.type === "decrease" ? "📉" : item.type === "budget" ? "⚠️" : "💡";
    card.innerHTML = `
      <div class="insight-icon-box ${item.type}">
        ${icon}
      </div>
      <div class="insight-body">
        <h4>${escapeHTML(item.title)}</h4>
        <p>${escapeHTML(item.description)}</p>
      </div>
    `;
    grid.appendChild(card);
  });
}

// ==============================================================
// VIEW 5: SAVINGS GOALS
// ==============================================================

async function loadSavingsGoals() {
  try {
    const goals = await fetchAPI("/savings-goals");
    state.savingsGoals = goals;
    renderSavingsGrid(goals);
  } catch (err) {
    showToast(err.message || "Failed to load savings goals", "danger");
  }
}

function renderSavingsGrid(goals) {
  const grid = document.getElementById("savingsGrid");
  const emptyBox = document.getElementById("savingsEmptyState");
  grid.innerHTML = "";

  if (!goals || goals.length === 0) {
    emptyBox.style.display = "block";
    return;
  }
  emptyBox.style.display = "none";

  goals.forEach(g => {
    const card = document.createElement("div");
    card.className = `goal-card ${g.is_completed ? "completed" : ""}`;

    const pct = Math.min(g.progress_percentage, 100);
    const deadlineText = g.deadline ? `Target date: ${formatDate(g.deadline)}` : "No deadline set";

    card.innerHTML = `
      <div class="goal-card-header">
        <div>
          <div class="goal-title">${escapeHTML(g.title)}</div>
          <span class="goal-category">${escapeHTML(g.category || "General")} &bull; ${deadlineText}</span>
        </div>
        <span class="kpi-badge ${g.is_completed ? "success" : "info"}">
          ${g.is_completed ? "🎉 Achieved" : `${g.progress_percentage}%`}
        </span>
      </div>

      <div class="goal-numbers">
        <div>
          <span style="font-size: 11px; color: var(--text-tertiary); display: block; text-transform: uppercase;">Saved</span>
          <span class="goal-saved">₹${formatINR(g.saved_amount)}</span>
        </div>
        <div style="text-align: right;">
          <span style="font-size: 11px; color: var(--text-tertiary); display: block; text-transform: uppercase;">Target</span>
          <span class="goal-target">₹${formatINR(g.target_amount)}</span>
        </div>
      </div>

      <div class="progress-bar-wrap" style="height: 10px;">
        <div class="progress-bar-fill ${g.is_completed ? 'normal' : 'normal'}" style="width: ${pct}%; background: ${g.is_completed ? 'var(--success)' : 'var(--primary)'};"></div>
      </div>

      <div class="goal-actions-row">
        ${!g.is_completed ? `
          <button class="btn-primary" style="flex: 1; padding: 7px 12px; font-size: 12px;" data-contribute-goal-id="${g.id}" data-goal-title="${escapeHTML(g.title)}">
            + Deposit Funds
          </button>
        ` : `
          <button class="btn-secondary" style="flex: 1; padding: 7px 12px; font-size: 12px;" disabled>
            Goal Complete!
          </button>
        `}
        <button class="action-delete-btn" title="Delete Goal" data-delete-type="goal" data-id="${g.id}" data-summary="Goal: ${escapeHTML(g.title)}">
          ✕
        </button>
      </div>
    `;

    // Hook contribute button
    const contribBtn = card.querySelector("[data-contribute-goal-id]");
    if (contribBtn) {
      contribBtn.addEventListener("click", () => {
        openContributeModal(g.id, g.title);
      });
    }

    grid.appendChild(card);
  });

  hookDeleteButtons();
}

// ==============================================================
// MODAL CONTROLLERS & FORM SUBMISSIONS
// ==============================================================

function openModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.add("open");
}

function closeModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.remove("open");
}

function openAddExpenseModal() {
  const form = document.getElementById("addExpenseForm");
  form.reset();
  document.getElementById("expDateInput").value = new Date().toISOString().split("T")[0];
  document.querySelectorAll(".chip-btn").forEach(c => c.classList.remove("selected"));
  openModal("addExpenseModal");
  setTimeout(() => document.getElementById("expAmountInput").focus(), 150);
}

function openSetBudgetModal(category = "", amount = "", month = "") {
  const form = document.getElementById("setBudgetForm");
  form.reset();
  document.getElementById("budgetCategoryInput").value = category;
  document.getElementById("budgetAmountInput").value = amount || "";
  document.getElementById("budgetMonthInput").value = month || state.selectedMonth;
  openModal("setBudgetModal");
}

function openSavingsGoalModal() {
  const form = document.getElementById("savingsGoalForm");
  form.reset();
  openModal("savingsGoalModal");
}

function openContributeModal(goalId, goalTitle) {
  const form = document.getElementById("contributeForm");
  form.reset();
  document.getElementById("contributeGoalId").value = goalId;
  document.getElementById("contributeModalTitle").textContent = `Deposit: ${goalTitle}`;
  document.getElementById("contributeDateInput").value = new Date().toISOString().split("T")[0];
  openModal("contributeModal");
}

function openDeleteModal(type, id, summary) {
  state.deleteTarget = { type, id, summary };
  document.getElementById("deleteItemSummary").textContent = summary;
  openModal("deleteModal");
}

function hookDeleteButtons() {
  document.querySelectorAll("[data-delete-type]").forEach(btn => {
    btn.onclick = (e) => {
      e.stopPropagation();
      const type = btn.getAttribute("data-delete-type");
      const id = btn.getAttribute("data-id");
      const summary = btn.getAttribute("data-summary");
      openDeleteModal(type, id, summary);
    };
  });
}

function setupPanelLinks() {
  document.querySelectorAll("[data-switch-view]").forEach(link => {
    link.onclick = (e) => {
      e.preventDefault();
      switchView(link.getAttribute("data-switch-view"));
    };
  });
}

// ==============================================================
// EVENT LISTENERS INITIALIZATION
// ==============================================================

function setupEventListeners() {
  // Navigation
  document.querySelectorAll(".sidebar-nav .nav-link, .mobile-nav-bar .mobile-nav-item").forEach(btn => {
    btn.addEventListener("click", () => {
      switchView(btn.getAttribute("data-view"));
    });
  });

  setupPanelLinks();

  // Top Month Picker
  const monthPicker = document.getElementById("globalMonthPicker");
  monthPicker.value = state.selectedMonth;
  monthPicker.addEventListener("change", (e) => {
    state.selectedMonth = e.target.value;
    // Reload active view
    switchView(state.currentView);
  });

  // Action Buttons
  document.getElementById("openAddExpenseBtn").addEventListener("click", openAddExpenseModal);
  const addBtn2 = document.getElementById("openAddExpenseBtn2");
  if (addBtn2) addBtn2.addEventListener("click", openAddExpenseModal);

  document.getElementById("openAddBudgetBtn").addEventListener("click", () => openSetBudgetModal());
  document.getElementById("openAddGoalBtn").addEventListener("click", openSavingsGoalModal);

  document.getElementById("refreshDataBtn").addEventListener("click", async () => {
    const btn = document.getElementById("refreshDataBtn");
    btn.style.transform = "rotate(180deg)";
    await switchView(state.currentView);
    setTimeout(() => { btn.style.transform = "none"; }, 300);
    showToast("Live data refreshed", "info");
  });

  // Close modals
  document.querySelectorAll("[data-close-modal]").forEach(btn => {
    btn.addEventListener("click", () => {
      closeModal(btn.getAttribute("data-close-modal"));
    });
  });

  // Modal backdrop click
  document.querySelectorAll(".modal-overlay").forEach(overlay => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.classList.remove("open");
    });
  });

  // Status pill click -> Network Modal
  document.getElementById("sidebarStatusPill").addEventListener("click", () => {
    document.getElementById("currentServerUrl").textContent = window.location.origin;
    openModal("networkModal");
  });

  // Quick Chips in Add Expense Form
  document.querySelectorAll("#addExpenseModal .chip-btn").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll("#addExpenseModal .chip-btn").forEach(c => c.classList.remove("selected"));
      chip.classList.add("selected");
      document.getElementById("expCategoryInput").value = chip.getAttribute("data-cat");
    });
  });

  // Quick Chips in Set Budget Form
  document.querySelectorAll("#setBudgetModal .budget-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll("#setBudgetModal .budget-chip").forEach(c => c.classList.remove("selected"));
      chip.classList.add("selected");
      document.getElementById("budgetCategoryInput").value = chip.getAttribute("data-cat");
    });
  });

  // Transaction Search & Filter
  const txSearch = document.getElementById("txSearchInput");
  if (txSearch) txSearch.addEventListener("input", filterAndRenderTransactions);
  const txFilter = document.getElementById("txCategoryFilter");
  if (txFilter) txFilter.addEventListener("change", filterAndRenderTransactions);

  // Form Submissions
  // 1. Add Expense
  document.getElementById("addExpenseForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const amount = parseFloat(document.getElementById("expAmountInput").value);
    const category = document.getElementById("expCategoryInput").value.trim();
    const dateVal = document.getElementById("expDateInput").value;
    const desc = document.getElementById("expDescInput").value.trim();

    if (!amount || amount <= 0) {
      showToast("Amount must be greater than zero", "danger");
      return;
    }

    try {
      document.getElementById("submitExpenseBtn").disabled = true;
      await fetchAPI("/expenses", {
        method: "POST",
        body: JSON.stringify({ amount, category, date: dateVal, description: desc })
      });
      showToast(`Recorded ₹${formatINR(amount)} for ${category}`, "success");
      closeModal("addExpenseModal");
      switchView(state.currentView);
    } catch (err) {
      showToast(err.message, "danger");
    } finally {
      document.getElementById("submitExpenseBtn").disabled = false;
    }
  });

  // 2. Set Budget
  document.getElementById("setBudgetForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const category = document.getElementById("budgetCategoryInput").value.trim();
    const month = document.getElementById("budgetMonthInput").value;
    const amount = parseFloat(document.getElementById("budgetAmountInput").value);

    if (!amount || amount <= 0) {
      showToast("Budget must be greater than zero", "danger");
      return;
    }

    try {
      document.getElementById("submitBudgetBtn").disabled = true;
      await fetchAPI("/budgets", {
        method: "POST",
        body: JSON.stringify({ category, month, amount })
      });
      showToast(`Budget set for ${category}: ₹${formatINR(amount)}`, "success");
      closeModal("setBudgetModal");
      switchView(state.currentView);
    } catch (err) {
      showToast(err.message, "danger");
    } finally {
      document.getElementById("submitBudgetBtn").disabled = false;
    }
  });

  // 3. Create Savings Goal
  document.getElementById("savingsGoalForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("goalTitleInput").value.trim();
    const target_amount = parseFloat(document.getElementById("goalTargetInput").value);
    const category = document.getElementById("goalCategoryInput").value.trim() || "General";
    const deadline = document.getElementById("goalDeadlineInput").value || null;

    try {
      document.getElementById("submitGoalBtn").disabled = true;
      await fetchAPI("/savings-goals", {
        method: "POST",
        body: JSON.stringify({ title, target_amount, category, deadline })
      });
      showToast(`Created savings goal: ${title}`, "success");
      closeModal("savingsGoalModal");
      switchView("savings");
    } catch (err) {
      showToast(err.message, "danger");
    } finally {
      document.getElementById("submitGoalBtn").disabled = false;
    }
  });

  // 4. Contribute to Savings Goal
  document.getElementById("contributeForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const goalId = document.getElementById("contributeGoalId").value;
    const amount = parseFloat(document.getElementById("contributeAmountInput").value);
    const dateVal = document.getElementById("contributeDateInput").value;
    const note = document.getElementById("contributeNoteInput").value.trim();

    try {
      document.getElementById("submitContributeBtn").disabled = true;
      await fetchAPI(`/savings-goals/${goalId}/contribute`, {
        method: "POST",
        body: JSON.stringify({ amount, date: dateVal, note })
      });
      showToast(`Added deposit of ₹${formatINR(amount)}!`, "success");
      closeModal("contributeModal");
      loadSavingsGoals();
    } catch (err) {
      showToast(err.message, "danger");
    } finally {
      document.getElementById("submitContributeBtn").disabled = false;
    }
  });

  // 5. Confirm Delete
  document.getElementById("confirmDeleteActionBtn").addEventListener("click", async () => {
    if (!state.deleteTarget) return;
    const { type, id } = state.deleteTarget;

    try {
      document.getElementById("confirmDeleteActionBtn").disabled = true;
      if (type === "expense") {
        await fetchAPI(`/expenses/${id}`, { method: "DELETE" });
      } else if (type === "budget") {
        await fetchAPI(`/budgets/${id}`, { method: "DELETE" });
      } else if (type === "goal") {
        await fetchAPI(`/savings-goals/${id}`, { method: "DELETE" });
      }
      showToast("Deleted successfully", "info");
      closeModal("deleteModal");
      state.deleteTarget = null;
      switchView(state.currentView);
    } catch (err) {
      showToast(err.message, "danger");
    } finally {
      document.getElementById("confirmDeleteActionBtn").disabled = false;
    }
  });
}

// ==============================================================
// System Status & Initialization
// ==============================================================

async function checkSystemStatus() {
  try {
    const status = await fetchAPI("/status");
    state.systemStatus = status;

    const dot = document.getElementById("sidebarStatusDot");
    const text = document.getElementById("sidebarStatusText");

    if (status.mode === "cloud" && status.cloud_configured) {
      text.textContent = "Cloud Firestore";
      dot.className = "status-dot cloud";
    } else {
      text.textContent = "Local SQLite";
      dot.className = "status-dot";
    }
  } catch (_) {
    document.getElementById("sidebarStatusText").textContent = "Offline";
  }
}

// Progressive Web App Service Worker Registration
function registerPWA() {
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/service-worker.js").catch(() => {});
    });
  }
}

// Bootstrap on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  checkSystemStatus();
  switchView("dashboard");
  registerPWA();
});
