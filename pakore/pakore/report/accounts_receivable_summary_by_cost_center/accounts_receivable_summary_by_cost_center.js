// Copyright (c) 2024, Pakore and contributors
// For license information, please see license.txt

frappe.query_reports["Accounts Receivable Summary by Cost Center"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "report_date",
			label: __("Posting Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "cost_centers_include",
			label: __("Cost Centers (Include)"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Cost Center", txt);
			},
		},
		{
			fieldname: "cost_centers_exclude",
			label: __("Cost Centers (Exclude)"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Cost Center", txt);
			},
		},
	],
};
