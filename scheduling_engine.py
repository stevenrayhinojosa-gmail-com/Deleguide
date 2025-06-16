from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import sessionmaker
from models import engine, Student, Staff, Task
from typing import Dict, Optional, Tuple
import calendar

class TaskSchedulingEngine:
    def __init__(self):
        self.Session = sessionmaker(bind=engine)
        
        # School year configuration (can be customized)
        self.school_year_start = date(2024, 8, 26)  # Typical late August start
        self.school_year_end = date(2025, 6, 6)     # Typical early June end
        
        # Define 9-week grading periods
        self.grading_periods = self._calculate_grading_periods()
        
        # Monthly scheduling preferences
        self.monthly_day_preference = 1  # Default to 1st of month (can be 1 or 15)
        
        # ARD scheduling buffer (weeks before ARD)
        self.ard_buffer_weeks = 3
    
    def _calculate_grading_periods(self) -> list:
        """Calculate the 9-week grading periods for the school year"""
        periods = []
        current_start = self.school_year_start
        
        for period_num in range(1, 5):  # 4 grading periods
            period_end = current_start + timedelta(weeks=9) - timedelta(days=1)
            
            # Adjust if it goes beyond school year
            if period_end > self.school_year_end:
                period_end = self.school_year_end
            
            periods.append({
                'period': period_num,
                'start_date': current_start,
                'end_date': period_end
            })
            
            current_start = period_end + timedelta(days=1)
            
            # Stop if we've reached the end of school year
            if current_start > self.school_year_end:
                break
        
        return periods
    
    def calculate_due_date(self, task: Task, student: Student) -> Dict:
        """
        Calculate the due date for a task based on its frequency and student's ARD date
        
        Args:
            task: Task object with frequency information
            student: Student object with ARD date
            
        Returns:
            Dictionary with task info, due_date, and reason
        """
        frequency = task.frequency.lower() if task.frequency else 'once'
        today = date.today()
        
        result = {
            'task_id': task.id,
            'task_name': task.description,
            'frequency': task.frequency,
            'student_name': student.name,
            'due_date': None,
            'reason': '',
            'calculation_details': {}
        }
        
        if frequency == 'daily':
            result['due_date'] = today
            result['reason'] = 'Daily task - due today'
            
        elif frequency == 'every 9 weeks':
            due_date, period_info = self._calculate_nine_week_due_date(today)
            result['due_date'] = due_date
            result['reason'] = f'Every 9 weeks - due at end of grading period {period_info["period"]}'
            result['calculation_details'] = period_info
            
        elif frequency == 'once a month':
            due_date, month_info = self._calculate_monthly_due_date(today)
            result['due_date'] = due_date
            result['reason'] = f'Monthly task - due on {self.monthly_day_preference}{"st" if self.monthly_day_preference == 1 else "th"} of month'
            result['calculation_details'] = month_info
            
        elif frequency == 'once a year':
            if student.ard_date:
                due_date, ard_info = self._calculate_ard_based_due_date(student.ard_date, today)
                result['due_date'] = due_date
                result['reason'] = f'Once a year task - due {self.ard_buffer_weeks} weeks before ARD'
                result['calculation_details'] = ard_info
            else:
                # Default to end of school year if no ARD date
                result['due_date'] = self.school_year_end - timedelta(weeks=4)
                result['reason'] = 'Once a year task - due 4 weeks before school year end (no ARD date set)'
                
        else:  # 'once' or other frequencies
            # Default to 1 week from task creation/assignment
            result['due_date'] = today + timedelta(weeks=1)
            result['reason'] = 'One-time task - due in 1 week'
        
        return result
    
    def _calculate_nine_week_due_date(self, reference_date: date) -> Tuple[date, Dict]:
        """Calculate due date for 9-week frequency tasks"""
        current_period = None
        
        # Find which grading period we're currently in
        for period in self.grading_periods:
            if period['start_date'] <= reference_date <= period['end_date']:
                current_period = period
                break
        
        if current_period:
            # Due at the end of current grading period
            due_date = current_period['end_date']
            period_info = {
                'period': current_period['period'],
                'period_start': current_period['start_date'],
                'period_end': current_period['end_date'],
                'days_remaining': (current_period['end_date'] - reference_date).days
            }
        else:
            # If not in a grading period, find the next one
            next_period = None
            for period in self.grading_periods:
                if period['start_date'] > reference_date:
                    next_period = period
                    break
            
            if next_period:
                due_date = next_period['end_date']
                period_info = {
                    'period': next_period['period'],
                    'period_start': next_period['start_date'],
                    'period_end': next_period['end_date'],
                    'days_until_start': (next_period['start_date'] - reference_date).days
                }
            else:
                # Default to end of school year
                due_date = self.school_year_end
                period_info = {
                    'period': 'End of Year',
                    'period_start': self.school_year_start,
                    'period_end': self.school_year_end,
                    'note': 'No more grading periods this year'
                }
        
        return due_date, period_info
    
    def _calculate_monthly_due_date(self, reference_date: date) -> Tuple[date, Dict]:
        """Calculate due date for monthly frequency tasks"""
        today = reference_date
        
        # Calculate next occurrence of the preferred day
        if self.monthly_day_preference == 1:
            # First of next month
            if today.day == 1:
                # If today is the 1st, next due date is next month's 1st
                next_month = today + relativedelta(months=1)
                due_date = next_month.replace(day=1)
            else:
                # Next 1st of current month or next month
                try:
                    due_date = today.replace(day=1) + relativedelta(months=1)
                except ValueError:
                    due_date = today + relativedelta(months=1, day=1)
        else:
            # 15th of month
            try:
                if today.day <= 15:
                    due_date = today.replace(day=15)
                else:
                    due_date = today.replace(day=15) + relativedelta(months=1)
            except ValueError:
                due_date = today + relativedelta(months=1, day=15)
        
        month_info = {
            'target_day': self.monthly_day_preference,
            'current_month': today.strftime('%B %Y'),
            'due_month': due_date.strftime('%B %Y'),
            'days_until_due': (due_date - today).days
        }
        
        return due_date, month_info
    
    def _calculate_ard_based_due_date(self, ard_date: date, reference_date: date) -> Tuple[date, Dict]:
        """Calculate due date based on ARD date (3 weeks before)"""
        due_date = ard_date - timedelta(weeks=self.ard_buffer_weeks)
        
        # If the calculated due date is in the past, schedule for next year's ARD
        if due_date < reference_date:
            next_ard = ard_date + relativedelta(years=1)
            due_date = next_ard - timedelta(weeks=self.ard_buffer_weeks)
        
        ard_info = {
            'ard_date': ard_date,
            'buffer_weeks': self.ard_buffer_weeks,
            'days_until_ard': (ard_date - reference_date).days,
            'days_until_due': (due_date - reference_date).days,
            'ard_year': ard_date.year
        }
        
        return due_date, ard_info
    
    def calculate_all_task_due_dates(self, student_id: Optional[int] = None) -> list:
        """Calculate due dates for all tasks, optionally filtered by student"""
        session = self.Session()
        
        try:
            if student_id:
                tasks = session.query(Task).filter(
                    Task.student_id == student_id,
                    Task.completed == False
                ).all()
            else:
                tasks = session.query(Task).filter(Task.completed == False).all()
            
            results = []
            
            for task in tasks:
                student = task.student
                if student:
                    calculation = self.calculate_due_date(task, student)
                    results.append(calculation)
            
            return results
            
        finally:
            session.close()
    
    def get_tasks_due_soon(self, days_ahead: int = 7) -> list:
        """Get tasks due within specified number of days"""
        all_calculations = self.calculate_all_task_due_dates()
        today = date.today()
        cutoff_date = today + timedelta(days=days_ahead)
        
        due_soon = []
        for calc in all_calculations:
            if calc['due_date'] and calc['due_date'] <= cutoff_date:
                calc['urgency_days'] = (calc['due_date'] - today).days
                due_soon.append(calc)
        
        # Sort by due date (most urgent first)
        due_soon.sort(key=lambda x: x['due_date'])
        
        return due_soon
    
    def update_task_deadlines(self, auto_update: bool = False) -> Dict:
        """Update task deadlines in database based on calculated due dates"""
        session = self.Session()
        
        try:
            updated_tasks = []
            calculations = self.calculate_all_task_due_dates()
            
            for calc in calculations:
                task = session.query(Task).filter(Task.id == calc['task_id']).first()
                if task and calc['due_date']:
                    old_deadline = task.deadline
                    new_deadline = calc['due_date']
                    
                    if old_deadline != new_deadline:
                        if auto_update:
                            task.deadline = new_deadline
                            updated_tasks.append({
                                'task_id': task.id,
                                'task_name': task.description,
                                'old_deadline': old_deadline,
                                'new_deadline': new_deadline,
                                'reason': calc['reason']
                            })
                        else:
                            updated_tasks.append({
                                'task_id': task.id,
                                'task_name': task.description,
                                'current_deadline': old_deadline,
                                'suggested_deadline': new_deadline,
                                'reason': calc['reason'],
                                'needs_update': True
                            })
            
            if auto_update and updated_tasks:
                session.commit()
                
            return {
                'updated_count': len(updated_tasks),
                'auto_updated': auto_update,
                'tasks': updated_tasks
            }
            
        finally:
            session.close()
    
    def generate_scheduling_report(self, student_id: Optional[int] = None) -> str:
        """Generate a comprehensive scheduling report"""
        calculations = self.calculate_all_task_due_dates(student_id)
        
        if student_id:
            session = self.Session()
            try:
                student = session.query(Student).filter(Student.id == student_id).first()
                student_name = student.name if student else f"Student ID {student_id}"
            finally:
                session.close()
            report_title = f"📅 Task Scheduling Report for {student_name}"
        else:
            report_title = "📅 Task Scheduling Report - All Students"
        
        report = [report_title]
        report.append("=" * len(report_title))
        report.append("")
        
        # Group by frequency
        freq_groups = {}
        for calc in calculations:
            freq = calc['frequency'] or 'Once'
            if freq not in freq_groups:
                freq_groups[freq] = []
            freq_groups[freq].append(calc)
        
        for frequency, tasks in freq_groups.items():
            report.append(f"## {frequency.upper()} TASKS ({len(tasks)} tasks)")
            report.append("-" * 40)
            
            # Sort tasks by due date
            tasks.sort(key=lambda x: x['due_date'] if x['due_date'] else date.max)
            
            for task in tasks:
                due_date_str = task['due_date'].strftime('%Y-%m-%d') if task['due_date'] else 'TBD'
                days_until = (task['due_date'] - date.today()).days if task['due_date'] else None
                
                urgency = ""
                if days_until is not None:
                    if days_until < 0:
                        urgency = " ⚠️ OVERDUE"
                    elif days_until <= 3:
                        urgency = " 🔴 URGENT"
                    elif days_until <= 7:
                        urgency = " 🟡 SOON"
                
                report.append(f"• {task['task_name']} ({task['student_name']})")
                report.append(f"  Due: {due_date_str}{urgency}")
                report.append(f"  Reason: {task['reason']}")
                
                if task.get('calculation_details'):
                    details = task['calculation_details']
                    if 'period' in details:
                        report.append(f"  Grading Period: {details['period']}")
                    if 'ard_date' in details:
                        report.append(f"  ARD Date: {details['ard_date']}")
                
                report.append("")
        
        # Summary statistics
        report.append("## SUMMARY")
        report.append("-" * 20)
        report.append(f"Total Tasks: {len(calculations)}")
        
        overdue = len([c for c in calculations if c['due_date'] and c['due_date'] < date.today()])
        urgent = len([c for c in calculations if c['due_date'] and 0 <= (c['due_date'] - date.today()).days <= 3])
        soon = len([c for c in calculations if c['due_date'] and 4 <= (c['due_date'] - date.today()).days <= 7])
        
        report.append(f"Overdue: {overdue}")
        report.append(f"Due in 1-3 days: {urgent}")
        report.append(f"Due in 4-7 days: {soon}")
        
        return "\n".join(report)

