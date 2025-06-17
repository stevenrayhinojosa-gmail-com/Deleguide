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
   - Multi-page navigation (Dashboard, Daily Task Feed, Teacher Interface, Task Recommendations, Smart Scheduling, Recurring Tasks, Student/Staff/Task Management, Progress Tracking, Reports)
   - Interactive forms for data entry
   - Real-time data visualization with Plotly
   - Responsive design with custom CSS

2. **Database Models** (`models.py`)
   - SQLAlchemy ORM with PostgreSQL backend
   - Three main entities: Students, Staff, Tasks
   - Relationship mapping between entities
   - Enhanced with ARD dates and task frequency tracking

3. **Recurring Task Generator** (`recurring_task_generator.py`)
   - Automated daily task generation for active school days
   - School calendar integration with holiday/break detection
   - Task exception system for staff-declared skip dates
   - Recurring task template management with frequency support
   - School calendar event management and reporting

4. **Smart Scheduling Engine** (`scheduling_engine.py`)
   - Intelligent due date calculations for frequency-based tasks
   - Grading period alignment with academic calendar
   - ARD-based scheduling with configurable buffer periods
   - Deadline update system with preview and auto-update options
   - Comprehensive scheduling reports with urgency indicators

5. **Daily Task Feed Generator** (`daily_task_feed.py`)
   - Automated task scheduling based on frequency patterns
   - ARD date proximity notifications (21-day alert window)
   - Staff-specific task summaries
   - Console and web-based output formats

6. **Task Recommendation Engine** (`task_recommender.py`)
   - AI-powered task suggestions based on IEP goals and student needs
   - Rule-based keyword matching system with comprehensive dictionaries
   - Staff expertise matching for optimal task assignment
   - Priority-based recommendations (high/medium priority)
   - ARD preparation task generation
   - Bulk recommendation processing for multiple students

7. **Teacher Interface Module** (`teacher_interface.py`)
   - Daily task management and completion workflow for individual teachers
   - Real-time task status updates with completion notes and timestamps
   - Interactive dashboard with progress tracking and analytics
   - Task filtering by teacher, date, and completion status
   - Export functionality with CSV download for daily reports
   - Visual completion analytics with pie charts and category breakdowns

8. **Weekly SPED Task Report Generator** (`reporting_module.py`)
   - Comprehensive weekly report generation for SPED staff and administrators
   - Automated task completion summaries with missed task identification
   - IEP goal coverage analysis using intelligent keyword mapping
   - Individual staff reports and master reports for all staff members
   - Multi-format export capabilities (CSV detailed, CSV summary, text format)
   - Historical reporting support for multiple week periods
   - Integration with Streamlit Reports dashboard with tabbed interface

### Database Schema
- **Students**: id, name, goals, needs, ard_date
- **Staff**: id, name, expertise
- **Tasks**: id, description, category, staff_id, student_id, deadline, completed, frequency, last_completed, completion_note, completed_at

### Key Features
- **Task Frequency Support**: Daily, Weekly, Monthly, Every 9 Weeks, Once a Year, Once
- **ARD Integration**: Automatic countdown and task generation for ARD preparation
- **Recurring Task Automation**: Automated daily task generation with school calendar integration
- **Smart Scheduling Engine**: Intelligent due date calculations based on academic calendar
- **Task Exception System**: Staff can skip recurring tasks for specific dates with reasons
- **School Calendar Integration**: Holiday and break detection with event management
- **Daily Feed Generation**: Automated morning task lists for each staff member
- **Teacher Task Interface**: Individual teacher dashboards for daily task completion workflow
- **Task Completion Tracking**: Real-time completion status with notes and timestamps
- **AI Task Recommendations**: Intelligent task suggestions based on IEP goals and student needs
- **Staff Expertise Matching**: Automatic assignment of tasks to appropriately skilled staff
- **One-Click Task Creation**: Direct creation of recommended tasks with optimal settings
- **Bulk Processing**: Generate recommendations for all students simultaneously
- **Progress Tracking**: Completion rates and analytics with urgency indicators
- **Export Capabilities**: CSV download and daily report generation
- **Weekly SPED Reporting**: Comprehensive weekly reports with completion summaries and goal coverage
- **Multi-Format Export**: CSV, text, and summary exports for administrative reporting
- **Historical Analysis**: Multi-week reporting capabilities for trend analysis
- **Administrative Dashboard**: Master reports covering all staff with performance metrics
- **Responsive UI**: Professional interface with icons and organized layout

