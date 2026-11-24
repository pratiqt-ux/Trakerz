"""
Smart Expense Categorization Service for Milestone 5.
Uses deterministic keyword matching against existing Trakerz categories,
with optional Gemini AI refinement when configured and needed.
"""
import re
from typing import List, Dict, Tuple, Optional
import httpx
from app.database.base import BaseExpenseDatabase
from app.config import settings
from app.models.ai import CategorizeResponse


# Canonical keyword dictionary mapped to standard Trakerz categories
KEYWORD_RULES: Dict[str, List[str]] = {
    "Food": [
        "dominos", "pizza", "burger", "swiggy", "zomato", "biryani", "lunch",
        "dinner", "breakfast", "cafe", "coffee", "tea", "chai", "canteen",
        "restaurant", "snack", "snacks", "maggi", "dosa", "samosa", "kfc",
        "mcdonald", "subway", "momos", "bakery", "ice cream", "sweet", "thali",
        "eating", "meal", "paratha", "idli", "noodles", "pasta", "shawarma"
    ],
    "Travel": [
        "uber", "ola", "rapido", "metro", "bus", "auto", "rickshaw", "train",
        "flight", "fuel", "petrol", "diesel", "cab", "taxi", "ticket", "irctc",
        "commute", "parking", "toll", "redbus", "travel", "ride", "rick", "pass"
    ],
    "Groceries": [
        "blinkit", "zepto", "instamart", "bigbasket", "dmart", "milk", "bread",
        "vegetable", "vegetables", "fruit", "fruits", "rice", "grocery",
        "groceries", "supermarket", "kirana", "eggs", "atta", "oil", "paneer"
    ],
    "Bills": [
        "electricity", "water", "wifi", "broadband", "airtel", "jio", "vi",
        "recharge", "rent", "gas", "cylinder", "bill", "maintenance", "pg",
        "hostel", "accommodation", "room", "mobile", "postpaid", "dth"
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "ajio", "meesho", "shoes", "shirt",
        "clothes", "jeans", "tshirt", "electronics", "headphone", "headphones",
        "charger", "watch", "mall", "bag", "jacket", "shopping", "nike", "zara"
    ],
    "Entertainment": [
        "movie", "movies", "pvr", "inox", "bookmyshow", "netflix", "spotify",
        "prime", "hotstar", "game", "gaming", "concert", "bowling", "outing",
        "cinema", "ticket", "youtube", "arcade", "club"
    ],
    "Health": [
        "pharmacy", "medicine", "medicines", "doctor", "hospital", "clinic",
        "apollo", "medplus", "pharmeasy", "1mg", "dental", "checkup", "gym",
        "protein", "vitamin", "tablet", "medical", "health"
    ],
    "Education": [
        "book", "books", "notebook", "pen", "stationery", "xerox", "print",
        "printing", "tuition", "course", "udemy", "coursera", "exam", "fee",
        "fees", "college", "textbook", "lab", "calculator"
    ]
}

# Alias map so "Transport" matches "Travel" or user's existing category cleanly
CATEGORY_ALIASES: Dict[str, List[str]] = {
    "Travel": ["travel", "transport", "transportation", "commute"],
    "Food": ["food", "dining", "eating out", "meals"],
    "Bills": ["bills", "utilities", "rent", "accommodation"],
    "Entertainment": ["entertainment", "movies", "fun"],
    "Health": ["health", "medical", "fitness"],
    "Education": ["education", "college", "study"],
    "Groceries": ["groceries", "grocery"],
    "Shopping": ["shopping", "clothes", "apparel"]
}


