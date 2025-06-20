from datetime import datetime, date, timedelta
from sqlalchemy import text
from models import engine, Student, Staff, Task, SessionLocal
from typing import Dict, List, Optional, Tuple
import calendar

class RecurringTaskGenerator:
    def __init__(self):
        self.Session = SessionLocal
        
        # School calendar configuration
        self.school_year_start = date(2024, 8, 26)
        self.school_year_end = date(2025, 6, 6)
        
        # Default holidays and breaks
        self.default_holidays = [
            ('2024-09-02', 'Labor Day'),
            ('2024-10-14', 'Columbus Day'),
            ('2024-11-11', 'Veterans Day'),
            ('2024-11-28', 'Thanksgiving Day'),
            ('2024-11-29', 'Day after Thanksgiving'),
            ('2024-12-23', 'Winter Break Start'),
            ('2024-12-24', 'Christmas Eve'),
            ('2024-12-25', 'Christmas Day'),
            ('2024-12-26', 'Winter Break'),
            ('2024-12-27', 'Winter Break'),
            ('2024-12-30', 'Winter Break'),
            ('2024-12-31', 'New Year\'s Eve'),
            ('2025-01-01', 'New Year\'s Day'),
            ('2025-01-02', 'Winter Break'),
            ('2025-01-03', 'Winter Break End'),
            ('2025-01-20', 'Martin Luther King Jr. Day'),
            ('2025-02-17', 'Presidents Day'),
            ('2025-03-31', 'Spring Break Start'),
            ('2025-04-01', 'Spring Break'),
            ('2025-04-02', 'Spring Break'),
            ('2025-04-03', 'Spring Break'),
            ('2025-04-04', 'Spring Break End'),
            ('2025-05-26', 'Memorial Day')
        ]
        
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the recurring task system with default data"""
        session = self.Session()
        
        try:
            # Create simple tables using raw SQL
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS school_calendar (
                    id SERIAL PRIMARY KEY,
                    date DATE NOT NULL UNIQUE,
                    event_name VARCHAR NOT NULL,
                    event_type VARCHAR DEFAULT 'holiday',
                    description TEXT
                )
            """))
            
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS task_exceptions (
                    id SERIAL PRIMARY KEY,
                    staff_id INTEGER REFERENCES staff(id),
                    student_id INTEGER REFERENCES students(id),
                    task_template_name VARCHAR NOT NULL,
                    exception_date DATE NOT NULL,
                    reason VARCHAR NOT NULL,
                    created_at DATE DEFAULT CURRENT_DATE
                )
            """))
            
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS recurring_task_templates (
                    id SERIAL PRIMARY KEY,
                    task_name VARCHAR NOT NULL,
                    category VARCHAR NOT NULL,
                    frequency VARCHAR NOT NULL,
                    is_active BOOLEAN DEFAULT true,
                    staff_id INTEGER REFERENCES staff(id),
                    student_id INTEGER REFERENCES students(id),
                    last_generated_date DATE,
                    created_at DATE DEFAULT CURRENT_DATE
                )
            """))
            
            # Add default holidays if they don't exist
            for holiday_date, holiday_name in self.default_holidays:
                result = session.execute(text(
                    "SELECT COUNT(*) FROM school_calendar WHERE date = :date"
                ), {"date": holiday_date})
                
                if result.scalar() == 0:
                    session.execute(text(
                        "INSERT INTO school_calendar (date, event_name, event_type) VALUES (:date, :name, 'holiday')"
                    ), {"date": holiday_date, "name": holiday_name})
            
            # Add default recurring task templates for existing staff
            staff_members = session.query(Staff).all()
            
            default_templates = [
                ('Take classroom attendance', 'Administrative', 'Daily'),
                ('Log therapy minutes', 'Therapy', 'Daily'),
                ('Update progress notes', 'Documentation', 'Daily'),
                ('Weekly progress review', 'Assessment', 'Weekly'),
                ('Monthly IEP review', 'Administrative', 'Monthly'),
                ('Quarterly data collection', 'Assessment', 'Every 9 Weeks')
            ]
            
            for staff in staff_members:
                for task_name, category, frequency in default_templates:
                    result = session.execute(text(
                        "SELECT COUNT(*) FROM recurring_task_templates WHERE task_name = :name AND staff_id = :staff_id"
                    ), {"name": task_name, "staff_id": staff.id})
                    
                    if result.scalar() == 0:
                        session.execute(text(
                            "INSERT INTO recurring_task_templates (task_name, category, frequency, staff_id) VALUES (:name, :category, :frequency, :staff_id)"
                        ), {"name": task_name, "category": category, "frequency": frequency, "staff_id": staff.id})
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            print(f"Error initializing recurring task system: {e}")
        finally:
            session.close()
    
    def is_school_day(self, check_date: date) -> Tuple[bool, Optional[str]]:
        """Check if a given date is a school day"""
        session = self.Session()
        
        try:
            # Check if it's a weekend
            if check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False, "Weekend"
            
            # Check if it's outside school year
            if check_date < self.school_year_start or check_date > self.school_year_end:
                return False, "Outside school year"
            
            # Check if it's a holiday or non-instructional day
            result = session.execute(text(
                "SELECT event_name FROM school_calendar WHERE date = :date"
            ), {"date": check_date})
            
            event = result.fetchone()
            if event:
                return False, event[0]
            
            return True, None
            
        finally:
            session.close()
    
    def should_generate_today(self, frequency: str, check_date: date) -> bool:
        """Determine if a task should be generated today based on frequency"""
        frequency = frequency.lower()
        
        if frequency == 'daily':
            return True
        elif frequency == 'weekly':
            # Generate on Mondays (weekday 0)
            return check_date.weekday() == 0
        elif frequency == 'monthly':
            # Generate on the 1st of each month
            return check_date.day == 1
        elif frequency == 'every 9 weeks':
            # Generate at the start of each grading period
            grading_periods = [
                self.school_year_start,  # Period 1 start
                self.school_year_start + timedelta(weeks=9),  # Period 2 start
                self.school_year_start + timedelta(weeks=18),  # Period 3 start
                self.school_year_start + timedelta(weeks=27),  # Period 4 start
            ]
            return check_date in grading_periods
        
        return False
    
    def generate_recurring_tasks(self, target_date: Optional[date] = None) -> Dict:
        """Generate all recurring tasks for a specific date"""
        if target_date is None:
            target_date = date.today()
        
        session = self.Session()
        results = {
            'date': target_date,
            'is_school_day': False,
            'school_day_reason': None,
            'generated_tasks': [],
            'skipped_tasks': [],
            'exceptions': [],
            'errors': []
        }
        
        try:
            # Check if it's a school day
            is_school_day, reason = self.is_school_day(target_date)
            results['is_school_day'] = is_school_day
            results['school_day_reason'] = reason
            
            if not is_school_day:
                results['skipped_tasks'].append(f"No school day: {reason}")
                results['success'] = True
                results['tasks_created'] = 0
                results['summary'] = f"No school day: {reason}"
                return results
            
            # Get all active recurring task templates
            result = session.execute(text(
                "SELECT id, task_name, category, frequency, staff_id, student_id FROM recurring_task_templates WHERE is_active = true"
            ))
            templates = result.fetchall()
            
            for template in templates:
                try:
                    template_id, task_name, category, frequency, staff_id, student_id = template
                    
                    # Check if we should generate this task today
                    if not self.should_generate_today(frequency, target_date):
                        continue
                    
                    # Check if task already generated today
                    if student_id:
                        existing_check = session.execute(text(
                            "SELECT COUNT(*) FROM tasks WHERE description = :desc AND staff_id = :staff_id AND student_id = :student_id AND deadline = :date"
                        ), {"desc": task_name, "staff_id": staff_id, "student_id": student_id, "date": target_date})
                    else:
                        existing_check = session.execute(text(
                            "SELECT COUNT(*) FROM tasks WHERE description = :desc AND staff_id = :staff_id AND deadline = :date"
                        ), {"desc": task_name, "staff_id": staff_id, "date": target_date})
                    
                    if existing_check.scalar() > 0:
                        staff = session.query(Staff).filter(Staff.id == staff_id).first()
                        staff_name = staff.name if staff else "Unknown Staff"
                        results['skipped_tasks'].append(
                            f"Already exists: {task_name} (Staff: {staff_name})"
                        )
                        continue
                    
                    # Check for exceptions
                    if student_id:
                        exception_check = session.execute(text(
                            "SELECT reason FROM task_exceptions WHERE staff_id = :staff_id AND task_template_name = :task_name AND exception_date = :date AND student_id = :student_id"
                        ), {"staff_id": staff_id, "task_name": task_name, "date": target_date, "student_id": student_id})
                    else:
                        exception_check = session.execute(text(
                            "SELECT reason FROM task_exceptions WHERE staff_id = :staff_id AND task_template_name = :task_name AND exception_date = :date AND student_id IS NULL"
                        ), {"staff_id": staff_id, "task_name": task_name, "date": target_date})
                    
                    exception = exception_check.fetchone()
                    if exception:
                        results['exceptions'].append(
                            f"Exception: {task_name} - {exception[0]}"
                        )
                        continue
                    
                    # Get staff info for logging
                    staff = session.query(Staff).filter(Staff.id == staff_id).first()
                    staff_name = staff.name if staff else "Unknown Staff"
                    
                    # Generate the task
                    if student_id:
                        # Task for specific student
                        student = session.query(Student).filter(Student.id == student_id).first()
                        student_name = student.name if student else "Unknown Student"
                        
                        new_task = Task(
                            description=task_name,
                            category=category,
                            staff_id=staff_id,
                            student_id=student_id,
                            deadline=target_date,
                            completed=False,
                            frequency=frequency
                        )
                        session.add(new_task)
                        
                        results['generated_tasks'].append(
                            f"{task_name} → {student_name} (assigned to {staff_name})"
                        )
                    else:
                        # Task for all students
                        students = session.query(Student).all()
                        
                        for student in students:
                            new_task = Task(
                                description=task_name,
                                category=category,
                                staff_id=staff_id,
                                student_id=student.id,
                                deadline=target_date,
                                completed=False,
                                frequency=frequency
                            )
                            session.add(new_task)
                        
                        results['generated_tasks'].append(
                            f"{task_name} → All students (assigned to {staff_name})"
                        )
                    
                    # Update last generated date
                    session.execute(text(
                        "UPDATE recurring_task_templates SET last_generated_date = :date WHERE id = :id"
                    ), {"date": target_date, "id": template_id})
                    
                except Exception as e:
                    results['errors'].append(f"Error with template {task_name}: {str(e)}")
            
            session.commit()
            
            # Add summary information
            results['success'] = True
            results['tasks_created'] = len(results['generated_tasks'])
            results['summary'] = f"{len(results['generated_tasks'])} tasks generated, {len(results['skipped_tasks'])} skipped, {len(results['exceptions'])} exceptions"
            
        except Exception as e:
            session.rollback()
            results['errors'].append(f"Database error: {str(e)}")
            results['success'] = False
            results['tasks_created'] = 0
            results['summary'] = f"Failed: {str(e)}"
        finally:
            session.close()
        
        return results
    
    def add_task_exception(self, staff_id: int, task_name: str, exception_date: date, 
                          reason: str, student_id: Optional[int] = None) -> bool:
        """Add an exception for a specific task on a specific date"""
        session = self.Session()
        
        try:
            session.execute(text(
                "INSERT INTO task_exceptions (staff_id, student_id, task_template_name, exception_date, reason) VALUES (:staff_id, :student_id, :task_name, :date, :reason)"
            ), {"staff_id": staff_id, "student_id": student_id, "task_name": task_name, "date": exception_date, "reason": reason})
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error adding exception: {e}")
            return False
        finally:
            session.close()
    
    def add_recurring_task_template(self, task_name: str, category: str, frequency: str,
                                   staff_id: int, student_id: Optional[int] = None) -> bool:
        """Add a new recurring task template"""
        session = self.Session()
        
        try:
            session.execute(text(
                "INSERT INTO recurring_task_templates (task_name, category, frequency, staff_id, student_id) VALUES (:task_name, :category, :frequency, :staff_id, :student_id)"
            ), {"task_name": task_name, "category": category, "frequency": frequency, "staff_id": staff_id, "student_id": student_id})
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error adding template: {e}")
            return False
        finally:
            session.close()
    
    def get_recurring_templates(self, staff_id: Optional[int] = None) -> List[tuple]:
        """Get all recurring task templates, optionally filtered by staff"""
        session = self.Session()
        
        try:
            if staff_id:
                result = session.execute(text(
                    "SELECT * FROM recurring_task_templates WHERE staff_id = :staff_id ORDER BY task_name"
                ), {"staff_id": staff_id})
            else:
                result = session.execute(text(
                    "SELECT * FROM recurring_task_templates ORDER BY task_name"
                ))
            
            return result.fetchall()
            
        finally:
            session.close()
    
    def generate_summary_report(self, target_date: Optional[date] = None) -> str:
        """Generate a summary report of recurring task generation"""
        if target_date is None:
            target_date = date.today()
        
        results = self.generate_recurring_tasks(target_date)
        
        report = [
            f"🗓️ Recurring Task Generation Report",
            f"Date: {target_date.strftime('%A, %B %d, %Y')}",
            "=" * 50
        ]
        
        if not results['is_school_day']:
            report.append(f"❌ Not a school day: {results['school_day_reason']}")
            return "\n".join(report)
        
        report.append(f"✅ School day - Processing recurring tasks")
        report.append("")
        
        if results['generated_tasks']:
            report.append(f"📌 Generated Tasks ({len(results['generated_tasks'])}):")
            for task in results['generated_tasks']:
                report.append(f"  • {task}")
            report.append("")
        
        if results['skipped_tasks']:
            report.append(f"⏭️ Skipped Tasks ({len(results['skipped_tasks'])}):")
            for task in results['skipped_tasks']:
                report.append(f"  • {task}")
            report.append("")
        
        if results['exceptions']:
            report.append(f"🚫 Exceptions ({len(results['exceptions'])}):")
            for exception in results['exceptions']:
                report.append(f"  • {exception}")
            report.append("")
        
        if results['errors']:
            report.append(f"❌ Errors ({len(results['errors'])}):")
            for error in results['errors']:
                report.append(f"  • {error}")
            report.append("")
        
        report.append("=" * 50)
        report.append(f"Summary: {len(results['generated_tasks'])} tasks generated, {len(results['skipped_tasks'])} skipped, {len(results['exceptions'])} exceptions")
        
        return "\n".join(report)

