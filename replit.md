# Educational Task Management System

## Overview
A comprehensive Streamlit-based educational task management system designed for Special Education (SPED) programs. The system streamlines task delegation and tracking between students and staff, with enhanced features for daily task feeds, ARD date tracking, and automated task scheduling.

### Purpose
- Manage student profiles with learning goals, needs, and ARD dates
- Track staff expertise and availability
- Create and assign tasks with various frequencies (Daily, Weekly, Monthly, etc.)
- Generate daily task feeds for staff members
- Monitor task completion and progress
- Generate comprehensive reports and analytics

### Current State
- Fully functional with PostgreSQL database integration
- Enhanced UI with Daily Task Feed functionality
- Supporting ARD date tracking and countdown notifications
- Task frequency management (Daily, Once a Month, Every 9 Weeks, Once a Year)
- Real-time dashboard with analytics and visualizations

## Project Architecture

### Core Components
1. **Streamlit Frontend** (`app.py`)
   - Multi-page navigation (Dashboard, Daily Task Feed, Student/Staff/Task Management, Progress Tracking, Reports)
   - Interactive forms for data entry
   - Real-time data visualization with Plotly
   - Responsive design with custom CSS

2. **Database Models** (`models.py`)
   - SQLAlchemy ORM with PostgreSQL backend
   - Three main entities: Students, Staff, Tasks
   - Relationship mapping between entities
   - Enhanced with ARD dates and task frequency tracking

3. **Daily Task Feed Generator** (`daily_task_feed.py`)
   - Automated task scheduling based on frequency patterns
   - ARD date proximity notifications (21-day alert window)
   - Staff-specific task summaries
   - Console and web-based output formats

### Database Schema
- **Students**: id, name, goals, needs, ard_date
- **Staff**: id, name, expertise
- **Tasks**: id, description, category, staff_id, student_id, deadline, completed, frequency, last_completed

### Key Features
- **Task Frequency Support**: Daily, Once a Month, Every 9 Weeks, Once a Year, Once
- **ARD Integration**: Automatic countdown and task generation for ARD preparation
- **Daily Feed Generation**: Automated morning task lists for each staff member
- **Progress Tracking**: Completion rates and analytics
- **Responsive UI**: Professional interface with icons and organized layout

## Recent Changes

### 2025-01-16: Daily Task Feed Implementation
- Added comprehensive daily task feed generator module
- Enhanced database schema with frequency and ARD date fields
- Implemented ARD countdown notifications (21-day window)
- Added staff-specific task summary functionality
- Integrated daily feed into main Streamlit navigation
- Updated forms to support ARD dates and task frequencies

### Architecture Decisions
- **PostgreSQL**: Chosen for robust data persistence and relationship management
- **SQLAlchemy ORM**: Provides clean database abstraction and migration support
- **Streamlit**: Rapid development framework with built-in UI components
- **Frequency-Based Scheduling**: Supports educational calendar patterns (9-week cycles, monthly reviews)

## Technical Details

### Dependencies
- streamlit: Web application framework
- pandas: Data manipulation and analysis
- plotly: Interactive data visualizations
- sqlalchemy: Database ORM
- psycopg2-binary: PostgreSQL adapter

### Configuration
- Server runs on port 5000 with 0.0.0.0 binding for deployment
- Database connection via DATABASE_URL environment variable
- Streamlit config in `.streamlit/config.toml`

### Database Migrations
- Schema changes applied via SQL ALTER statements
- Added: students.ard_date, tasks.frequency, tasks.last_completed

## User Preferences
- Prefers simple, everyday language explanations
- Values comprehensive functionality over minimal features
- Interested in educational workflow automation
- Focuses on practical SPED program management needs

## Future Enhancement Opportunities
- Email/SMS notifications for task reminders
- Advanced task assignment algorithms based on staff expertise matching
- Calendar integration for better scheduling
- Custom report generation with export capabilities
- Mobile-responsive design improvements
- Bulk task import/export functionality

## Deployment Notes
- Application ready for Replit deployment
- All essential files present (README.md, .gitignore, LICENSE, tests)
- Environment configured for production use
- Database schema current and stable