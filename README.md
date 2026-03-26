# 🚀 Jira Dynamic Reporting Platform

A production-grade reporting system that allows users to dynamically create, schedule, and download Jira reports without writing JQL manually.

---

## 📌 Overview

This project is a **full-stack reporting platform** built using FastAPI and Docker that enables:

* Dynamic report creation via UI
* Automated report scheduling
* Efficient handling of large datasets
* Real-time progress tracking
* Report history, retry, and cleanup

Designed with **performance, scalability, and usability** in mind.

---

## 🏗️ Architecture

```
Frontend (HTML + JS)
        ↓
FastAPI Backend (REST APIs)
        ↓
Report Engine (JQL Builder + Pagination)
        ↓
Jira / JSM APIs
        ↓
MySQL Database (Reports + History)
        ↓
Scheduler (Cron-based automation)
```

---

## ✨ Features

### 🔹 Core Features

* Dynamic report builder (Project, Status, Issue Type, Fields)
* Custom JQL support
* Date filters (Start/End Date, Last N Days)
* Preview before execution
* CSV report download

---

### ⚡ Advanced Features

* 📊 Pagination for large datasets (5000+ issues)
* ⏳ Real-time progress tracking (API polling)
* 🕓 Report history with audit trail
* 🔁 Retry failed reports
* 🧹 Auto cleanup of old reports
* ⏰ Scheduler (One-time, Daily, Weekly, Monthly)
* 🌍 Multi-instance support (Jira + JSM ready)
* 🕒 IST timezone consistency across system

---

### 🚀 Performance Optimizations

* Cached downloads (instant reuse)
* Freshness check (1-hour caching)
* Avoid redundant API calls
* Efficient background processing

---

## 🛠️ Tech Stack

* **Backend:** FastAPI (Python)
* **Frontend:** HTML, CSS, JavaScript
* **Database:** MySQL
* **Containerization:** Docker, Docker Compose
* **APIs:** Jira REST API
* **Scheduler:** Cron-based (custom implementation)

---

## 📂 Project Structure

```
.
├── app
│   ├── api              # API routes (Jira, Reports, JSM)
│   ├── db               # Database connection
│   ├── models           # SQLAlchemy models
│   ├── services         # Report engine, scheduler
│   └── main.py          # FastAPI entry point
├── templates            # Frontend UI (HTML)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── wait_for_db.py
```

---

## ⚙️ Setup & Installation

### 🔹 Prerequisites

* Docker & Docker Compose installed

---

### 🔹 Run the Application

```bash
git clone <your-repo-url>
cd jira-report-platform

docker-compose up --build
```

---

### 🔹 Access Application

```
http://localhost:8000
```

---

## 📊 Usage

1. Create a report using UI
2. Select:

   * Projects
   * Status
   * Issue Types
   * Fields
3. Apply date filters
4. Preview report
5. Download CSV
6. Optionally schedule the report

---

## 🔁 Scheduler Options

* One Time
* Daily
* Weekly
* Monthly

---

## 📈 API Highlights

| Endpoint                      | Description           |
| ----------------------------- | --------------------- |
| `/reports`                    | Create / List reports |
| `/reports/{id}/preview`       | Preview report        |
| `/reports/{id}/download`      | Download report       |
| `/reports/progress/{job_id}`  | Track progress        |
| `/reports/history`            | View report history   |
| `/reports/history/{id}/retry` | Retry failed reports  |

---

## 🧠 Key Learnings

* Handling large datasets with pagination
* Optimizing API performance with caching
* Building dynamic query systems (JQL)
* Managing background tasks & scheduling
* Ensuring timezone consistency (IST)
* Designing scalable backend architecture

---

## 🚀 Future Enhancements

* Async processing (Celery + Redis)
* S3 file storage
* Email notifications
* Role-based access control
* Kubernetes deployment

---

## 👨‍💻 Author

**Vijay Kumar C M**

---

## ⭐ Acknowledgements

* Atlassian Jira APIs
* FastAPI Documentation
* Open-source community

---

## 📌 Notes

* All timestamps are handled in IST (Asia/Kolkata)
* Designed for production-scale Jira environments

---

## ⭐ If you like this project

Give it a ⭐ on GitHub!
