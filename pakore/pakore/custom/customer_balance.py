import frappe
from erpnext.accounts.party import get_dashboard_info

@frappe.whitelist()
def get_customer_balance():
    user = frappe.session.user
    contact = frappe.get_value("Contact", {"user": user}, "name")
    customer = frappe.get_value("Customer", {"customer_name": contact}, "name")
    info = get_dashboard_info('Customer', customer)
    return info[0].get('total_unpaid') if info else 0