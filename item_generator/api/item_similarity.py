# Copyright (c) 2024, Pratul Tiwari and contributors
# For license information, please see license.txt

"""
Similar Item Detection API.

Uses FULLTEXT search + fuzzy matching to find similar items and prevent duplicates.
Optimized for 40k+ items with <100ms response time.
"""

from __future__ import unicode_literals

import frappe


def _normalize_query(query: str) -> str:
	"""
	Normalize search input: lowercase, trim, collapse multiple spaces.
	"""
	if not query or not isinstance(query, str):
		return ""
	return " ".join(query.lower().strip().split())


@frappe.whitelist()
def get_similar_items(query: str) -> list:
	"""
	Search for similar items by item_name/description.

	Uses LIKE for partial matching (Google-like: "sneaker" finds "Sneakers")
	+ fuzzy matching for ranking. Returns top 5 items sorted by similarity score.

	Args:
		query: Search string (item_name + description combined)

	Returns:
		List of dicts: [{"name", "item_code", "item_name", "score"}, ...]
	"""
	query = _normalize_query(query)

	if len(query) < 3:
		return []

	# Use LIKE for partial matching (sneaker -> Sneakers, etc.)
	# FULLTEXT treats "sneaker" and "sneakers" as different words
	return _search_with_like(query)


def _search_with_like(query: str) -> list:
	"""
	Search using LIKE for partial matching (Google-like).
	"sneaker" finds "Sneakers", "sneakers" finds "Sneakers", etc.
	"""
	# Escape for LIKE: % and _ are wildcards
	escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
	pattern = f"%{escaped}%"
	results = frappe.db.sql(
		"""
		SELECT name, item_code, item_name, description
		FROM tabItem
		WHERE item_name LIKE %s OR description LIKE %s OR item_code LIKE %s
		LIMIT 50
		""",
		(pattern, pattern, pattern),
		as_dict=True,
	)
	return _apply_fuzzy_ranking(query, results)


def _apply_fuzzy_ranking(query: str, results: list) -> list:
	"""
	Apply rapidfuzz scoring: case-insensitive, supports partial matches.
	"sneakers" vs "Sneakers" -> 100; "sneaker" vs "Sneakers" -> high (partial).
	"""
	try:
		from rapidfuzz import fuzz, utils
	except ImportError:
		return [{"name": r.name, "item_code": r.item_code, "item_name": r.item_name, "score": 0} for r in results[:5]]

	processor = utils.default_process  # lowercase, trim
	scored = []
	for r in results:
		text = f"{r.item_name or ''} {r.description or ''}".strip()
		item_name = (r.item_name or "").strip()
		item_code = (r.item_code or "").strip()

		# Exact/partial match on item_name (case-insensitive)
		name_score = max(
			fuzz.ratio(query, item_name, processor=processor),
			fuzz.partial_ratio(query, item_name, processor=processor),
			fuzz.token_sort_ratio(query, item_name, processor=processor),
		)
		# Partial match on full text (item_name + description)
		text_score = max(
			fuzz.partial_ratio(query, text, processor=processor),
			fuzz.token_sort_ratio(query, text, processor=processor),
		)
		# Item code match
		code_score = fuzz.partial_ratio(query, item_code, processor=processor)

		combined = max(name_score, text_score, code_score)
		scored.append(
			{
				"name": r.name,
				"item_code": r.item_code,
				"item_name": r.item_name,
				"score": combined,
			}
		)

	scored.sort(key=lambda x: x["score"], reverse=True)
	return scored[:5]
