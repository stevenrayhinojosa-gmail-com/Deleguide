# Educational Task Management System 📚

A robust Streamlit-based educational task management system designed to streamline task delegation and tracking between students and staff. This application helps educational institutions manage and monitor student progress through efficient task assignment and progress tracking.

## Features 🌟

- **Student Profile Management**
  - Create and manage student profiles
  - Track educational goals and specific needs
  - Monitor individual progress

- **Staff Management**
  - Maintain staff profiles with expertise areas
  - Track task assignments and completion rates
  - Performance monitoring

- **Task Management**
  - Create and assign educational tasks
  - Track task completion status
  - Set deadlines and priorities

- **Progress Tracking**
  - Real-time progress monitoring
  - Interactive dashboards
  - Performance analytics

- **Reporting System**
  - Generate comprehensive reports
  - Visualize task completion rates
  - Track student and staff performance

## Installation 🔧

1. Clone the repository:
```bash
git clone <repository-url>
cd educational-task-management
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up the PostgreSQL database:
   - Ensure PostgreSQL is installed and running
   - Create a `.env` file with your database credentials:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

4. Run the application:
```bash
streamlit run app.py
```

## Tech Stack 💻

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Data Visualization**: Plotly
- **Data Processing**: Pandas

## Project Structure 📁

```
educational-task-management/
├── app.py              # Main application file
├── models.py           # Database models
├── requirements.txt    # Project dependencies
├── .env               # Environment variables
├── .gitignore         # Git ignore rules
├── README.md          # Project documentation
└── .streamlit/        # Streamlit configuration
    └── config.toml    # Streamlit settings
```

## Usage Guide 📖

1. **Adding Students**
   - Navigate to "Student Management"
   - Fill in student details and educational needs
   - Submit the form to create a student profile

2. **Managing Staff**
   - Go to "Staff Management"
   - Add staff members with their expertise areas
   - View current staff and their assignments

3. **Creating Tasks**
   - Select "Task Management"
   - Create tasks with descriptions and deadlines
   - Assign tasks to specific staff members and students

4. **Tracking Progress**
   - Use the "Progress Tracking" section
   - Monitor task completion status
   - Update task status as needed

5. **Generating Reports**
   - Access the "Reports" section
   - View performance metrics and analytics
   - Export reports as needed

## Contributing 🤝

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature/improvement`)
6. Create a Pull Request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support 🆘

For support, please open an issue in the repository or contact the development team.
