#!/usr/bin/env python3
"""
Teacher Interface Module for Educational Task Management System

This module provides functionality for SPED teachers to:
- View their daily task assignments
- Mark tasks as completed with optional notes
- Track completion history and timestamps
- Manage task workflow efficiently

Author: Educational Task Management System
Date: 2025-01-16
"""

import os
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Student, Staff, Task, get_db

class TeacherTaskInterface:
    """
    Main class for handling teacher task interactions
    """
    
    def __init__(self):
        """Initialize the teacher interface with database connection"""
        self.db = get_db()
        
    def get_teacher_by_name(self, teacher_name: str) -> Optional[Staff]:
        """
        Get teacher/staff record by name
        
        Args:
            teacher_name: Name of the teacher
            
        Returns:
            Staff object or None if not found
        """
        try:
            return self.db.query(Staff).filter(Staff.name.ilike(f"%{teacher_name}%")).first()
        except Exception as e:
            print(f"Error finding teacher: {str(e)}")
            return None
    
    def get_all_teachers(self) -> List[Staff]:
        """Get all available teachers/staff"""
        try:
            return self.db.query(Staff).all()
        except Exception as e:
            print(f"Error getting teachers: {str(e)}")
            return []
    
    def get_tasks_for_today(self, staff_id: int, target_date: Optional[date] = None) -> List[Dict]:
        """
        Get all tasks assigned to a teacher for today (or specified date)
        
        Args:
            staff_id: ID of the staff member
            target_date: Date to check for tasks (defaults to today)
            
        Returns:
            List of task dictionaries with student and task information
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            # Query for tasks assigned to this teacher for the specified date
            query = """
            SELECT 
                t.id as task_id,
                t.description as task_name,
                t.category,
                t.deadline,
                t.completed,
                t.completion_note,
                t.completed_at,
                t.frequency,
                s.name as student_name,
                s.id as student_id,
                st.name as staff_name
            FROM tasks t
            JOIN students s ON t.student_id = s.id
            JOIN staff st ON t.staff_id = st.id
            WHERE t.staff_id = :staff_id 
            AND t.deadline = :target_date
            ORDER BY t.completed ASC, t.category ASC, s.name ASC
            """
            
            result = self.db.execute(text(query), {
                "staff_id": staff_id, 
                "target_date": target_date
            })
            
            tasks = []
            for row in result:
                task_dict = {
                    'task_id': row.task_id,
                    'task_name': row.task_name,
                    'category': row.category,
                    'deadline': row.deadline,
                    'completed': row.completed,
                    'completion_note': row.completion_note,
                    'completed_at': row.completed_at,
                    'frequency': row.frequency,
                    'student_name': row.student_name,
                    'student_id': row.student_id,
                    'staff_name': row.staff_name
                }
                tasks.append(task_dict)
            
            return tasks
            
        except Exception as e:
            print(f"Error getting tasks for today: {str(e)}")
            return []
    
    def get_pending_tasks(self, staff_id: int, target_date: Optional[date] = None) -> List[Dict]:
        """
        Get only pending (incomplete) tasks for a teacher
        
        Args:
            staff_id: ID of the staff member
            target_date: Date to check for tasks (defaults to today)
            
        Returns:
            List of pending task dictionaries
        """
        all_tasks = self.get_tasks_for_today(staff_id, target_date)
        return [task for task in all_tasks if not task['completed']]
    
    def get_completed_tasks(self, staff_id: int, target_date: Optional[date] = None) -> List[Dict]:
        """
        Get only completed tasks for a teacher
        
        Args:
            staff_id: ID of the staff member
            target_date: Date to check for tasks (defaults to today)
            
        Returns:
            List of completed task dictionaries
        """
        all_tasks = self.get_tasks_for_today(staff_id, target_date)
        return [task for task in all_tasks if task['completed']]
    
    def mark_task_complete(self, task_id: int, completion_note: Optional[str] = None, 
                          completed_by: Optional[str] = None) -> bool:
        """
        Mark a task as completed with optional note and timestamp
        
        Args:
            task_id: ID of the task to complete
            completion_note: Optional note about the task completion
            completed_by: Name of the person completing the task
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the task
            task = self.db.query(Task).filter(Task.id == task_id).first()
            
            if not task:
                print(f"Task with ID {task_id} not found")
                return False
            
            # Update task completion status
            task.completed = True
            task.completed_at = datetime.now()
            
            if completion_note:
                task.completion_note = completion_note
            
            # If completed_by is provided, we could store it in a separate field
            # For now, we'll include it in the note if provided
            if completed_by and completion_note:
                task.completion_note = f"[{completed_by}] {completion_note}"
            elif completed_by and not completion_note:
                task.completion_note = f"Completed by: {completed_by}"
            
            # Update last_completed for recurring tasks
            if task.frequency and task.frequency != 'Once':
                task.last_completed = date.today()
            
            # Commit changes
            self.db.commit()
            
            print(f"✅ Task '{task.description}' marked as completed")
            return True
            
        except Exception as e:
            print(f"Error marking task complete: {str(e)}")
            self.db.rollback()
            return False
    
    def mark_task_incomplete(self, task_id: int) -> bool:
        """
        Mark a task as incomplete (undo completion)
        
        Args:
            task_id: ID of the task to mark as incomplete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            
            if not task:
                print(f"Task with ID {task_id} not found")
                return False
            
            # Reset completion status
            task.completed = False
            task.completed_at = None
            task.completion_note = None
            
            self.db.commit()
            
            print(f"↩️ Task '{task.description}' marked as incomplete")
            return True
            
        except Exception as e:
            print(f"Error marking task incomplete: {str(e)}")
            self.db.rollback()
            return False
    
    def add_task_note(self, task_id: int, note: str, append: bool = False) -> bool:
        """
        Add or update a note for a task
        
        Args:
            task_id: ID of the task
            note: Note to add
            append: If True, append to existing note; if False, replace
            
        Returns:
            True if successful, False otherwise
        """
        try:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            
            if not task:
                print(f"Task with ID {task_id} not found")
                return False
            
            if append and task.completion_note:
                task.completion_note = f"{task.completion_note}\n{note}"
            else:
                task.completion_note = note
            
            self.db.commit()
            
            print(f"📝 Note added to task '{task.description}'")
            return True
            
        except Exception as e:
            print(f"Error adding note: {str(e)}")
            self.db.rollback()
            return False
    
    def get_task_summary(self, staff_id: int, target_date: Optional[date] = None) -> Dict:
        """
        Get a summary of tasks for a teacher
        
        Args:
            staff_id: ID of the staff member
            target_date: Date to check for tasks (defaults to today)
            
        Returns:
            Dictionary with task summary statistics
        """
        if target_date is None:
            target_date = date.today()
        
        all_tasks = self.get_tasks_for_today(staff_id, target_date)
        pending_tasks = [t for t in all_tasks if not t['completed']]
        completed_tasks = [t for t in all_tasks if t['completed']]
        
        # Group by category
        categories = {}
        for task in all_tasks:
            cat = task['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'completed': 0, 'pending': 0}
            categories[cat]['total'] += 1
            if task['completed']:
                categories[cat]['completed'] += 1
            else:
                categories[cat]['pending'] += 1
        
        # Calculate completion rate
        total_tasks = len(all_tasks)
        completed_count = len(completed_tasks)
        completion_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'date': target_date,
            'total_tasks': total_tasks,
            'completed_tasks': completed_count,
            'pending_tasks': len(pending_tasks),
            'completion_rate': round(completion_rate, 1),
            'categories': categories,
            'tasks': all_tasks
        }
    
    def display_teacher_dashboard(self, staff_id: int, target_date: Optional[date] = None) -> str:
        """
        Generate a formatted dashboard view for a teacher
        
        Args:
            staff_id: ID of the staff member
            target_date: Date to display (defaults to today)
            
        Returns:
            Formatted string with teacher dashboard
        """
        if target_date is None:
            target_date = date.today()
        
        # Get teacher info
        teacher = self.db.query(Staff).filter(Staff.id == staff_id).first()
        if not teacher:
            return "❌ Teacher not found"
        
        # Get task summary
        summary = self.get_task_summary(staff_id, target_date)
        
        # Build dashboard
        dashboard = f"""