class CategorizationService:
    def __init__(self, db: BaseExpenseDatabase):
        self.db = db

    def _get_existing_categories(self) -> List[str]:
        expenses = self.db.get_expenses()
        cats = []
        seen = set()
        for e in expenses:
            c = (e.get("category") or "").strip()
            if c and c.lower() not in seen:
                seen.add(c.lower())
                cats.append(c)
        return cats

    def _resolve_to_existing_category(self, canonical_cat: str, existing_cats: List[str]) -> str:
        """Prefer user's existing category name if it matches an alias (avoids duplicate categories)."""
        aliases = CATEGORY_ALIASES.get(canonical_cat, [canonical_cat.lower()])
        for existing in existing_cats:
            if existing.lower() in aliases:
                return existing
        return canonical_cat

    def _clean_description(self, raw_desc: str, amount: Optional[float] = None) -> str:
        """Clean trailing numbers (e.g., 'Dominos pizza 450' -> 'Dominos pizza')."""
        cleaned = raw_desc.strip()
        # Strip trailing standalone number if user typed amount inside description
        cleaned = re.sub(r"\s+(?:rs\.?|inr|₹)?\s*\d+(?:\.\d{1,2})?\s*$", "", cleaned, flags=re.IGNORECASE).strip()
        if not cleaned:
            cleaned = raw_desc.strip()
        # Capitalize first letter nicely if all lowercase
        if cleaned and cleaned.islower():
            cleaned = cleaned[0].upper() + cleaned[1:]
        return cleaned[:255]

    def _rule_based_match(self, text: str) -> Tuple[Optional[str], str, str]:
        lower = text.lower()
        scores: Dict[str, List[str]] = {}

        for cat, keywords in KEYWORD_RULES.items():
            matched = []
            for kw in keywords:
                # Word boundary check for short words, substring for longer
                if len(kw) <= 3:
                    if re.search(rf"\b{re.escape(kw)}\b", lower):
                        matched.append(kw)
                else:
                    if kw in lower:
                        matched.append(kw)
            if matched:
                scores[cat] = matched

        if not scores:
            return None, "low", "No matching keyword found in description."

        best_cat = max(scores.keys(), key=lambda c: len(scores[c]))
        matched_kws = scores[best_cat]
        conf = "high" if len(matched_kws) >= 1 else "medium"
        reason = f"Matched keyword(s): {', '.join(matched_kws[:3])}"
        return best_cat, conf, reason

    async def suggest_category(self, description: str, amount: Optional[float] = None) -> CategorizeResponse:
        existing_cats = self._get_existing_categories()
        cleaned_desc = self._clean_description(description, amount)

        # 1. Try fast local rule-based categorization
        matched_cat, confidence, reason = self._rule_based_match(description)
        if matched_cat:
            final_cat = self._resolve_to_existing_category(matched_cat, existing_cats)
            return CategorizeResponse(
                suggested_category=final_cat,
                suggested_description=cleaned_desc,
                confidence=confidence,
                source="rule_based",
                reason=reason
            )

        # 2. If unrecognized locally and Gemini API key is configured, ask AI
        api_key = settings.GEMINI_API_KEY
        if api_key and api_key != "your_gemini_api_key_here":
            ai_cat = await self._ai_categorize(cleaned_desc, existing_cats, api_key)
            if ai_cat:
                return CategorizeResponse(
                    suggested_category=ai_cat,
                    suggested_description=cleaned_desc,
                    confidence="medium",
                    source="ai",
                    reason="Suggested by Gemini AI based on transaction context"
                )

        # 3. Safe fallback when unrecognized and AI is unavailable
        fallback = self._resolve_to_existing_category("Other", existing_cats)
        return CategorizeResponse(
            suggested_category=fallback,
            suggested_description=cleaned_desc,
            confidence="low",
            source="rule_based",
            reason="Unrecognized description; defaulted to Other (you can change it manually)"
        )

    async def _ai_categorize(self, description: str, existing_cats: List[str], api_key: str) -> Optional[str]:
        standard_cats = ["Food", "Travel", "Groceries", "Bills", "Shopping", "Entertainment", "Health", "Education", "Other"]
        all_choices = list(dict.fromkeys(existing_cats + standard_cats))
        prompt = (
            f"Categorize this personal expense description into exactly ONE category from this list: {', '.join(all_choices)}.\n"
            f"Description: \"{description}\"\n"
            "Reply with ONLY the single category name, nothing else."
        )
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(
                    url,
                    headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                    json={"contents": [{"parts": [{"text": prompt}]}]}
                )
                if res.status_code == 200:
                    data = res.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    # Match against allowed choices
                    for choice in all_choices:
                        if choice.lower() == text.lower() or choice.lower() in text.lower():
                            return choice
        except Exception:
            pass
        return None