def calculate_due_date(task: Task, student: Student) -> Dict:
    """Standalone function for calculating due dates"""
    engine = TaskSchedulingEngine()
    return engine.calculate_due_date(task, student)

def get_tasks_due_soon(days_ahead: int = 7) -> list:
    """Standalone function for getting tasks due soon"""
    engine = TaskSchedulingEngine()
    return engine.get_tasks_due_soon(days_ahead)

def generate_scheduling_report(student_id: Optional[int] = None) -> str:
    """Standalone function for generating scheduling reports"""
    engine = TaskSchedulingEngine()
    return engine.generate_scheduling_report(student_id)

if __name__ == "__main__":
    # CLI interface for testing
    print("📅 Task Scheduling Engine")
    print("=" * 40)
    
    engine = TaskSchedulingEngine()
    
    # Display grading periods
    print("\n🗓️ Grading Periods:")
    for period in engine.grading_periods:
        print(f"Period {period['period']}: {period['start_date']} to {period['end_date']}")
    
    # Generate and display full report
    print("\n" + engine.generate_scheduling_report())
    
    # Show tasks due soon
    print("\n🚨 Tasks Due Soon (Next 7 Days):")
    due_soon = engine.get_tasks_due_soon(7)
    
    if due_soon:
        for task in due_soon:
            urgency_emoji = "🔴" if task['urgency_days'] <= 3 else "🟡"
            print(f"{urgency_emoji} {task['task_name']} ({task['student_name']}) - Due: {task['due_date']} ({task['urgency_days']} days)")
    else:
        print("✅ No tasks due in the next 7 days.")