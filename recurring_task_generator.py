from datetime import datetime, date, timedelta
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from models import Base, engine, Student, Staff, Task, SessionLocal
from typing import Dict, List, Optional, Tuple
import calendar

class SchoolCalendar(Base):
    """Track non-instructional days (holidays, breaks, etc.)"""
    __tablename__ = 'school_calendar'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, unique=True)
    event_name = Column(String, nullable=False)
    event_type = Column(String, default='holiday')  # holiday, break, staff_development, etc.
    description = Column(Text)

class TaskException(Base):
    """Track teacher-declared exceptions for specific tasks on specific days"""
    __tablename__ = 'task_exceptions'
    
    id = Column(Integer, primary_key=True)
    staff_id = Column(Integer, ForeignKey('staff.id'))
    student_id = Column(Integer, ForeignKey('students.id'), nullable=True)
    task_template_name = Column(String, nullable=False)  # Template task name
    exception_date = Column(Date, nullable=False)
    reason = Column(String, nullable=False)
    created_at = Column(Date, default=date.today)
    
    staff_member = relationship("Staff", foreign_keys=[staff_id])
    student = relationship("Student", foreign_keys=[student_id])

class RecurringTaskTemplate(Base):
    """Templates for recurring tasks"""
    __tablename__ = 'recurring_task_templates'
    
    id = Column(Integer, primary_key=True)
    task_name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    frequency = Column(String, nullable=False)  # Daily, Weekly, Monthly, Every 9 Weeks
    is_active = Column(Boolean, default=True)
    staff_id = Column(Integer, ForeignKey('staff.id'))
    student_id = Column(Integer, ForeignKey('students.id'), nullable=True)  # NULL for all students
    last_generated_date = Column(Date)
    created_at = Column(Date, default=date.today)
    
    staff_member = relationship("Staff", foreign_keys=[staff_id])
    student = relationship("Student", foreign_keys=[student_id])

