# Project Guidelines

## Code Style
- Python: Follow Frappe conventions (import frappe, use snake_case, etc.)
- JavaScript: Use Frappe's client-side API (frappe.call, frappe.msgprint)
- DocType naming: singular, CamelCase for class names, lowercase with underscores for doctype names
- Custom fields prefix: Use `custom_` for fields added to existing doctypes

## Architecture
- This is a Frappe v16 app extending ERPNext for property communal fees management.
- Main components: PakoreSettings doctype, customer extension field, customer balance API, frontend alert.
- The app adds a custom field `custom_apartment` to Customer doctype.
- Whitelisted API endpoint at `pakore.pakore.custom.customer_balance.get_customer_balance`.
- Frontend JavaScript injected via web_include_js in hooks.

## Build and Test
- Install app: `bench install-app pakore`
- Run tests: `bench --site <sitename> run-tests app.pakore`
- Start development server: `bench start`
- Dependencies: Managed by bench; Python 3.10+ required.
- No custom build steps; assets are static.

## Conventions
- Custom fields use `custom_` prefix.
- Whitelisted methods must be decorated with `@frappe.whitelist()`.
- Doctype classes inherit from `frappe.model.document.Document` with minimal overrides.
- API endpoints return simple values; error handling is minimal.
- Frontend JavaScript uses `frappe.ready` and `frappe.call`.

## Potential Pitfalls
- Customer balance depends on user→contact→customer mapping; returns 0 if missing.
- Ensure ERPNext accounts module is installed for party dashboard functions.
- Workspace and dashboard references may become stale if ERPNext structure changes.
- The app is minimal; expand with versioning strategy for settings.

## Key Reference Files
- `hooks.py`: App hooks and web includes.
- `pakore/pakore/custom/customer_balance.py`: Whitelisted API pattern.
- `pakore/pakore/custom/customer.json`: Custom field extension example.
- `pakore/public/js/pakore.js`: Frontend API call pattern.
- `pakore/pakore/doctype/pakore_settings/`: Minimal doctype example.