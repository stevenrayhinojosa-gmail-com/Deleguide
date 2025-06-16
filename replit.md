# Educational Task Management System

## Overview

This is a Streamlit-based educational task management system designed to streamline task delegation and tracking between students and staff in educational institutions. The application provides a web interface for managing student profiles, staff assignments, and task progress tracking with real-time analytics and reporting capabilities.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit for web-based user interface
- **Styling**: Custom CSS for enhanced UI/UX
- **Visualization**: Plotly Express for interactive charts and dashboards
- **Layout**: Wide layout with sidebar navigation for different sections

### Backend Architecture
- **Language**: Python 3.11
- **ORM**: SQLAlchemy for database operations
- **Session Management**: SQLAlchemy SessionLocal for database connections
- **Data Processing**: Pandas for data manipulation and analysis

### Database Architecture
- **Database**: PostgreSQL (configurable via environment variables)
- **Tables**: 
  - `students` - Student profiles with goals and needs
  - `staff` - Staff members with expertise areas
  - `tasks` - Task assignments linking students and staff
- **Relationships**: Foreign key relationships between tasks, students, and staff

## Key Components

### 1. Data Models (`models.py`)
- **Student Model**: Stores student information, educational goals, and specific needs
- **Staff Model**: Manages staff profiles with expertise areas
- **Task Model**: Handles task assignments with completion tracking and deadlines
- **Database Session**: Centralized database connection management

### 2. Main Application (`app.py`)
- **Navigation System**: Sidebar-based page routing
- **Dashboard**: Quick stats and overview metrics
- **Section Management**: Modular approach for different application areas
- **Real-time Metrics**: Live counting of students and staff

### 3. Application Sections
- **Dashboard**: System overview and key metrics
- **Student Management**: CRUD operations for student profiles
- **Staff Management**: Staff profile and expertise management
- **Task Management**: Task creation, assignment, and tracking
- **Progress Tracking**: Real-time progress monitoring
- **Reports**: Analytics and performance reporting

## Data Flow

1. **Student Registration**: Students are registered with their educational goals and specific needs
2. **Staff Assignment**: Staff members are added with their areas of expertise
3. **Task Creation**: Tasks are created and assigned to appropriate staff based on student needs
4. **Progress Tracking**: Task completion status is monitored and updated
5. **Reporting**: Analytics are generated based on task completion and student progress

## External Dependencies

### Core Dependencies
- **Streamlit**: Web application framework for the user interface
- **SQLAlchemy**: ORM for database operations and model definitions
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive visualization and charting
- **psycopg2-binary**: PostgreSQL database adapter

### Database
- **PostgreSQL**: Primary database for persistent storage
- **Environment Configuration**: Database connection managed via environment variables

## Deployment Strategy

### Replit Configuration
- **Runtime**: Python 3.11 with Nix package management
- **Port Configuration**: Streamlit runs on port 5000, exposed as port 80
- **Auto-scaling**: Configured for autoscale deployment target
- **Workflow**: Automated package installation and application startup

### Environment Setup
- **Database URL**: Configurable PostgreSQL connection string
- **Debug Mode**: Toggleable debug settings for development
- **Security**: Environment variables for sensitive configuration

### Development Workflow
- **Package Management**: Automatic dependency installation via pyproject.toml
- **Testing**: Unit tests included for model validation
- **Version Control**: Git-based with comprehensive .gitignore

## Changelog

Changelog:
- June 16, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.