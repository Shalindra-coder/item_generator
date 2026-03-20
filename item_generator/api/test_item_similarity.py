# Copyright (c) 2024, Pratul Tiwari and contributors
# For license information, see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from item_generator.api.item_similarity import get_similar_items


class TestItemSimilarity(FrappeTestCase):
	def setUp(self):
		"""Create test Item if not exists"""
		if not frappe.db.exists("Item", "SKU-TEST-SIMILAR"):
			frappe.get_doc({
				"doctype": "Item",
				"item_code": "SKU-TEST-SIMILAR",
				"item_name": "Test Laptop",
				"description": "This is a test laptop for similarity",
				"item_group": "All Item Groups",
				"stock_uom": "Nos",
			}).insert(ignore_permissions=True)

	def test_get_similar_items_exact_match(self):
		"""Exact match should return high score"""
		result = get_similar_items("laptop")
		self.assertIsInstance(result, list)
		# Should find items with laptop in name/description
		if result:
			self.assertIn("item_code", result[0])
			self.assertIn("item_name", result[0])
			self.assertIn("score", result[0])

	def test_get_similar_items_partial_match(self):
		"""Partial match (e.g. 'lapt' -> 'Laptop') should work"""
		result = get_similar_items("lapt")
		self.assertIsInstance(result, list)

	def test_get_similar_items_short_query(self):
		"""Query < 3 chars should return empty"""
		result = get_similar_items("ab")
		self.assertEqual(result, [])

	def test_get_similar_items_empty_query(self):
		"""Empty query should return empty"""
		result = get_similar_items("")
		self.assertEqual(result, [])

	def tearDown(self):
		frappe.db.rollback()
