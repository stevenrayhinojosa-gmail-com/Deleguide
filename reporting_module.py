#!/usr/bin/env python3
"""
Weekly SPED Task Report Generator Module

This module generates comprehensive weekly reports for SPED staff, summarizing:
- Task completion status with completion notes
- Missed tasks that weren't completed by due date
- IEP goal coverage mapping based on completed tasks
- Export capabilities to CSV and optional Google Sheets integration

Author: Educational Task Management System
Date: 2025-01-16
"""

import os
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import get_db, Student, Staff, Task
import io


class WeeklyReportGenerator:
    """
    Main class for generating weekly SPED task reports
    """
    
    def __init__(self):
        """Initialize the report generator with database connection"""
        self.db = get_db()
        
        # IEP Goal keywords mapping for goal coverage analysis
        self.goal_keywords = {
            'behavior_regulation': [
                'behavior', 'regulation', 'self-control', 'emotional', 'social skills',
                'anger management', 'impulse control', 'coping strategies', 'ABC data',
                'behavior intervention', 'positive behavior', 'redirect', 'calming'
            ],
            'reading_fluency': [
                'reading', 'fluency', 'phonics', 'decoding', 'comprehension',
                'sight words', 'guided reading', 'reading level', 'literacy',
                'phonemic awareness', 'vocabulary', 'text analysis'
            ],
            'math_skills': [
                'math', 'mathematics', 'calculation', 'problem solving', 'numbers',
                'arithmetic', 'geometry', 'measurement', 'data analysis',
                'algebraic thinking', 'mathematical reasoning'
            ],
            'communication': [
                'communication', 'speech', 'language', 'verbal', 'articulation',
                'AAC', 'sign language', 'communication device', 'expressive',
                'receptive', 'social communication', 'conversation'
            ],
            'fine_motor': [
                'fine motor', 'handwriting', 'pencil grip', 'cutting', 'manipulatives',
                'dexterity', 'coordination', 'writing', 'drawing', 'fine motor skills'
            ],
            'gross_motor': [
                'gross motor', 'physical therapy', 'mobility', 'balance', 'coordination',
                'movement', 'exercise', 'motor planning', 'physical activity'
            ],
            'life_skills': [
                'life skills', 'independence', 'self-care', 'daily living', 'functional',
                'vocational', 'job skills', 'community skills', 'cooking', 'cleaning'
            ],
            'transition': [
                'transition', 'post-secondary', 'career', 'college', 'workplace',
                'independent living', 'community integration', 'job training'
            ]
        }
    
    def get_date_range(self, weeks_back: int = 0) -> Tuple[date, date]:
        """
        Get the date range for the report (default: past 7 days)
        
        Args:
            weeks_back: Number of weeks back from current week (0 = current week)
            
        Returns:
            Tuple of (start_date, end_date)
        """
        today = date.today()
        
        # Calculate start of the target week (Monday)
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday + (weeks_back * 7))
        week_end = week_start + timedelta(days=6)  # Sunday
        
        return week_start, week_end
    
    def get_staff_tasks_in_range(self, staff_id: int, start_date: date, end_date: date) -> List[Dict]:
        """
        Get all tasks for a staff member within date range
        
        Args:
            staff_id: ID of the staff member
            start_date: Start date of the range
            end_date: End date of the range
            
        Returns:
            List of task dictionaries with student and completion info
        """
        query = text("""
            SELECT 
                t.id as task_id,
                t.description as task_name,
                t.category,
                t.deadline,
                t.completed,
                t.completed_at,
                t.completion_note,
                s.name as student_name,
                s.goals as student_goals,
                s.needs as student_needs,
                staff.name as staff_name
            FROM tasks t
            JOIN students s ON t.student_id = s.id
            JOIN staff ON t.staff_id = staff.id
            WHERE t.staff_id = :staff_id
            AND t.deadline BETWEEN :start_date AND :end_date
            ORDER BY t.deadline ASC, s.name ASC
        """)
        
        result = self.db.execute(query, {
            'staff_id': staff_id,
            'start_date': start_date,
            'end_date': end_date
        })
        
        tasks = []
        for row in result:
            tasks.append({
                'task_id': row.task_id,
                'task_name': row.task_name,
                'category': row.category,
                'deadline': row.deadline,
                'completed': row.completed,
                'completed_at': row.completed_at,
                'completion_note': row.completion_note or '',
                'student_name': row.student_name,
                'student_goals': row.student_goals or '',
                'student_needs': row.student_needs or '',
                'staff_name': row.staff_name
            })
        
        return tasks
    
    def categorize_tasks(self, tasks: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Categorize tasks into completed and missed
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            Dictionary with 'completed' and 'missed' task lists
        """
        completed_tasks = []
        missed_tasks = []
        
        for task in tasks:
            if task['completed']:
                completed_tasks.append(task)
            else:
                # Check if task is past due date
                if task['deadline'] < date.today():
                    missed_tasks.append(task)
        
        return {
            'completed': completed_tasks,
            'missed': missed_tasks
        }
    
    def analyze_goal_coverage(self, completed_tasks: List[Dict]) -> Dict[str, Dict]:
        """
        Analyze IEP goal coverage based on completed tasks
        
        Args:
            completed_tasks: List of completed task dictionaries
            
        Returns:
            Dictionary mapping students to their covered goals
        """
        student_goal_coverage = {}
        
        for task in completed_tasks:
            student_name = task['student_name']
            student_goals = task['student_goals'].lower()
            task_description = task['task_name'].lower()
            
            if student_name not in student_goal_coverage:
                student_goal_coverage[student_name] = {
                    'goals_addressed': set(),
                    'task_count': 0,
                    'tasks': []
                }
            
            # Check which goal categories this task supports
            for goal_category, keywords in self.goal_keywords.items():
                for keyword in keywords:
                    if (keyword in task_description or 
                        keyword in student_goals or 
                        keyword in task['category'].lower()):
                        student_goal_coverage[student_name]['goals_addressed'].add(goal_category)
                        break
            
            student_goal_coverage[student_name]['task_count'] += 1
            student_goal_coverage[student_name]['tasks'].append(task)
        
        # Convert sets to lists for JSON serialization
        for student in student_goal_coverage:
            student_goal_coverage[student]['goals_addressed'] = list(
                student_goal_coverage[student]['goals_addressed']
            )
        
        return student_goal_coverage
    
    def generate_weekly_report(self, staff_id: int, start_date: Optional[date] = None, 
                              end_date: Optional[date] = None) -> Dict:
        """
        Generate comprehensive weekly report for a staff member
        
        Args:
            staff_id: ID of the staff member
            start_date: Start date for report (defaults to start of current week)
            end_date: End date for report (defaults to end of current week)
            
        Returns:
            Dictionary containing complete report data
        """
        # Use default date range if not provided
        if start_date is None or end_date is None:
            start_date, end_date = self.get_date_range()
        
        # Get staff information
        staff = self.db.query(Staff).filter(Staff.id == staff_id).first()
        if not staff:
            return {'error': f'Staff member with ID {staff_id} not found'}
        
        # Get all tasks in date range
        tasks = self.get_staff_tasks_in_range(staff_id, start_date, end_date)
        
        # Categorize tasks
        categorized_tasks = self.categorize_tasks(tasks)
        
        # Analyze goal coverage
        goal_coverage = self.analyze_goal_coverage(categorized_tasks['completed'])
        
        # Calculate summary statistics
        total_tasks = len(tasks)
        completed_count = len(categorized_tasks['completed'])
        missed_count = len(categorized_tasks['missed'])
        completion_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        report_data = {
            'staff_name': staff.name,
            'staff_id': staff_id,
            'report_period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'formatted_period': f"{start_date.strftime('%b %d')} – {end_date.strftime('%b %d, %Y')}"
            },
            'summary': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_count,
                'missed_tasks': missed_count,
                'completion_rate': round(completion_rate, 1),
                'students_served': len(goal_coverage)
            },
            'completed_tasks': categorized_tasks['completed'],
            'missed_tasks': categorized_tasks['missed'],
            'goal_coverage': goal_coverage,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return report_data
    
    def generate_master_report(self, start_date: Optional[date] = None, 
                              end_date: Optional[date] = None) -> Dict:
        """
        Generate master report for all staff members
        
        Args:
            start_date: Start date for report (defaults to start of current week)
            end_date: End date for report (defaults to end of current week)
            
        Returns:
            Dictionary containing master report data
        """
        # Use default date range if not provided
        if start_date is None or end_date is None:
            start_date, end_date = self.get_date_range()
        
        # Get all staff members
        all_staff = self.db.query(Staff).all()
        
        staff_reports = []
        master_summary = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'missed_tasks': 0,
            'total_students': 0,
            'staff_count': len(all_staff)
        }
        
        for staff in all_staff:
            staff_report = self.generate_weekly_report(staff.id, start_date, end_date)
            
            if 'error' not in staff_report:
                staff_reports.append(staff_report)
                
                # Add to master summary
                master_summary['total_tasks'] += staff_report['summary']['total_tasks']
                master_summary['completed_tasks'] += staff_report['summary']['completed_tasks']
                master_summary['missed_tasks'] += staff_report['summary']['missed_tasks']
                master_summary['total_students'] += staff_report['summary']['students_served']
        
        # Calculate master completion rate
        if master_summary['total_tasks'] > 0:
            master_summary['completion_rate'] = round(
                master_summary['completed_tasks'] / master_summary['total_tasks'] * 100, 1
            )
        else:
            master_summary['completion_rate'] = 0
        
        return {
            'report_type': 'Master Report',
            'report_period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'formatted_period': f"{start_date.strftime('%b %d')} – {end_date.strftime('%b %d, %Y')}"
            },
            'master_summary': master_summary,
            'staff_reports': staff_reports,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def format_report_text(self, report_data: Dict) -> str:
        """
        Format report data as readable text
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            Formatted text report
        """
        if 'error' in report_data:
            return f"Error: {report_data['error']}"
        
        # Handle master report
        if report_data.get('report_type') == 'Master Report':
            return self._format_master_report_text(report_data)
        
        # Individual staff report
        text_report = []
        
        # Header
        text_report.append(f"Weekly Report for {report_data['staff_name']}")
        text_report.append(f"Period: {report_data['report_period']['formatted_period']}")
        text_report.append("=" * 60)
        
        # Summary
        summary = report_data['summary']
        text_report.append(f"\n📊 SUMMARY:")
        text_report.append(f"   Total Tasks: {summary['total_tasks']}")
        text_report.append(f"   Completed: {summary['completed_tasks']} ({summary['completion_rate']}%)")
        text_report.append(f"   Missed: {summary['missed_tasks']}")
        text_report.append(f"   Students Served: {summary['students_served']}")
        
        # Completed Tasks
        text_report.append(f"\n✅ COMPLETED TASKS ({len(report_data['completed_tasks'])}):")
        if report_data['completed_tasks']:
            for task in report_data['completed_tasks']:
                completion_date = task['completed_at'].strftime('%b %d') if task['completed_at'] else 'Unknown'
                note_text = f" (\"{task['completion_note']}\")" if task['completion_note'] else ""
                text_report.append(f"   • {task['student_name']} → {task['task_name']} → {completion_date}{note_text}")
        else:
            text_report.append("   No completed tasks")
        
        # Missed Tasks
        text_report.append(f"\n❌ MISSED TASKS ({len(report_data['missed_tasks'])}):")
        if report_data['missed_tasks']:
            for task in report_data['missed_tasks']:
                due_date = task['deadline'].strftime('%b %d')
                text_report.append(f"   • {task['student_name']} → {task['task_name']} (Due: {due_date})")
        else:
            text_report.append("   No missed tasks")
        
        # Goal Coverage
        text_report.append(f"\n🎯 IEP GOAL COVERAGE:")
        if report_data['goal_coverage']:
            for student_name, coverage in report_data['goal_coverage'].items():
                goals_text = ", ".join([goal.replace('_', ' ').title() for goal in coverage['goals_addressed']])
                text_report.append(f"   • {student_name} → {goals_text} ✅ ({coverage['task_count']} tasks)")
        else:
            text_report.append("   No goal coverage data available")
        
        text_report.append(f"\nReport generated: {report_data['generated_at']}")
        
        return "\n".join(text_report)
    
    def _format_master_report_text(self, master_data: Dict) -> str:
        """Format master report as readable text"""
        text_report = []
        
        # Header
        text_report.append("MASTER WEEKLY REPORT - ALL STAFF")
        text_report.append(f"Period: {master_data['report_period']['formatted_period']}")
        text_report.append("=" * 60)
        
        # Master Summary
        summary = master_data['master_summary']
        text_report.append(f"\n📊 OVERALL SUMMARY:")
        text_report.append(f"   Staff Members: {summary['staff_count']}")
        text_report.append(f"   Total Tasks: {summary['total_tasks']}")
        text_report.append(f"   Completed: {summary['completed_tasks']} ({summary['completion_rate']}%)")
        text_report.append(f"   Missed: {summary['missed_tasks']}")
        text_report.append(f"   Students Served: {summary['total_students']}")
        
        # Individual Staff Reports
        text_report.append(f"\n👥 STAFF BREAKDOWN:")
        for staff_report in master_data['staff_reports']:
            staff_summary = staff_report['summary']
            text_report.append(f"\n   {staff_report['staff_name']}:")
            text_report.append(f"     Completed: {staff_summary['completed_tasks']}/{staff_summary['total_tasks']} ({staff_summary['completion_rate']}%)")
            text_report.append(f"     Missed: {staff_summary['missed_tasks']}")
            text_report.append(f"     Students: {staff_summary['students_served']}")
        
        text_report.append(f"\nReport generated: {master_data['generated_at']}")
        
        return "\n".join(text_report)
    
    def export_report_to_csv(self, report_data: Dict, filename: Optional[str] = None) -> str:
        """
        Export report data to CSV file
        
        Args:
            report_data: Report data dictionary
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Filename of the exported CSV file
        """
        if 'error' in report_data:
            raise ValueError(f"Cannot export report with error: {report_data['error']}")
        
        # Generate filename if not provided
        if filename is None:
            if report_data.get('report_type') == 'Master Report':
                filename = f"master_report_{report_data['report_period']['start_date']}_to_{report_data['report_period']['end_date']}.csv"
            else:
                staff_name = report_data['staff_name'].replace(' ', '_').replace('.', '')
                filename = f"{staff_name}_report_{report_data['report_period']['start_date']}_to_{report_data['report_period']['end_date']}.csv"
        
        # Prepare data for CSV export
        csv_data = []
        
        if report_data.get('report_type') == 'Master Report':
            # Export master report
            for staff_report in report_data['staff_reports']:
                for task in staff_report['completed_tasks'] + staff_report['missed_tasks']:
                    csv_data.append({
                        'Staff Name': staff_report['staff_name'],
                        'Student Name': task['student_name'],
                        'Task Name': task['task_name'],
                        'Category': task['category'],
                        'Due Date': task['deadline'],
                        'Status': 'Completed' if task['completed'] else 'Missed',
                        'Completion Date': task['completed_at'] if task['completed_at'] else '',
                        'Completion Note': task['completion_note'],
                        'Report Period': report_data['report_period']['formatted_period']
                    })
        else:
            # Export individual staff report
            for task in report_data['completed_tasks'] + report_data['missed_tasks']:
                csv_data.append({
                    'Staff Name': report_data['staff_name'],
                    'Student Name': task['student_name'],
                    'Task Name': task['task_name'],
                    'Category': task['category'],
                    'Due Date': task['deadline'],
                    'Status': 'Completed' if task['completed'] else 'Missed',
                    'Completion Date': task['completed_at'] if task['completed_at'] else '',
                    'Completion Note': task['completion_note'],
                    'Report Period': report_data['report_period']['formatted_period']
                })
        
        # Create DataFrame and export to CSV
        df = pd.DataFrame(csv_data)
        df.to_csv(filename, index=False)
        
        return filename
    
    def export_summary_to_csv(self, report_data: Dict, filename: Optional[str] = None) -> str:
        """
        Export summary statistics to CSV
        
        Args:
            report_data: Report data dictionary
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Filename of the exported CSV file
        """
        if filename is None:
            if report_data.get('report_type') == 'Master Report':
                filename = f"master_summary_{report_data['report_period']['start_date']}.csv"
            else:
                staff_name = report_data['staff_name'].replace(' ', '_').replace('.', '')
                filename = f"{staff_name}_summary_{report_data['report_period']['start_date']}.csv"
        
        summary_data = []
        
        if report_data.get('report_type') == 'Master Report':
            # Export master summary
            for staff_report in report_data['staff_reports']:
                summary_data.append({
                    'Staff Name': staff_report['staff_name'],
                    'Total Tasks': staff_report['summary']['total_tasks'],
                    'Completed Tasks': staff_report['summary']['completed_tasks'],
                    'Missed Tasks': staff_report['summary']['missed_tasks'],
                    'Completion Rate (%)': staff_report['summary']['completion_rate'],
                    'Students Served': staff_report['summary']['students_served'],
                    'Report Period': report_data['report_period']['formatted_period']
                })
        else:
            # Export individual summary
            summary_data.append({
                'Staff Name': report_data['staff_name'],
                'Total Tasks': report_data['summary']['total_tasks'],
                'Completed Tasks': report_data['summary']['completed_tasks'],
                'Missed Tasks': report_data['summary']['missed_tasks'],
                'Completion Rate (%)': report_data['summary']['completion_rate'],
                'Students Served': report_data['summary']['students_served'],
                'Report Period': report_data['report_period']['formatted_period']
            })
        
        df = pd.DataFrame(summary_data)
        df.to_csv(filename, index=False)
        
        return filename


def generate_weekly_report(staff_id: int, start_date: Optional[date] = None, 
                          end_date: Optional[date] = None) -> Dict:
    """
    Standalone function to generate weekly report for a staff member
    
    Args:
        staff_id: ID of the staff member
        start_date: Start date for report (defaults to start of current week)
        end_date: End date for report (defaults to end of current week)
        
    Returns:
        Dictionary containing report data
    """
    generator = WeeklyReportGenerator()
    return generator.generate_weekly_report(staff_id, start_date, end_date)


def generate_master_report(start_date: Optional[date] = None, 
                          end_date: Optional[date] = None) -> Dict:
    """
    Standalone function to generate master report for all staff
    
    Args:
        start_date: Start date for report (defaults to start of current week)
        end_date: End date for report (defaults to end of current week)
        
    Returns:
        Dictionary containing master report data
    """
    generator = WeeklyReportGenerator()
    return generator.generate_master_report(start_date, end_date)


def export_report_to_csv(report_data: Dict, filename: Optional[str] = None) -> str:
    """
    Standalone function to export report to CSV
    
    Args:
        report_data: Report data dictionary
        filename: Optional filename
        
    Returns:
        Filename of exported CSV
    """
    generator = WeeklyReportGenerator()
    return generator.export_report_to_csv(report_data, filename)


def print_weekly_report(staff_id: int, start_date: Optional[date] = None, 
                       end_date: Optional[date] = None):
    """
    Generate and print weekly report to console
    
    Args:
        staff_id: ID of the staff member
        start_date: Start date for report
        end_date: End date for report
    """
    generator = WeeklyReportGenerator()
    report_data = generator.generate_weekly_report(staff_id, start_date, end_date)
    formatted_report = generator.format_report_text(report_data)
    print(formatted_report)


def print_master_report(start_date: Optional[date] = None, 
                       end_date: Optional[date] = None):
    """
    Generate and print master report to console
    
    Args:
        start_date: Start date for report
        end_date: End date for report
    """
    generator = WeeklyReportGenerator()
    report_data = generator.generate_master_report(start_date, end_date)
    formatted_report = generator.format_report_text(report_data)
    print(formatted_report)


def demo_weekly_reports():
    """
    Demo function to show weekly report generation capabilities
    """
    print("🔄 Generating Weekly SPED Task Reports Demo...\n")
    
    generator = WeeklyReportGenerator()
    
    # Get all staff for demo
    db = get_db()
    all_staff = db.query(Staff).all()
    
    if not all_staff:
        print("❌ No staff members found in database")
        return
    
    # Generate individual report for first staff member
    first_staff = all_staff[0]
    print(f"📋 Individual Report for {first_staff.name}:")
    print("-" * 50)
    individual_report = generator.generate_weekly_report(first_staff.id)
    print(generator.format_report_text(individual_report))
    
    print("\n" + "="*60 + "\n")
    
    # Generate master report
    print("📊 Master Report for All Staff:")
    print("-" * 50)
    master_report = generator.generate_master_report()
    print(generator.format_report_text(master_report))
    
    # Export examples
    print(f"\n📤 Export Examples:")
    try:
        individual_csv = generator.export_report_to_csv(individual_report)
        print(f"   ✅ Individual report exported: {individual_csv}")
        
        master_csv = generator.export_report_to_csv(master_report)
        print(f"   ✅ Master report exported: {master_csv}")
        
        summary_csv = generator.export_summary_to_csv(master_report)
        print(f"   ✅ Summary report exported: {summary_csv}")
        
    except Exception as e:
        print(f"   ❌ Export error: {e}")
    
    print(f"\n✅ Weekly report generation demo completed!")


if __name__ == "__main__":
    """
    Run the weekly report demo when script is executed directly
    """
    demo_weekly_reports()