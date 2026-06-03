# Copyright (c) 2024, Pakore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Apartment"),
			"fieldname": "apartment",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 200,
		},
		{
			"label": _("Customer Name"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Advance Amount"),
			"fieldname": "advance_amount",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Invoiced Amount"),
			"fieldname": "invoiced_amount",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Paid Amount"),
			"fieldname": "paid_amount",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Credit Note"),
			"fieldname": "credit_note",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Outstanding Amount"),
			"fieldname": "outstanding_amount",
			"fieldtype": "Currency",
			"width": 140,
		},
	]


def get_data(filters):
	conditions = get_conditions(filters)
	company_currency = frappe.db.get_value("Company", filters.get("company"), "default_currency")

	data = frappe.db.sql(
		"""
		SELECT
			cus.custom_apartment AS apartment,
			si.customer,
			COALESCE(cus.customer_name, si.customer) AS customer_name,
			SUM(si.grand_total) AS invoiced_amount,
			SUM(si.paid_amount) AS paid_amount,
			SUM(
				CASE
					WHEN si.docstatus = 1 AND si.outstanding_amount < 0
					THEN ABS(si.outstanding_amount)
					ELSE 0
				END
			) AS credit_note,
			SUM(si.outstanding_amount) AS outstanding_amount
		FROM
			`tabSales Invoice` si
		INNER JOIN
			`tabCustomer` cus ON cus.name = si.customer
		WHERE
			si.docstatus = 1
			AND si.company = %(company)s
			AND si.posting_date <= %(report_date)s
			{conditions}
		GROUP BY
			si.customer
		HAVING
			ROUND(SUM(si.outstanding_amount), 2) != 0
		ORDER BY
			cus.custom_apartment ASC, si.customer ASC
		""".format(conditions=conditions),
		filters,
		as_dict=1,
	)

	# Add advance amounts per customer
	advance_map = get_advance_amounts(filters)
	for row in data:
		row.advance_amount = advance_map.get(row.customer, 0)

	return data


def get_conditions(filters):
	conditions = []

	if filters.get("cost_centers_include"):
		cc_list = "', '".join(filters["cost_centers_include"])
		conditions.append(
			f"""AND si.name IN (
				SELECT parent FROM `tabSales Invoice Item`
				WHERE cost_center IN ('{cc_list}')
			)"""
		)

	if filters.get("cost_centers_exclude"):
		cc_list = "', '".join(filters["cost_centers_exclude"])
		conditions.append(
			f"""AND si.name NOT IN (
				SELECT parent FROM `tabSales Invoice Item`
				WHERE cost_center IN ('{cc_list}')
			)"""
		)

	return " ".join(conditions)


def get_advance_amounts(filters):
	"""Get total advance payments per customer."""
	data = frappe.db.sql(
		"""
		SELECT
			jei.party AS customer,
			SUM(jei.credit - jei.debit) AS advance_amount
		FROM
			`tabJournal Entry Account` jei
		INNER JOIN
			`tabJournal Entry` je ON je.name = jei.parent
		WHERE
			je.docstatus = 1
			AND je.posting_date <= %(report_date)s
			AND jei.party_type = 'Customer'
			AND jei.reference_type IS NULL
			AND jei.is_advance = 'Yes'
			AND je.company = %(company)s
		GROUP BY
			jei.party
		""",
		{"company": filters.get("company"), "report_date": filters.get("report_date")},
		as_dict=1,
	)

	return {row.customer: row.advance_amount for row in data}