class RecurringTaskGenerator:
    def __init__(self):
        self.Session = SessionLocal
        
        # Create extended tables if they don't exist
        try:
            SchoolCalendar.__table__.create(engine, checkfirst=True)
            TaskException.__table__.create(engine, checkfirst=True)
            RecurringTaskTemplate.__table__.create(engine, checkfirst=True)
        except Exception as e:
            print(f"Tables may already exist: {e}")
        
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
        
        self._initialize_default_data()
    
    def _initialize_default_data(self):
        """Initialize default holidays and recurring task templates"""
        session = self.Session()
        
        try:
            # Add default holidays if they don't exist
            for holiday_date, holiday_name in self.default_holidays:
                existing = session.query(SchoolCalendar).filter(
                    SchoolCalendar.date == datetime.strptime(holiday_date, '%Y-%m-%d').date()
                ).first()
                
                if not existing:
                    holiday = SchoolCalendar(
                        date=datetime.strptime(holiday_date, '%Y-%m-%d').date(),
                        event_name=holiday_name,
                        event_type='holiday'
                    )
                    session.add(holiday)
            
            # Add default recurring task templates if they don't exist
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
                    existing = session.query(RecurringTaskTemplate).filter(
                        RecurringTaskTemplate.task_name == task_name,
                        RecurringTaskTemplate.staff_id == staff.id
                    ).first()
                    
                    if not existing:
                        template = RecurringTaskTemplate(
                            task_name=task_name,
                            category=category,
                            frequency=frequency,
                            staff_id=staff.id
                        )
                        session.add(template)
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            print(f"Error initializing default data: {e}")
        finally:
            session.close()
    
    def is_school_day(self, check_date: date) -> Tuple[bool, Optional[str]]:
        """
        Check if a given date is a school day
        
        Returns:
            Tuple of (is_school_day, reason_if_not)
        """
        session = self.Session()
        
        try:
            # Check if it's a weekend
            if check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False, "Weekend"
            
            # Check if it's outside school year
            if check_date < self.school_year_start or check_date > self.school_year_end:
                return False, "Outside school year"
            
            # Check if it's a holiday or non-instructional day
            calendar_event = session.query(SchoolCalendar).filter(
                SchoolCalendar.date == check_date
            ).first()
            
            if calendar_event:
                return False, calendar_event.event_name
            
            return True, None
            
        finally:
            session.close()
    
    def has_task_exception(self, staff_id: int, task_name: str, check_date: date, 
                          student_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if there's an exception for a specific task on a specific date
        
        Returns:
            Tuple of (has_exception, reason)
        """
        session = self.Session()
        
        try:
            query = session.query(TaskException).filter(
                TaskException.staff_id == staff_id,
                TaskException.task_template_name == task_name,
                TaskException.exception_date == check_date
            )
            
            if student_id:
                query = query.filter(TaskException.student_id == student_id)
            else:
                query = query.filter(TaskException.student_id.is_(None))
            
            exception = query.first()
            
            if exception:
                return True, exception.reason
            
            return False, None
            
        finally:
            session.close()
    
    def task_already_generated(self, template_id: int, check_date: date) -> bool:
        """Check if a task has already been generated for today from this template"""
        session = self.Session()
        
        try:
            template = session.query(RecurringTaskTemplate).filter(
                RecurringTaskTemplate.id == template_id
            ).first()
            
            if not template:
                return True  # If template doesn't exist, consider it "already generated"
            
            # Check if a task with this template's characteristics exists for today
            existing_task = session.query(Task).filter(
                Task.description == template.task_name,
                Task.staff_id == template.staff_id,
                Task.deadline == check_date
            )
            
            if template.student_id:
                existing_task = existing_task.filter(Task.student_id == template.student_id)
            
            return existing_task.first() is not None
            
        finally:
            session.close()
    
    def should_generate_today(self, template: RecurringTaskTemplate, check_date: date) -> bool:
        """Determine if a template should generate a task today based on frequency"""
        if not template.is_active:
            return False
        
        frequency = template.frequency.lower()
        
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
        """
        Generate all recurring tasks for a specific date
        
        Args:
            target_date: Date to generate tasks for (defaults to today)
            
        Returns:
            Dictionary with generation results
        """
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
                return results
            
            # Get all active recurring task templates
            templates = session.query(RecurringTaskTemplate).filter(
                RecurringTaskTemplate.is_active == True
            ).all()
            
            for template in templates:
                try:
                    # Check if we should generate this task today
                    if not self.should_generate_today(template, target_date):
                        continue
                    
                    # Check if task already generated
                    if self.task_already_generated(template.id, target_date):
                        results['skipped_tasks'].append(
                            f"Already exists: {template.task_name} (Staff: {template.staff_member.name})"
                        )
                        continue
                    
                    # Check for exceptions
                    has_exception, exception_reason = self.has_task_exception(
                        template.staff_id, 
                        template.task_name, 
                        target_date, 
                        template.student_id
                    )
                    
                    if has_exception:
                        results['exceptions'].append(
                            f"Exception: {template.task_name} - {exception_reason}"
                        )
                        continue
                    
                    # Get staff and student info for logging
                    staff = session.query(Staff).filter(Staff.id == template.staff_id).first()
                    staff_name = staff.name if staff else "Unknown Staff"
                    
                    # Generate the task
                    if template.student_id:
                        # Task for specific student
                        student = session.query(Student).filter(Student.id == template.student_id).first()
                        student_name = student.name if student else "Unknown Student"
                        
                        new_task = Task(
                            description=template.task_name,
                            category=template.category,
                            staff_id=template.staff_id,
                            student_id=template.student_id,
                            deadline=target_date,
                            completed=False,
                            frequency=template.frequency
                        )
                        session.add(new_task)
                        
                        results['generated_tasks'].append(
                            f"{template.task_name} → {student_name} (assigned to {staff_name})"
                        )
                    else:
                        # Task for all students of this staff member
                        students = session.query(Student).all()
                        
                        for student in students:
                            new_task = Task(
                                description=template.task_name,
                                category=template.category,
                                staff_id=template.staff_id,
                                student_id=student.id,
                                deadline=target_date,
                                completed=False,
                                frequency=template.frequency
                            )
                            session.add(new_task)
                        
                        results['generated_tasks'].append(
                            f"{template.task_name} → All students (assigned to {staff_name})"
                        )
                    
                    # Update last generated date - direct SQL update to avoid ORM issues
                    session.execute(
                        f"UPDATE recurring_task_templates SET last_generated_date = '{target_date}' WHERE id = {template.id}"
                    )
                    
                except Exception as e:
                    results['errors'].append(f"Error with template {template.task_name}: {str(e)}")
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            results['errors'].append(f"Database error: {str(e)}")
        finally:
            session.close()
        
        return results
    
    def add_task_exception(self, staff_id: int, task_name: str, exception_date: date, 
                          reason: str, student_id: Optional[int] = None) -> bool:
        """Add an exception for a specific task on a specific date"""
        session = self.Session()
        
        try:
            exception = TaskException(
                staff_id=staff_id,
                student_id=student_id,
                task_template_name=task_name,
                exception_date=exception_date,
                reason=reason
            )
            session.add(exception)
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
            template = RecurringTaskTemplate(
                task_name=task_name,
                category=category,
                frequency=frequency,
                staff_id=staff_id,
                student_id=student_id
            )
            session.add(template)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error adding template: {e}")
            return False
        finally:
            session.close()
    
    def get_recurring_templates(self, staff_id: Optional[int] = None) -> List[RecurringTaskTemplate]:
        """Get all recurring task templates, optionally filtered by staff"""
        session = self.Session()
        
        try:
            query = session.query(RecurringTaskTemplate)
            
            if staff_id:
                query = query.filter(RecurringTaskTemplate.staff_id == staff_id)
            
            return query.all()
            
        finally:
            session.close()
    
    def get_task_exceptions(self, staff_id: Optional[int] = None, 
                           start_date: Optional[date] = None, 
                           end_date: Optional[date] = None) -> List[TaskException]:
        """Get task exceptions, optionally filtered by staff and date range"""
        session = self.Session()
        
        try:
            query = session.query(TaskException)
            
            if staff_id:
                query = query.filter(TaskException.staff_id == staff_id)
            
            if start_date:
                query = query.filter(TaskException.exception_date >= start_date)
            
            if end_date:
                query = query.filter(TaskException.exception_date <= end_date)
            
            return query.order_by(TaskException.exception_date.desc()).all()
            
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
        template_count = session.query(RecurringTaskTemplate).count()
        exception_count = session.query(TaskException).count()
        calendar_count = session.query(SchoolCalendar).count()
        
        print(f"\n📈 System Statistics:")
        print(f"  • Recurring task templates: {template_count}")
        print(f"  • Task exceptions: {exception_count}")
        print(f"  • Calendar events: {calendar_count}")
        
    finally:
        session.close()