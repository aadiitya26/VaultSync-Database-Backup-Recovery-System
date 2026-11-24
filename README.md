# VaultSync – Database Backup and Recovery System

## 1. Project Description

VaultSync is a web-based Database Backup and Recovery System designed to simplify database backup, monitoring, integrity verification, and restoration. The system provides a centralized platform for managing multiple databases, performing manual and scheduled backups, verifying backup integrity, and restoring databases when required.

VaultSync ensures the reliability and security of database backups through SHA-256 integrity verification, audit logging, retention management, and concurrent operation protection. It also provides a System Health Monitoring module that checks system resources, scheduler status, metadata database connectivity, and registered database connections.

## 2. Objectives

- To provide a centralized platform for managing multiple databases.
- To automate database backup operations through scheduled backups.
- To ensure backup integrity using SHA-256 hashing.
- To provide secure and reliable database restoration.
- To maintain audit logs of system activities.
- To manage backup storage through retention policies.
- To prevent simultaneous backup and restore operations on the same database.
- To monitor system health, disk space, backup storage, and database connectivity.

## 3. Team Members

- Aditya Yadav
- Raj Somvanshi
- Vaishnavi Chandna
- Isha Negi

## 4. Technologies and Tools Used

- **Programming Language:** Python
- **Web Framework:** Flask
- **Database:** MySQL
- **Frontend:** HTML, CSS
- **Backup Utility:** MySQL `mysqldump`
- **Integrity Verification:** SHA-256 Hashing
- **Scheduling:** APScheduler
- **Concurrency Control:** MySQL Advisory Locks
- **Logging:** Audit Logging System
- **Environment Management:** Python Virtual Environment
- **Configuration Management:** python-dotenv
- **Development Environment:** Visual Studio Code

## 5. Project Setup and Installation

### 5.1 Prerequisites

- Python 3.10 or later
- MySQL Server
- MySQL Client Utilities (`mysqldump`)
- Git
- Visual Studio Code (optional)

### 5.2 Clone the Repository

```bash
git clone <repository-url>
cd VaultSync
```

### 5.3 Create and Activate Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment on Windows:

```powershell
venv\Scripts\activate
```

### 5.4 Install Dependencies

```bash
pip install -r requirements.txt
```

### 5.5 Configure Environment Variables

Create a `.env` file in the project root directory and configure the required environment variables.

Example:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=vaultsync

SECRET_KEY=your_secret_key
```

### 5.6 Initialize the Metadata Database

Create the metadata database in MySQL and initialize the required tables using the project's schema file.

The metadata database is used to store registered database information, backup records, audit logs, and other system-related data.

### 5.7 Run the Application

```bash
python run.py
```

Open the application in your browser using the local URL provided by Flask.

### 5.8 Run Tests

Individual test modules can be executed from the project root directory.

Example:

```bash
python -m tests.test_locking
```

## 6. Major Features and Modules

### 6.1 Authentication Module

- Provides a login interface for accessing the system.
- Uses session-based authentication.
- Provides logout functionality.
- Restricts access to protected dashboard and system health pages.

### 6.2 Database Management

- Allows users to register databases for backup management.
- Supports management of multiple databases.
- Displays registered databases on the dashboard.
- Provides database search functionality.
- Maintains database information for backup and restoration operations.

### 6.3 Manual Backup

- Allows users to initiate database backups manually.
- Uses `mysqldump` to export database contents.
- Compresses backup files into `.sql.gz` format.
- Stores backup files in the designated backup directory.
- Generates SHA-256 hashes for backup integrity verification.
- Records backup metadata in the metadata database.

### 6.4 Automated Backup Scheduling

- Uses APScheduler to perform scheduled backups.
- Supports automatic daily backups.
- Uses the configured scheduling timezone.
- Automatically processes registered databases.
- Performs scheduled operations while the application and scheduler are running.

### 6.5 Backup Integrity Verification

- Uses SHA-256 hashing to verify backup file integrity.
- Validates backup files before restoration.
- Detects modifications or corruption in backup files.
- Prevents restoration of corrupted or tampered backup files.

### 6.6 Database Restoration

- Allows restoration of databases from stored backup files.
- Verifies backup integrity before initiating restoration.
- Rejects corrupted backups.
- Handles MySQL dump compatibility considerations, including GTID-related filtering.
- Provides confirmation before performing restoration.
- Uses operation locking to prevent conflicting operations.

### 6.7 Backup Metadata Management

- Stores backup-related information in the metadata database.
- Maintains information such as database name, backup file details, timestamps, status, and integrity hash.
- Tracks backup history for registered databases.
- Provides backup search functionality.

### 6.8 Audit Logging

- Records important system activities.
- Tracks backup and restoration operations.
- Maintains records of relevant system events.
- Provides an audit activity section on the dashboard.
- Helps monitor and review system operations.

### 6.9 Backup Retention Management

- Implements retention management for stored backup files.
- Helps control backup storage consumption.
- Removes eligible older backups according to configured retention rules.
- Maintains backup storage efficiency.

### 6.10 Web Dashboard

- Provides a centralized interface for managing the system.
- Displays managed databases and total backup statistics.
- Provides database registration and manual backup operations.
- Displays backup history and restoration controls.
- Includes separate search functionality for managed databases and backup history.
- Provides scrollable tables for database lists, backup history, and audit activity.
- Uses a structured workspace layout for improved navigation.
- Provides access to the System Health Monitoring page.

### 6.11 System Health Monitoring

- Monitors backup folder storage usage.
- Displays available disk space and total disk capacity.
- Checks backup scheduler status.
- Checks metadata database connectivity.
- Displays registered database inventory.
- Provides an overall system health status.
- Displays the latest backup timestamp.
- Presents system health information through a dedicated interface.

### 6.12 Database Connection Monitoring

- Checks connectivity of registered databases.
- Performs individual connection checks for each registered database.
- Displays database connection status.
- Reports connection errors when a database cannot be accessed.
- Presents connection results in a separate scrollable table.
- Helps identify unavailable or inaccessible databases.

### 6.13 Concurrent Operation Protection

- Uses MySQL Advisory Locks to prevent simultaneous backup or restore operations.
- Rejects conflicting operations when a database is already being processed.
- Prevents overlapping backup and restoration tasks.
- Releases locks after operations complete or fail.
- Helps maintain operational consistency and reliability.

## 7. Current Project Status and Progress

The following features have been implemented and tested:

- Flask-based web application.
- Session-based authentication and logout.
- Database registration and management.
- Manual database backup using `mysqldump`.
- Compressed backup file generation.
- SHA-256 integrity verification.
- Database restoration with integrity validation.
- Backup metadata management.
- Audit logging.
- Backup retention management.
- Automated daily backup scheduling.
- MySQL Advisory Lock-based concurrency protection.
- Backup and restoration error handling.
- Lock release and cleanup handling.
- System Health Monitoring.
- Registered database connection monitoring.
- Dashboard search functionality.
- Scrollable dashboard tables.
- Improved dashboard navigation and user interface.

### Future Work

- Further improvements to the user interface.
- Additional test cases and reliability testing.
- Enhanced monitoring and reporting.
- Improved deployment and configuration management.
- Additional backup management and recovery enhancements.
