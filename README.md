# Django Clocking Web App

## 🚧 Project Status: In Progress 🚧
View only repo duplicated from main private repo as of Jan 30 2025

### Tasks to be Completed:
- Add more comments and function descriptions for better readability
- Standardize view structures across all apps for consistency
- Clean up indirection in report generation functions
- Complete tests for all apps
- Improve security measures

---

## Overview
This Django-based clocking web application is designed for efficient employee time tracking and reporting. It leverages class-based views for frequent functions and utilizes `asyncio` and Celery for background and scheduled operations to enhance performance. This repo is view only and a `**Redacted**` placeholder has been put in place of sensitive information, thus the code must be modified before it can be run. The actual code repository is private.

### Features:
- **Class-Based Views:** Used for frequent functions to maintain clean and reusable code.
- **AsyncIO Tasks & Celery:** Handles background tasks and scheduled operations.
- **Docker Deployment:** A `docker-compose.yml` sets up Django and Celery containers.
- **Daphne Server:** Used to deploy the Django application for improved performance.
- **Azure Deployment:** A YAML configuration file supports automatic deployment to Azure Container Services.

---

## Applications & Modules

### 1. **Clockify API**
Provides API endpoints for interfacing with the Clockify API.

### 2. **Report Generation**
Generates `.xlsx` reports based on backend data.

### 3. **LemAPP**
Provides API endpoints for interacting with LEM GENERATOR power apps.

### 4. **Utilities**
Includes helper functions, views, and batch functions for the Clocking API connection.

---

## Deployment Details

### **Docker & Celery Setup**
- The repo includes a `docker-compose.yml` file to create Django and Celery containers.
- Celery is managed using **supervisord**.
- The application is deployed using **Daphne**.

### **Azure Deployment**
- The repository contains a YAML configuration file for automatic deployment to **Azure Container Services**.

---

## Testing
A `test.py` file is included to test various functionalities across all applications.

---

## Security Considerations
Security improvements are ongoing, but additional measures are needed to **harden API endpoints and secure data transmission**.

---

## Author
All code in this repository was written by **Timmy Ifidon** at **Hill Plain Construction**.

