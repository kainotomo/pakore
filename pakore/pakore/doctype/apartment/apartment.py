# Copyright (c) 2024, KAINOTOMO PH LTD and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Apartment(Document):
	
	def validate(self):
		self.total = self.enclosed_space + self.covered_verandas + self.uncovered_verandas
		pass