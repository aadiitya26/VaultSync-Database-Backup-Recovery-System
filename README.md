# VaultSync — Database Backup and Recovery System

## 1. Project Description

**(VaultSync)** is a software designed to automate database backup, recovery, and integrity verification. It helps protect critical database information from accidental deletion, system failures, corruption, and unauthorized modification.

The system provides a centralized interface for managing database backups, monitoring backup operations, verifying backup integrity using cryptographic hashing, and restoring databases when required.

It supports manual and automated backups, compressed backup storage, SHA-256 integrity verification, backup metadata management, retention processing, and audit logging.

## 2. Objectives

1. Automate the database backup process.
2. Provide secure storage and management of backup files.
3. Verify backup integrity using cryptographic hash values.
4. Allow users to restore databases from available backups.
5. Maintain audit logs of important system activities.
6. Provide information about backup status and history.
7. Reduce the risk of permanent data loss due to database failures.

## 3. Team Members

1. Aditya Yadav
2. Raj Somvanshi
3. Vaishnavi Chandna
4. Isha Negi

## 4. Technologies and Tools Used

- **Python:** Used for backend programming and application logic.
- **Flask:** Used to develop the web application and handle HTTP routes.
- **MySQL:** Used as the relational database management system.
- **MySQL `mysqldump`:** Used to create database backups.
- **MySQL Command-Line Client (`mysql`):** Used to restore databases from SQL backup files.
- **HTML:** Used to structure the web pages and dashboard.
- **CSS:** Used to style the user interface.
- **JavaScript:** Used for client-side interactivity, where implemented.
- **SHA-256:** Used to verify backup file integrity and detect modifications.
- **APScheduler:** Used to schedule and execute automated daily backup jobs.
- **Werkzeug:** Used for password hashing and authentication utilities.
- **Python Virtual Environment (`venv`):** Used to isolate project dependencies.
- **python-dotenv:** Used to load environment variables from the `.env` file, if configured.

## 5. Project Setup and Installation

### Prerequisites

- Python 
- MySQL Server
- MySQL command-line utilities (`mysqldump` and `mysql`)
- PowerShell or another compatible terminal

### Step 1: Clone or obtain the project

If using Git:

```bash
git clone <repository-url>
cd VaultSync-Database-Backup-Recovery-System
```

Alternatively, open the directory containing the project files.

### Step 2: Create a virtual environment

```powershell
python -m venv venv
```

Activate the environment in Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 3: Install dependencies

```powershell
pip install -r requirements.txt
```

### Step 4: Configure environment variables

Create or configure the `.env` file according to the variables expected by `app/config.py`.

Provide the required MySQL connection settings, application configuration, and any other required environment variables.


### Step 5: Initialize the application database

Ensure that MySQL Server is running and that the application database and required tables have been created according to the project's schema and setup procedure.

Make sure the configured database account has the permissions required for backup and restoration operations.

### Step 6: Start the application

```powershell
python run.py
```

Open the application in a browser:

```text
http://127.0.0.1:5000
```

Log in using an existing application account.

### Step 7: Configure and test

1. Register the databases to be managed.
2. Create a manual backup to verify the configuration.
3. Check that backup files and metadata are generated.
4. Test backup integrity verification.
5. Test restoring a valid backup.
6. Keep the application running for scheduled backups.

**Note:** The current scheduler operates within the application process. It must remain running for scheduled jobs to execute.

## 6. Major Features and Modules

### 6.1 User Authentication

Provides login functionality and session-based access to the web application. Password hashing is handled using Werkzeug utilities.

### 6.2 Database Management

Allows users to register databases and retrieve information about the databases managed by VaultSync.

### 6.3 Manual Database Backup

Creates a database backup using `mysqldump`. Backup files are compressed and stored with timestamped filenames.

### 6.4 Automated Backup Scheduling

Uses APScheduler to execute daily backup jobs at a configurable time. The scheduler retrieves registered databases and invokes the backup service for each one.

### 6.5 Backup Integrity Verification

Uses SHA-256 hashes to detect changes to backup files. The calculated hash is compared with the stored hash to identify modified or corrupted backups.

### 6.6 Database Restoration

Restores databases from available backup files after checking their existence and integrity. A backup that fails integrity verification is rejected before the restoration proceeds.

### 6.7 Backup Metadata Management

Stores backup information such as the database reference, filename, file path, file size, SHA-256 hash, status, and creation timestamp.

### 6.8 Audit Logging

Records important application activities and their outcomes to support monitoring and troubleshooting.

### 6.9 Backup Retention Management

Applies the configured retention policy to remove older backup files and their associated metadata, helping manage storage usage.

### 6.10 Web Dashboard

Provides a centralized interface for managing registered databases, creating backups, and accessing restoration functionality.

## 7. Current Project Status and Progress

The core backup and recovery functionality has been implemented and tested.

### Completed and tested

- User authentication and dashboard functionality.
- Database registration and management.
- Manual database backups.
- Automated daily backups using APScheduler.
- Timestamped, compressed SQL backup files.
- Backup metadata storage.
- SHA-256 integrity verification.
- Rejection of a corrupted backup during restoration.
- Successful restoration of a valid backup.
- Backup retention processing.
- Audit logging functionality.

### Future Work

- Improving the user interface and user experience.
- Strengthening error handling and operational reliability.
- Expanding automated tests and recovery validation.
- Improving deployment and scheduler reliability.
- Implementing additional requirements identified for subsequent project phases.
