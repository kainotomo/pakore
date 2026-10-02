# Copyright (c) 2024, KAINOTOMO PH LTD and Contributors
# See license.txt

from frappe.tests.utils import FrappeTestCase

from pakore.pakore.report.accounts_receivable_summary_by_cost_center.accounts_receivable_summary_by_cost_center import (
	get_conditions,
)


class TestAccountsReceivableSummaryByCostCenter(FrappeTestCase):
	def test_disabled_customers_excluded_by_default(self):
		self.assertIn("disabled = 1", get_conditions({}))

	def test_disabled_customers_excluded_when_flag_absent_from_filters(self):
		self.assertIn("disabled = 1", get_conditions({"company": "Test Company"}))

	def test_disabled_customers_included_when_flagged(self):
		self.assertNotIn(
			"disabled = 1", get_conditions({"include_disabled_customers": 1})
		)

	def test_string_zero_still_excludes_disabled_customers(self):
		self.assertIn(
			"disabled = 1", get_conditions({"include_disabled_customers": "0"})
		)

	def test_cost_centers_include_still_applied_alongside_exclusion(self):
		conditions = get_conditions(
			{"include_disabled_customers": 1, "cost_centers_include": ["Main"]}
		)
		self.assertNotIn("disabled = 1", conditions)
		self.assertIn("'Main'", conditions)
