# Stockwise — Inventory and Stock Management System

A complete beginner-friendly Python project built with Flask, SQLite, HTML, Bootstrap, CSS and JavaScript. It includes hashed admin passwords, a dashboard, product CRUD, search and filters, low-stock warnings, quantity adjustments, input validation, and inventory valuation.

## Run in VS Code (Windows)
1. Install Python 3.10+ and open this folder in VS Code.
2. Open Terminal and run `py -m venv .venv`
3. Activate it: `.venv\Scripts\Activate.ps1` (PowerShell). If PowerShell blocks activation, use Command Prompt and run `.venv\Scripts\activate.bat`.
4. Install Flask: `pip install -r requirements.txt`
5. Start the app: `py app.py`
6. Open http://127.0.0.1:5000 in your browser.

macOS/Linux: replace step 2 with `python3 -m venv .venv`, activate with `source .venv/bin/activate`, then run `python app.py`.

Demo login: **admin** / **admin123**. The app creates `inventory.db` and example rows on first start. Keep it local for a training demo; change the demo password and `SECRET_KEY` before deployment.

## Try it locally
Sign in, add a product with a unique SKU, edit its details, use the search/category/low-stock filters, adjust stock with a positive or negative whole number, and delete a product. Try entering a duplicate SKU, a negative quantity, or reducing stock below zero to see validation messages. Refresh after edits to confirm SQLite saved the data.

## Viva notes
- `app.py`: Flask URL routes, validation, login checks and SQLite queries.
- `templates/`: Jinja HTML views; `static/`: styling and a delete confirmation.
- `users`: stores a Werkzeug password hash, never the plain password.
- `products`: stores each SKU, category, unit price, current quantity and reorder threshold.
- Dashboard value = sum of `price × quantity`; low-stock means `quantity <= reorder_level`.