## Recent Changes

### 2025-06-17: System Validation and Debug Completion
- Achieved 100% system functionality across all 8 core components
- Fixed critical SQLAlchemy session management issue in daily task feed generator
- Resolved Task object subscription errors by converting to dictionaries before session closure
- Successfully validated task recommendation engine generating 16 intelligent suggestions
- Confirmed all database relationships and data integrity (3 students, 4 staff, 54 tasks)
- Completed comprehensive end-to-end testing with full system integration
- System now production-ready with authentic data processing and no mock/placeholder data

### 2025-01-16: Weekly SPED Task Report Generator Implementation
- Built comprehensive Weekly SPED Task Report Generator module for administrative reporting
- Created automated weekly report generation with completion summaries and missed task analysis
- Implemented IEP goal coverage mapping using keyword matching algorithms
- Added support for individual staff reports and master reports for all staff
- Built CSV export functionality with detailed and summary report options
- Integrated text format export for email and document sharing
- Added multi-week historical reporting capabilities (current week to 4 weeks back)
- Connected all reporting data with completion timestamps and goal coverage analytics
- Fully integrated into Streamlit Reports section with tabbed interface
- Successfully tested report generation, goal mapping, and export functionality

### 2025-01-16: Teacher Interface Module Implementation
- Built comprehensive Teacher Task Interface module for daily task management
- Created task completion workflow with note-taking functionality
- Added database schema updates for completion tracking (completion_note, completed_at)
- Implemented interactive teacher dashboard with real-time progress tracking
- Added task filtering by teacher and date with completion status updates
- Built export functionality with CSV download capabilities
- Integrated visual charts for task completion analytics
- Connected all completion data with timestamp and teacher attribution
- Fully tested workflow from task assignment to completion with notes

### 2025-01-16: Recurring Task Generator Implementation
- Built comprehensive recurring task automation system with intelligent scheduling
- Created automated daily task generation for active school days
- Implemented school calendar integration with holiday/break detection
- Added task exception system for staff-declared skip dates (absences, field trips)
- Built recurring task template management with frequency support
- Integrated school calendar management with event tracking
- Added complete task generation reporting and preview functionality
- Supports Daily, Weekly, Monthly, and Every 9 Weeks frequency patterns

### 2025-01-16: Smart Scheduling Engine Implementation
- Built intelligent due date calculator for non-daily tasks
- Added support for frequency-based scheduling (Daily, Monthly, Every 9 Weeks, Once a Year)
- Implemented grading period calculations aligned with school calendar
- Created ARD-based scheduling with 3-week buffer for yearly tasks
- Added deadline update system with preview and auto-update options
- Built comprehensive scheduling reports with urgency indicators
- Integrated task frequency distribution analytics

### 2025-01-16: Task Recommendation Engine Implementation
- Built comprehensive AI-powered task recommendation system
- Added rule-based matching engine for IEP goals to task suggestions
- Implemented keyword extraction and intelligent task mapping
- Created comprehensive goal-to-task and service-to-task dictionaries
- Added staff expertise matching for optimal task assignment
- Integrated one-click task creation from recommendations
- Built bulk recommendation functionality for all students
- Added priority-based task categorization (high/medium priority)
- Implemented ARD-proximity task generation (preparation tasks)

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