def generate_recurring_tasks(target_date: Optional[date] = None) -> Dict:
    """Standalone function to generate recurring tasks"""
    generator = RecurringTaskGenerator()
    return generator.generate_recurring_tasks(target_date)

def run_daily_generation():
    """Main function to run daily recurring task generation"""
    generator = RecurringTaskGenerator()
    print(generator.generate_summary_report())

if __name__ == "__main__":
    print("🔁 Recurring Task Generator")
    print("=" * 40)
    
    generator = RecurringTaskGenerator()
    
    # Test the functionality
    print("\n📊 Testing recurring task generation...")
    
    # Generate today's report
    print(generator.generate_summary_report())
    
    # Show some statistics
    session = SessionLocal()
    try:
        template_result = session.execute(text("SELECT COUNT(*) FROM recurring_task_templates"))
        template_count = template_result.scalar()
        
        exception_result = session.execute(text("SELECT COUNT(*) FROM task_exceptions"))
        exception_count = exception_result.scalar()
        
        calendar_result = session.execute(text("SELECT COUNT(*) FROM school_calendar"))
        calendar_count = calendar_result.scalar()
        
        print(f"\n📈 System Statistics:")
        print(f"  • Recurring task templates: {template_count}")
        print(f"  • Task exceptions: {exception_count}")
        print(f"  • Calendar events: {calendar_count}")
        
    finally:
        session.close()