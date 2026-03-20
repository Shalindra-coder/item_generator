# Copyright (c) 2024, Pratul Tiwari and contributors
# For license information, please see license.txt

"""Add FULLTEXT index on Item for similar item detection (item_code, item_name, description)."""

from __future__ import unicode_literals

import frappe


def execute():
	"""Add FULLTEXT index on tabItem if it does not exist."""
	index_name = "item_similarity_fulltext"

	# Check if FULLTEXT index already exists
	# tabItem is the actual table name in Frappe
	existing_indexes = frappe.db.sql(
		"""
		SELECT INDEX_NAME
		FROM information_schema.STATISTICS
		WHERE TABLE_SCHEMA = DATABASE()
			AND TABLE_NAME = 'tabItem'
			AND INDEX_NAME = %s
		""",
		(index_name,),
		as_dict=True,
	)

	if existing_indexes:
		return  # Index already exists

	# Add FULLTEXT index (MariaDB/MySQL)
	# Note: FULLTEXT requires columns to be CHAR, VARCHAR, or TEXT
	frappe.db.sql(
		"""
		ALTER TABLE `tabItem`
		ADD FULLTEXT INDEX `item_similarity_fulltext` (item_code, item_name, description)
		"""
	)
	frappe.db.commit()
