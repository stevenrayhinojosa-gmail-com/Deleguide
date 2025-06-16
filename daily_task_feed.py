from datetime import datetime, date, timedelta
from sqlalchemy.orm import sessionmaker
from models import engine, Student, Staff, Task
import calendar

class DailyTaskFeedGenerator:
    def __init__(self):
        self.Session = sessionmaker(bind=engine)
    
    def get_today_tasks(self, staff_id):
        """Get all tasks due today for a specific staff member"""
        session = self.Session()
        today = date.today()
        
        try:
            # Get all tasks assigned to this staff member
            tasks = session.query(Task).filter(
                Task.staff_id == staff_id,
                Task.completed == False
            ).all()
            
            today_tasks = []
            
            for task in tasks:
                if self._is_task_due_today(task, today):
                    today_tasks.append(task)
            
            return today_tasks
            
        finally:
            session.close()
    
    def _is_task_due_today(self, task, today):
        """Check if a task is due today based on its frequency"""
        frequency = task.frequency.lower() if task.frequency else 'once'
        
        if frequency == 'daily':
            return True
        
        elif frequency == 'every 9 weeks':
            # Check if today matches the 9-week cycle
            # Assuming tasks start from the beginning of school year (September 1st)
            school_year_start = date(today.year, 9, 1)
            if today < school_year_start:
                school_year_start = date(today.year - 1, 9, 1)
            
            days_since_start = (today - school_year_start).days
            return days_since_start % (9 * 7) == 0
        
        elif frequency == 'once a month':
            # Task is due within first 7 days of the month
            return today.day <= 7
        
        elif frequency == 'once a year':
            # Task is due if ARD is within 21 days
            if task.student and task.student.ard_date:
                days_until_ard = (task.student.ard_date - today).days
                return 0 <= days_until_ard <= 21
            return False
        
        else:  # 'once' or other frequencies
            # Check if task deadline is today
            return task.deadline == today
    
    def get_days_until_ard(self, student_id):
        """Get number of days until student's ARD date"""
        session = self.Session()
        today = date.today()
        
        try:
            student = session.query(Student).filter(Student.id == student_id).first()
            if student and student.ard_date:
                days_until = (student.ard_date - today).days
                return days_until if days_until >= 0 else None
            return None
        finally:
            session.close()
    
    def generate_daily_feed(self):
        """Generate the complete daily task feed for all staff members"""
        session = self.Session()
        today = date.today()
        
        try:
            # Get all staff members
            staff_members = session.query(Staff).all()
            
            feed_output = []
            feed_output.append(f"📅 Daily Task Feed for {today.strftime('%Y-%m-%d')}")
            feed_output.append("=" * 50)
            
            for staff_member in staff_members:
                today_tasks = self.get_today_tasks(staff_member.id)
                
                if today_tasks:
                    feed_output.append(f"\n🧑‍🏫 Teacher: {staff_member.name}")
                    feed_output.append(f"📅 Tasks for {today.strftime('%Y-%m-%d')}:")
                    feed_output.append("")
                    
                    for task in today_tasks:
                        student_name = task.student.name if task.student else "Unknown Student"
                        task_line = f"{student_name} → {task.description}"
                        
                        # Add ARD countdown if applicable
                        if task.student and task.student.ard_date:
                            days_until_ard = self.get_days_until_ard(task.student.id)
                            if days_until_ard is not None and days_until_ard <= 21:
                                task_line += f" (ARD in {days_until_ard} days)"
                        
                        feed_output.append(task_line)
                    
                    feed_output.append("")
            
            if len([line for line in feed_output if line.startswith("🧑‍🏫")]) == 0:
                feed_output.append("\n✅ No tasks due today for any staff members.")
            
            return "\n".join(feed_output)
            
        finally:
            session.close()
    
    def get_staff_task_summary(self, staff_id):
        """Get a summary of tasks for a specific staff member"""
        session = self.Session()
        today = date.today()
        
        try:
            staff_member = session.query(Staff).filter(Staff.id == staff_id).first()
            if not staff_member:
                return "Staff member not found."
            
            today_tasks = self.get_today_tasks(staff_id)
            
            summary = []
            summary.append(f"🧑‍🏫 {staff_member.name}'s Tasks for {today.strftime('%Y-%m-%d')}")
            summary.append("-" * 40)
            
            if today_tasks:
                for task in today_tasks:
                    student_name = task.student.name if task.student else "Unknown Student"
                    task_info = f"• {student_name}: {task.description}"
                    
                    # Add frequency info
                    if task.frequency and task.frequency.lower() != 'once':
                        task_info += f" ({task.frequency})"
                    
                    # Add ARD countdown if applicable
                    if task.student and task.student.ard_date:
                        days_until_ard = self.get_days_until_ard(task.student.id)
                        if days_until_ard is not None and days_until_ard <= 21:
                            task_info += f" - ARD in {days_until_ard} days"
                    
                    summary.append(task_info)
            else:
                summary.append("✅ No tasks due today.")
            
            return "\n".join(summary)
            
        finally:
            session.close()

def run_daily_feed():
    """Main function to run the daily task feed generator"""
    generator = DailyTaskFeedGenerator()
    feed = generator.generate_daily_feed()
    print(feed)
    return feed

def run_staff_summary(staff_id):
    """Get task summary for a specific staff member"""
    generator = DailyTaskFeedGenerator()
    summary = generator.get_staff_task_summary(staff_id)
    print(summary)
    return summary

if __name__ == "__main__":
    # Run the daily feed when executed directly
    run_daily_feed()