# Copyright (c) 2024, Pakore and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.party import get_partywise_advanced_payment_amount


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
	company = filters.get("company")
	report_date = filters.get("report_date")

	# Get all receivable accounts for this company
	receivable_accounts = frappe.db.get_all(
		"Account",
		filters={"company": company, "account_type": "Receivable", "is_group": 0},
		pluck="name",
	)

	if not receivable_accounts:
		return []

	# Query Payment Ledger Entry for all customer transactions
	ple_data = frappe.db.sql(
		"""
		SELECT
			ple.party AS customer,
			ple.voucher_type,
			ple.voucher_no,
			ple.against_voucher_type,
			ple.against_voucher_no,
			ple.amount,
			ple.account
		FROM
			`tabPayment Ledger Entry` ple
		WHERE
			ple.company = %(company)s
			AND ple.posting_date <= %(report_date)s
			AND ple.delinked = 0
			AND ple.party_type = 'Customer'
			AND ple.account IN %(accounts)s
			{conditions}
		ORDER BY
			ple.party, ple.voucher_no
		""".format(conditions=conditions),
		{
			"company": company,
			"report_date": report_date,
			"accounts": receivable_accounts,
		},
		as_dict=1,
	)

	# Build voucher-level balances (invoiced, paid, credit_note per voucher)
	voucher_balance = {}
	for ple in ple_data:
		key = (ple.account, ple.voucher_type, ple.voucher_no, ple.customer)
		if key not in voucher_balance:
			voucher_balance[key] = {
				"invoiced": 0.0,
				"paid": 0.0,
				"credit_note": 0.0,
			}

		row = voucher_balance[key]
		amt = ple.amount

		if amt > 0:
			if ple.voucher_type in ("Journal Entry", "Payment Entry") and ple.voucher_no != ple.against_voucher_no:
				row["paid"] += amt
			else:
				row["invoiced"] += amt
		else:
			if ple.voucher_type in ("Sales Invoice", "Purchase Invoice"):
				if ple.voucher_no == ple.against_voucher_no:
					row["paid"] -= amt
				else:
					row["credit_note"] -= amt
			else:
				row["paid"] -= amt

	# Aggregate per customer
	customer_totals = {}
	for (account, vtype, vno, customer), bal in voucher_balance.items():
		if customer not in customer_totals:
			customer_totals[customer] = {
				"invoiced": 0.0,
				"paid": 0.0,
				"credit_note": 0.0,
			}
		ct = customer_totals[customer]
		ct["invoiced"] += bal["invoiced"]
		ct["paid"] += bal["paid"]
		ct["credit_note"] += bal["credit_note"]

	# Get advance amounts
	advance_map = get_partywise_advanced_payment_amount(
		["Customer"],
		report_date,
		filters.get("show_future_payments"),
		company,
	)

	# Get customer details (apartment, customer_name)
	customer_details = get_customer_details(list(customer_totals.keys()))

	# Build final rows
	currency_precision = frappe.db.get_single_value("System Settings", "currency_precision") or 2
	data = []
	for customer, bal in customer_totals.items():
		outstanding = bal["invoiced"] - bal["paid"] - bal["credit_note"]

		advance = advance_map.get(customer, 0)
		paid_excluding_advance = bal["paid"] - advance
		if paid_excluding_advance < 0:
			paid_excluding_advance = 0.0

		details = customer_details.get(customer, {})
		data.append({
			"apartment": details.get("custom_apartment", ""),
			"customer": customer,
			"advance_amount": advance,
			"invoiced_amount": bal["invoiced"],
			"paid_amount": paid_excluding_advance,
			"credit_note": bal["credit_note"],
			"outstanding_amount": outstanding,
		})

	data.sort(key=lambda r: (r["apartment"] or "", r["customer"] or ""))
	return data


def get_customer_details(customers):
	"""Get apartment and customer_name for a list of customers."""
	if not customers:
		return {}
	data = frappe.db.sql(
		"""
		SELECT name, custom_apartment, customer_name
		FROM `tabCustomer`
		WHERE name IN %s
		""",
		(customers,),
		as_dict=1,
	)
	return {d.name: d for d in data}


def get_conditions(filters):
	conditions = []

	if filters.get("cost_centers_include"):
		cc_list = "', '".join(filters["cost_centers_include"])
		conditions.append(
			f"""AND (
				ple.voucher_no IN (
					SELECT parent FROM `tabSales Invoice Item`
					WHERE cost_center IN ('{cc_list}')
				)
				OR ple.against_voucher_no IN (
					SELECT parent FROM `tabSales Invoice Item`
					WHERE cost_center IN ('{cc_list}')
				)
			)"""
		)

	if filters.get("cost_centers_exclude"):
		cc_list = "', '".join(filters["cost_centers_exclude"])
		conditions.append(
			f"""AND ple.voucher_no NOT IN (
				SELECT parent FROM `tabSales Invoice Item`
				WHERE cost_center IN ('{cc_list}')
			)
			AND ple.against_voucher_no NOT IN (
				SELECT parent FROM `tabSales Invoice Item`
				WHERE cost_center IN ('{cc_list}')
			)"""
		)

	return " ".join(conditions)
