/**
 * Trakerz Mobile Frontend Client - Milestone 3
 * Handles API communication, responsive UI rendering, PWA lifecycle, and user interactions.
 */

// Category emoji dictionary for instant recognition
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
  education: "📚",
  college: "🎓",
  groceries: "🥦",
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

// Indian Rupee currency formatter
function formatINR(amount) {
  const num = Number(amount) || 0;
  return num.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

// Date formatter
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

// Global Application State
const state = {
  expenses: [],
  filteredExpenses: [],
  summary: null,
  categories: [],
  monthly: [],
  systemStatus: null,
  selectedFilter: "ALL",
  searchQuery: "",
  deletingExpenseId: null
};

// ==============================================================
// DOM Element References
// ==============================================================
const DOM = {
  statusPill: document.getElementById("statusPill"),
  statusDot: document.getElementById("statusDot"),
  statusText: document.getElementById("statusText"),
  refreshBtn: document.getElementById("refreshBtn"),
  infoBtn: document.getElementById("infoBtn"),
  
  // Dashboard
  totalAmountText: document.getElementById("totalAmountText"),
  monthAmountText: document.getElementById("monthAmountText"),
  totalCountText: document.getElementById("totalCountText"),
  
  // Categories
  categoryList: document.getElementById("categoryList"),
  
  // History
  filterBar: document.getElementById("filterBar"),
  searchInput: document.getElementById("searchInput"),
  expenseList: document.getElementById("expenseList"),
  emptyState: document.getElementById("emptyState"),
  
  // Add Expense Modal
  addModal: document.getElementById("addModal"),
  closeAddModalBtn: document.getElementById("closeAddModalBtn"),
  cancelAddBtn: document.getElementById("cancelAddBtn"),
  openAddModalBtn: document.getElementById("openAddModalBtn"),
  fabBtn: document.getElementById("fabBtn"),
  expenseForm: document.getElementById("expenseForm"),
  inputAmount: document.getElementById("inputAmount"),
  inputCategory: document.getElementById("inputCategory"),
  inputDate: document.getElementById("inputDate"),
  inputDesc: document.getElementById("inputDesc"),
  submitExpenseBtn: document.getElementById("submitExpenseBtn"),
  quickCatChips: document.querySelectorAll(".cat-chip"),
  
  // Delete Modal
  deleteModal: document.getElementById("deleteModal"),
  closeDeleteModalBtn: document.getElementById("closeDeleteModalBtn"),
  cancelDeleteBtn: document.getElementById("cancelDeleteBtn"),
  confirmDeleteBtn: document.getElementById("confirmDeleteBtn"),
  deleteExpenseSummary: document.getElementById("deleteExpenseSummary"),

  // Network Info Modal
  networkModal: document.getElementById("networkModal"),
  closeNetworkModalBtn: document.getElementById("closeNetworkModalBtn"),
  closeNetworkBtn: document.getElementById("closeNetworkBtn"),
  currentUrlDisplay: document.getElementById("currentUrlDisplay"),

  // Toasts
  toastContainer: document.getElementById("toastContainer")
};

// ==============================================================
// API Client Methods
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
        const errorData = await res.json();
        if (errorData.detail) {
          errorMsg = Array.isArray(errorData.detail)
            ? errorData.detail.map(d => d.msg || d).join(", ")
            : errorData.detail;
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

// Show feedback toast
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${type === "success" ? "✓" : type === "error" ? "⚠️" : "ℹ️"}</span> <span>${message}</span>`;
  DOM.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(-10px)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

// ==============================================================
// App Data Loading & Rendering
// ==============================================================

async function loadAllData() {
  try {
    const [status, summary, categories, monthly, expenses] = await Promise.all([
      fetchAPI("/status"),
      fetchAPI("/analytics/total"),
      fetchAPI("/analytics/categories"),
      fetchAPI("/analytics/monthly"),
      fetchAPI("/expenses")
    ]);

    state.systemStatus = status;
    state.summary = summary;
    state.categories = categories;
    state.monthly = monthly;
    state.expenses = expenses;

    renderSystemStatus();
    renderDashboard();
    renderCategoryBreakdown();
    renderFilterChips();
    applyFilters();
  } catch (err) {
    showToast(err.message || "Failed to load expenses", "error");
  }
}

function renderSystemStatus() {
  if (!state.systemStatus) return;
  const { mode, database, cloud_configured } = state.systemStatus;

  if (mode === "cloud" && cloud_configured) {
    DOM.statusText.textContent = "☁️ Cloud Firestore";
    DOM.statusDot.className = "status-dot cloud";
  } else {
    DOM.statusText.textContent = "🟢 Local SQLite";
    DOM.statusDot.className = "status-dot";
  }
}

function renderDashboard() {
  if (!state.summary) return;
  DOM.totalAmountText.textContent = formatINR(state.summary.total_amount);
  DOM.monthAmountText.textContent = `₹${formatINR(state.summary.current_month_total)}`;
  DOM.totalCountText.textContent = `${state.summary.expense_count} entries`;
}

function renderCategoryBreakdown() {
  DOM.categoryList.innerHTML = "";

  if (!state.categories || state.categories.length === 0) {
    DOM.categoryList.innerHTML = `
      <div style="color: var(--text-muted); font-size: 13px; text-align: center; padding: 12px 0;">
        No spending categories recorded yet.
      </div>`;
    return;
  }

  state.categories.forEach((cat) => {
    const emoji = getCategoryEmoji(cat.category);
    const card = document.createElement("div");
    card.className = "category-card";
    card.innerHTML = `
      <div class="category-info-row">
        <div class="category-name-wrap">
          <span class="category-emoji">${emoji}</span>
          <span>${escapeHTML(cat.category)}</span>
        </div>
        <div class="category-amount-wrap">
          <div class="category-amount">₹${formatINR(cat.total)}</div>
          <div class="category-count">${cat.percentage}% (${cat.count} ${cat.count === 1 ? 'item' : 'items'})</div>
        </div>
      </div>
      <div class="progress-track">
        <div class="progress-fill" style="width: ${Math.min(cat.percentage, 100)}%;"></div>
      </div>
    `;
    DOM.categoryList.appendChild(card);
  });
}

function renderFilterChips() {
  const categories = ["ALL", ...new Set(state.expenses.map(e => e.category))];
  
  DOM.filterBar.innerHTML = "";
  categories.forEach(cat => {
    const chip = document.createElement("button");
    chip.className = `filter-chip ${state.selectedFilter === cat ? "active" : ""}`;
    chip.textContent = cat === "ALL" ? "All" : `${getCategoryEmoji(cat)} ${cat}`;
    chip.addEventListener("click", () => {
      state.selectedFilter = cat;
      renderFilterChips();
      applyFilters();
    });
    DOM.filterBar.appendChild(chip);
  });
}

function applyFilters() {
  const query = state.searchQuery.toLowerCase().trim();

  state.filteredExpenses = state.expenses.filter(e => {
    const matchCategory = state.selectedFilter === "ALL" || e.category.toLowerCase() === state.selectedFilter.toLowerCase();
    const matchSearch = !query || 
      e.category.toLowerCase().includes(query) || 
      (e.description && e.description.toLowerCase().includes(query)) ||
      String(e.amount).includes(query);
    return matchCategory && matchSearch;
  });

  renderExpensesList();
}

function renderExpensesList() {
  DOM.expenseList.innerHTML = "";

  if (state.filteredExpenses.length === 0) {
    DOM.emptyState.style.display = "block";
    return;
  }

  DOM.emptyState.style.display = "none";

  state.filteredExpenses.forEach(exp => {
    const emoji = getCategoryEmoji(exp.category);
    const item = document.createElement("div");
    item.className = "expense-item";
    item.innerHTML = `
      <div class="expense-left">
        <div class="expense-icon-badge">${emoji}</div>
        <div class="expense-details">
          <div class="expense-category-name">${escapeHTML(exp.category)}</div>
          <div class="expense-desc">${escapeHTML(exp.description || "No description")}</div>
          <div class="expense-date">${formatDate(exp.date)}</div>
        </div>
      </div>
      <div class="expense-right">
        <div class="expense-price">₹${formatINR(exp.amount)}</div>
        <button class="delete-btn" title="Delete Expense" aria-label="Delete" data-id="${exp.id}">
          ✕
        </button>
      </div>
    `;

    // Hook up delete button
    const deleteBtn = item.querySelector(".delete-btn");
    deleteBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      openDeleteConfirmation(exp);
    });

    DOM.expenseList.appendChild(item);
  });
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

// ==============================================================
// Modal Actions
// ==============================================================

function openAddModal() {
  // Reset form
  DOM.expenseForm.reset();
  const today = new Date().toISOString().split("T")[0];
  DOM.inputDate.value = today;

  // Unselect category chips
  DOM.quickCatChips.forEach(chip => chip.classList.remove("selected"));

  DOM.addModal.classList.add("open");
  setTimeout(() => DOM.inputAmount.focus(), 150);
}

function closeAddModal() {
  DOM.addModal.classList.remove("open");
}

function openDeleteConfirmation(expense) {
  state.deletingExpenseId = expense.id;
  DOM.deleteExpenseSummary.textContent = `${expense.category}: ₹${formatINR(expense.amount)} (${formatDate(expense.date)})`;
  DOM.deleteModal.classList.add("open");
}

function closeDeleteModal() {
  state.deletingExpenseId = null;
  DOM.deleteModal.classList.remove("open");
}

function openNetworkModal() {
  const origin = window.location.origin;
  DOM.currentUrlDisplay.textContent = origin;
  DOM.networkModal.classList.add("open");
}

function closeNetworkModal() {
  DOM.networkModal.classList.remove("open");
}

// ==============================================================
// Event Listeners & Form Submissions
// ==============================================================

function setupEventListeners() {
  // Open / Close Modals
  DOM.openAddModalBtn.addEventListener("click", openAddModal);
  DOM.fabBtn.addEventListener("click", openAddModal);
  DOM.closeAddModalBtn.addEventListener("click", closeAddModal);
  DOM.cancelAddBtn.addEventListener("click", closeAddModal);

  DOM.closeDeleteModalBtn.addEventListener("click", closeDeleteModal);
  DOM.cancelDeleteBtn.addEventListener("click", closeDeleteModal);

  DOM.statusPill.addEventListener("click", openNetworkModal);
  DOM.infoBtn.addEventListener("click", openNetworkModal);
  DOM.closeNetworkModalBtn.addEventListener("click", closeNetworkModal);
  DOM.closeNetworkBtn.addEventListener("click", closeNetworkModal);

  // Close modals on overlay backdrop click
  [DOM.addModal, DOM.deleteModal, DOM.networkModal].forEach(modal => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.remove("open");
      }
    });
  });

  // Refresh
  DOM.refreshBtn.addEventListener("click", async () => {
    DOM.refreshBtn.style.transform = "rotate(180deg)";
    await loadAllData();
    setTimeout(() => {
      DOM.refreshBtn.style.transform = "none";
    }, 300);
    showToast("Refreshed data", "info");
  });

  // Quick Category Chips
  DOM.quickCatChips.forEach(chip => {
    chip.addEventListener("click", () => {
      DOM.quickCatChips.forEach(c => c.classList.remove("selected"));
      chip.classList.add("selected");
      DOM.inputCategory.value = chip.getAttribute("data-cat");
    });
  });

  // Manual typing in category input deselects quick chips if not matching
  DOM.inputCategory.addEventListener("input", (e) => {
    const val = e.target.value.toLowerCase().trim();
    DOM.quickCatChips.forEach(chip => {
      if (chip.getAttribute("data-cat").toLowerCase() === val) {
        chip.classList.add("selected");
      } else {
        chip.classList.remove("selected");
      }
    });
  });

  // Search filter input
  DOM.searchInput.addEventListener("input", (e) => {
    state.searchQuery = e.target.value;
    applyFilters();
  });

  // Add Expense Form Submission
  DOM.expenseForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const amount = parseFloat(DOM.inputAmount.value);
    const category = DOM.inputCategory.value.trim();
    const dateVal = DOM.inputDate.value;
    const desc = DOM.inputDesc.value.trim();

    // Validations
    if (!amount || amount <= 0) {
      showToast("Amount must be greater than zero", "error");
      DOM.inputAmount.focus();
      return;
    }
    if (!category) {
      showToast("Please select or enter a category", "error");
      DOM.inputCategory.focus();
      return;
    }
    if (!dateVal) {
      showToast("Please choose a valid date", "error");
      return;
    }

    try {
      DOM.submitExpenseBtn.disabled = true;
      DOM.submitExpenseBtn.textContent = "Saving...";

      await fetchAPI("/expenses", {
        method: "POST",
        body: JSON.stringify({
          amount: amount,
          category: category,
          date: dateVal,
          description: desc
        })
      });

      showToast(`Added ₹${formatINR(amount)} for ${category}`, "success");
      closeAddModal();
      await loadAllData();
    } catch (err) {
      showToast(err.message || "Failed to add expense", "error");
    } finally {
      DOM.submitExpenseBtn.disabled = false;
      DOM.submitExpenseBtn.textContent = "Save Expense";
    }
  });

  // Confirm Delete
  DOM.confirmDeleteBtn.addEventListener("click", async () => {
    if (!state.deletingExpenseId) return;

    try {
      DOM.confirmDeleteBtn.disabled = true;
      DOM.confirmDeleteBtn.textContent = "Deleting...";

      await fetchAPI(`/expenses/${state.deletingExpenseId}`, {
        method: "DELETE"
      });

      showToast("Expense deleted", "info");
      closeDeleteModal();
      await loadAllData();
    } catch (err) {
      showToast(err.message || "Failed to delete expense", "error");
    } finally {
      DOM.confirmDeleteBtn.disabled = false;
      DOM.confirmDeleteBtn.textContent = "Delete Expense";
    }
  });
}

// ==============================================================
// PWA Service Worker Registration
// ==============================================================
function registerServiceWorker() {
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker
        .register("/service-worker.js")
        .then((reg) => {
          console.log("[Trakerz] Service Worker registered with scope:", reg.scope);
        })
        .catch((err) => {
          console.log("[Trakerz] Service Worker registration skipped or failed:", err);
        });
    });
  }
}

// ==============================================================
// Bootstrap
// ==============================================================
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  loadAllData();
  registerServiceWorker();
});
