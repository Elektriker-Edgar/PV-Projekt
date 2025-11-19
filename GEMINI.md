# Gemini Project: EDGARD Elektro - PV-Service Platform

## Project Overview

This is a monolithic **Django** application that serves as a price calculator and quote generation tool for a PV (photovoltaic) systems installation company. The frontend is a multi-step form built with **Bootstrap** and **jQuery**, without a modern SPA framework.

The application's core functionality is a 6-step price calculator that provides users with a live price estimate for their PV system installation. The pricing logic is driven by a `PriceConfig` model in the database, making it easily configurable.

The project also includes a product catalog, a quote editing system, and integration with n8n for workflow automation.

**Key Technologies:**

*   **Backend:** Django, Django REST Framework
*   **Frontend:** Bootstrap, jQuery
*   **Database:** PostgreSQL (production), SQLite (development)

## Building and Running

### 1. Install Dependencies

The Python dependencies are listed in `docs/requirements.txt`. To install them, run:

```bash
pip install -r docs/requirements.txt
```

### 2. Apply Database Migrations

Before running the application for the first time, you need to apply the database migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create a Superuser (Optional)

To access the Django admin interface, you'll need a superuser account:

```bash
python manage.py createsuperuser
```

### 4. Run the Development Server

You can start the Django development server with the following command:

```bash
python manage.py runserver 192.168.178.30:8025
```

The application will then be accessible at `http://192.168.178.30:8025/`.

## Development Conventions

### Code Structure

*   The project follows a standard Django project structure, with the main project folder being `edgard_site` and individual applications located in the `apps/` directory.
*   The core application seems to be `apps/quotes`, which contains the pricing logic, models, and views for the pre-check wizard.
*   Frontend code (HTML and JavaScript) is primarily located in the `templates/` directory, with the main file being `templates/quotes/precheck_wizard.html`.

### Pricing Logic

*   The pricing logic is centralized in `apps/quotes/pricing.py` and is used by the pre-check wizard, the API, and the quote generation system.
*   Prices are stored in the `PriceConfig` model (`apps/quotes/models.py`) and can be managed through the Django admin interface.

### Testing

The project includes a `TESTS/` directory with some automated tests. To run the tests, you can use the `run_tests.bat` script.

The `README.md` and `docs/CLAUDE.md` files also provide `curl` commands for testing the API endpoints.
