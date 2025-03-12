# Django Clocking Web App

## 🚧 Project Status: In Progress 🚧

---

## Overview
This Django-based clocking web application is designed for efficient employee time tracking and reporting. It leverages class-based views for frequent functions and utilizes `asyncio` and Celery for background and scheduled operations to enhance performance. This repo is view only and a `**Redacted**` placeholder has been put in place of sensitive information, thus the code must be modified before it can be run. The actual code repository is private.

### Features:
- **Class-Based Views:** Used for frequent functions to maintain clean and reusable code.
- **AsyncIO Tasks & Celery:** Handles background tasks and scheduled operations.
- **Docker Deployment:** A `docker-compose.yml` compsese two DockerFiles to set up Django and Celery Containers
- **Daphne Server:** Used to deploy the Django application for ASGI performance.
- **Supervisord:** Manages multiple celery worker processes
- **Azure Deployment:** A YAML configuration file supports CI/CD to Azure Container Services.
- **SQL Database Management:** Initially defined in MSSQL, now maintained through Django’s ORM for efficient database connections and migrations.
- **App Level README:** Specific instructions and documentation detailed at the App level directories.
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

### 5. **BackgroundTasks**
Includes the defintion for background and scheduled tasks.

### 6. **LemApplication**
API backend for LEM generator Power APP.

---

## Deployment Details

### **Docker & Celery Setup**
- The repo includes a `docker-compose.yml` file to create Django and Celery containers.
- Each image is pushed to an Azure Container Instance.
- Celery is managed using **supervisord**.
- The application server is started using **Daphne**.

### **Azure Deployment**
- The repository contains a YAML configuration file for automatic deployment to **Azure Container Services**.

---

## Testing
A `test.py` file is included in each app directory, implementing unit tests, user stories, and various functionalities across all modules.

---

## Security Considerations
Current Security Measures:
- API Authentication with Secret Keys: All API requests require authentication through secret keys, ensuring only authorized applications can access endpoints.
- IP Whitelisting for Database Access: The database is configured to allow queries only from trusted IPs, enforced through Azure firewall rules, reducing exposure to unauthorized access.
- Microsoft Entra Authentication: User authentication and access control are managed via Microsoft Entra ID, ensuring secure identity verification.
- CSRF Protection: Cross-Site Request Forgery (CSRF) protection is implemented to prevent unauthorized actions from malicious sites.

Further enhancements will focus on strengthening encryption, implementing role-based access controls, and continuous security audits.
---

## Author
All code in this repository was written by **Timmy Ifidon** at **Hill Plain Construction LP** between the months of Jan 2024 and March 2025.