👩‍🏫 Teacher Dashboard: {teacher.name}
📅 Date: {target_date.strftime('%A, %B %d, %Y')}
{'=' * 50}

📊 Task Summary:
• Total Tasks: {summary['total_tasks']}
• Completed: {summary['completed_tasks']} ✅
• Pending: {summary['pending_tasks']} ⏳
• Completion Rate: {summary['completion_rate']}%

📋 Tasks by Category:
"""
        
        for category, stats in summary['categories'].items():
            dashboard += f"• {category}: {stats['completed']}/{stats['total']} completed\n"
        
        dashboard += f"\n{'=' * 50}\n"
        
        # Show pending tasks
        pending_tasks = [t for t in summary['tasks'] if not t['completed']]
        if pending_tasks:
            dashboard += "⏳ PENDING TASKS:\n"
            for i, task in enumerate(pending_tasks, 1):
                dashboard += f"{i:2d}. [{task['category']}] {task['task_name']} - {task['student_name']}\n"
        
        # Show completed tasks
        completed_tasks = [t for t in summary['tasks'] if t['completed']]
        if completed_tasks:
            dashboard += f"\n✅ COMPLETED TASKS ({len(completed_tasks)}):\n"
            for task in completed_tasks:
                completed_time = ""
                if task['completed_at']:
                    completed_time = f" at {task['completed_at'].strftime('%H:%M')}"
                note_info = f" - {task['completion_note']}" if task['completion_note'] else ""
                dashboard += f"• [{task['category']}] {task['task_name']} - {task['student_name']}{completed_time}{note_info}\n"
        
        return dashboard

def interactive_teacher_session(teacher_name: Optional[str] = None):
    """
    Run an interactive console session for teachers to manage their tasks
    
    Args:
        teacher_name: Optional teacher name to start with
    """
    interface = TeacherTaskInterface()
    
    print("🎓 Educational Task Management - Teacher Interface")
    print("=" * 55)
    
    # Get teacher
    if teacher_name:
        teacher = interface.get_teacher_by_name(teacher_name)
        if not teacher:
            print(f"❌ Teacher '{teacher_name}' not found")
            return
    else:
        # Show available teachers
        teachers = interface.get_all_teachers()
        if not teachers:
            print("❌ No teachers found in the system")
            return
        
        print("\n👥 Available Teachers:")
        for i, t in enumerate(teachers, 1):
            print(f"{i:2d}. {t.name} ({t.expertise})")
        
        try:
            choice = int(input(f"\nSelect teacher (1-{len(teachers)}): "))
            if 1 <= choice <= len(teachers):
                teacher = teachers[choice - 1]
            else:
                print("❌ Invalid selection")
                return
        except ValueError:
            print("❌ Invalid input")
            return
    
    print(f"\n🔑 Logged in as: {teacher.name}")
    
    while True:
        # Display dashboard
        dashboard = interface.display_teacher_dashboard(teacher.id)
        print("\n" + dashboard)
        
        # Get pending tasks for interaction
        pending_tasks = interface.get_pending_tasks(teacher.id)
        
        if not pending_tasks:
            print("\n🎉 All tasks completed for today!")
            break
        
        print(f"\n📝 Task Actions:")
        print("Select a task number to complete, or:")
        print("• [R] Refresh dashboard")
        print("• [Q] Quit")
        
        user_input = input("\nYour choice: ").strip().upper()
        
        if user_input == 'Q':
            print("👋 Goodbye!")
            break
        elif user_input == 'R':
            continue
        
        try:
            task_num = int(user_input)
            if 1 <= task_num <= len(pending_tasks):
                selected_task = pending_tasks[task_num - 1]
                
                print(f"\n📋 Selected Task: {selected_task['task_name']}")
                print(f"👤 Student: {selected_task['student_name']}")
                print(f"📂 Category: {selected_task['category']}")
                
                # Task completion options
                print("\nActions:")
                print("• [C] Mark as completed")
                print("• [N] Add note only")
                print("• [B] Go back")
                
                action = input("Choose action: ").strip().upper()
                
                if action == 'C':
                    note = input("Optional completion note (press Enter to skip): ").strip()
                    note = note if note else None
                    
                    success = interface.mark_task_complete(
                        selected_task['task_id'], 
                        completion_note=note,
                        completed_by=teacher.name
                    )
                    
                    if success:
                        print("✅ Task marked as completed!")
                    else:
                        print("❌ Failed to complete task")
                
                elif action == 'N':
                    note = input("Enter note: ").strip()
                    if note:
                        success = interface.add_task_note(selected_task['task_id'], note)
                        if success:
                            print("📝 Note added!")
                        else:
                            print("❌ Failed to add note")
                    else:
                        print("❌ No note entered")
                
                elif action == 'B':
                    continue
                else:
                    print("❌ Invalid action")
            else:
                print("❌ Invalid task number")
        except ValueError:
            print("❌ Invalid input")
        
        input("\nPress Enter to continue...")

def get_tasks_for_today(staff_id: int, target_date: Optional[date] = None) -> List[Dict]:
    """
    Standalone function to get tasks for today
    
    Args:
        staff_id: ID of the staff member
        target_date: Date to check for tasks (defaults to today)
        
    Returns:
        List of task dictionaries
    """
    interface = TeacherTaskInterface()
    return interface.get_tasks_for_today(staff_id, target_date)

def mark_task_complete(task_id: int, note: Optional[str] = None) -> bool:
    """
    Standalone function to mark a task as complete
    
    Args:
        task_id: ID of the task to complete
        note: Optional completion note
        
    Returns:
        True if successful, False otherwise
    """
    interface = TeacherTaskInterface()
    return interface.mark_task_complete(task_id, completion_note=note)

def get_teacher_summary(staff_id: int, target_date: Optional[date] = None) -> Dict:
    """
    Standalone function to get teacher task summary
    
    Args:
        staff_id: ID of the staff member
        target_date: Date to check for tasks (defaults to today)
        
    Returns:
        Dictionary with task summary
    """
    interface = TeacherTaskInterface()
    return interface.get_task_summary(staff_id, target_date)

if __name__ == "__main__":
    """
    Run the interactive teacher interface when script is executed directly
    """
    import sys
    
    # Check for teacher name argument
    teacher_name = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        interactive_teacher_session(teacher_name)
    except KeyboardInterrupt:
        print("\n\n👋 Session ended by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")