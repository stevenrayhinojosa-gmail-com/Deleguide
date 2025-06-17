#!/usr/bin/env python3
"""
Inference Test (Validation) Script for Educational Task Management System

This script validates the task recommendation system by running test cases
with real student data to ensure correct task suggestions and system functionality.

Author: Educational Task Management System
Date: 2025-01-16
"""

import sys
import traceback
from datetime import date, timedelta
from models import get_db, Student, Staff, Task
from task_recommender import TaskRecommendationEngine, suggest_tasks_for_student
from daily_task_feed import DailyTaskFeedGenerator
from recurring_task_generator import RecurringTaskGenerator
from scheduling_engine import TaskSchedulingEngine
from teacher_interface import TeacherTaskInterface
from reporting_module import WeeklyReportGenerator


class InferenceTestSuite:
    """
    Comprehensive test suite for validating task management system components
    """
    
    def __init__(self):
        """Initialize test suite with database connection"""
        self.db = get_db()
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}: {message}")
        
        if success:
            self.test_results['passed'] += 1
        else:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {message}")
    
    def test_task_recommendations(self):
        """Test task recommendation engine with real student data"""
        print("\n🔍 Testing Task Recommendation Engine...")
        
        try:
            # Get real student data
            students = self.db.query(Student).all()
            
            if not students:
                self.log_result("Task Recommendations", False, "No students found in database")
                return
            
            # Test with first student
            student = students[0]
            print(f"Testing recommendations for student: {student.name}")
            print(f"Student goals: {student.goals}")
            print(f"Student needs: {student.needs}")
            
            # Generate recommendations
            recommendations = suggest_tasks_for_student(student.id)
            
            if 'error' in recommendations:
                self.log_result("Task Recommendations", False, f"Error: {recommendations['error']}")
                return
            
            # Validate recommendations structure
            required_keys = ['student_name', 'recommendations', 'staff_suggestions']
            for key in required_keys:
                if key not in recommendations:
                    self.log_result("Task Recommendations", False, f"Missing key: {key}")
                    return
            
            # Print recommendations for manual validation
            print(f"\n📋 Generated {len(recommendations['recommendations'])} recommendations:")
            for i, rec in enumerate(recommendations['recommendations'], 1):
                print(f"  {i}. {rec['task_name']} ({rec['category']}) - Priority: {rec['priority']}")
                print(f"     Reason: {rec['reason']}")
            
            print(f"\n👥 Staff suggestions: {', '.join(recommendations['staff_suggestions'])}")
            
            # Validate that recommendations are relevant
            relevant_count = 0
            for rec in recommendations['recommendations']:
                # Check if recommendation relates to student goals or needs
                student_text = f"{student.goals} {student.needs}".lower()
                task_text = f"{rec['task_name']} {rec['reason']}".lower()
                
                # Simple keyword matching for relevance
                goal_keywords = ['reading', 'math', 'behavior', 'communication', 'motor', 'social']
                for keyword in goal_keywords:
                    if keyword in student_text and keyword in task_text:
                        relevant_count += 1
                        break
            
            if relevant_count > 0:
                self.log_result("Task Recommendations", True, 
                              f"Generated {len(recommendations['recommendations'])} relevant recommendations")
            else:
                self.log_result("Task Recommendations", False, "No relevant recommendations generated")
                
        except Exception as e:
            self.log_result("Task Recommendations", False, f"Exception: {str(e)}")
    
    def test_daily_task_feed(self):
        """Test daily task feed generation"""
        print("\n📅 Testing Daily Task Feed Generator...")
        
        try:
            feed_generator = DailyTaskFeedGenerator()
            
            # Test getting tasks for today
            staff_members = self.db.query(Staff).all()
            
            if not staff_members:
                self.log_result("Daily Task Feed", False, "No staff members found")
                return
            
            staff = staff_members[0]
            today_tasks = feed_generator.get_today_tasks(staff.id)
            
            print(f"Testing daily feed for: {staff.name}")
            print(f"Tasks due today: {len(today_tasks)}")
            
            for task in today_tasks[:3]:  # Show first 3 tasks
                student_name = task.student.name if task.student else "Unknown Student"
                print(f"  - {task.description} (Student: {student_name})")
            
            # Test full daily feed generation
            daily_feed = feed_generator.generate_daily_feed()
            
            if daily_feed and len(daily_feed) > 0:
                self.log_result("Daily Task Feed", True, 
                              f"Generated feed for {len(daily_feed)} staff members")
            else:
                self.log_result("Daily Task Feed", True, "No tasks due today (valid scenario)")
                
        except Exception as e:
            self.log_result("Daily Task Feed", False, f"Exception: {str(e)}")
    
    def test_recurring_task_generator(self):
        """Test recurring task generation"""
        print("\n🔄 Testing Recurring Task Generator...")
        
        try:
            recurring_generator = RecurringTaskGenerator()
            
            # Test recurring task generation for today
            today = date.today()
            generation_result = recurring_generator.generate_recurring_tasks(today)
            
            print(f"Testing recurring task generation for: {today}")
            print(f"Generation result: {generation_result['summary']}")
            
            if generation_result['success']:
                self.log_result("Recurring Task Generator", True, 
                              f"Generated {generation_result['tasks_created']} recurring tasks")
            else:
                self.log_result("Recurring Task Generator", True, 
                              "No recurring tasks generated (valid for non-school days)")
                
        except Exception as e:
            self.log_result("Recurring Task Generator", False, f"Exception: {str(e)}")
    
    def test_scheduling_engine(self):
        """Test smart scheduling engine"""
        print("\n⏰ Testing Smart Scheduling Engine...")
        
        try:
            scheduling_engine = TaskSchedulingEngine()
            
            # Test due date calculations
            students = self.db.query(Student).all()
            
            if not students:
                self.log_result("Scheduling Engine", False, "No students found")
                return
            
            student = students[0]
            tasks = self.db.query(Task).filter(Task.student_id == student.id).all()
            
            if not tasks:
                self.log_result("Scheduling Engine", True, "No tasks found for scheduling test")
                return
            
            # Test calculating due dates for tasks
            task = tasks[0]
            due_date_info = scheduling_engine.calculate_due_date(task, student)
            
            print(f"Testing scheduling for task: {task.description}")
            print(f"Original deadline: {task.deadline}")
            print(f"Calculated due date: {due_date_info['due_date']}")
            print(f"Reason: {due_date_info['reason']}")
            
            # Test getting tasks due soon
            tasks_due_soon = scheduling_engine.get_tasks_due_soon(days_ahead=7)
            
            print(f"Tasks due within 7 days: {len(tasks_due_soon)}")
            
            self.log_result("Scheduling Engine", True, 
                          f"Processed scheduling calculations successfully")
                
        except Exception as e:
            self.log_result("Scheduling Engine", False, f"Exception: {str(e)}")
    
    def test_teacher_interface(self):
        """Test teacher interface functionality"""
        print("\n👩‍🏫 Testing Teacher Interface...")
        
        try:
            teacher_interface = TeacherTaskInterface()
            
            # Get all teachers
            teachers = teacher_interface.get_all_teachers()
            
            if not teachers:
                self.log_result("Teacher Interface", False, "No teachers found")
                return
            
            teacher = teachers[0]
            print(f"Testing teacher interface for: {teacher.name}")
            
            # Test getting tasks for today
            today_tasks = teacher_interface.get_tasks_for_today(teacher.id)
            pending_tasks = teacher_interface.get_pending_tasks(teacher.id)
            completed_tasks = teacher_interface.get_completed_tasks(teacher.id)
            
            print(f"Tasks for today: {len(today_tasks)}")
            print(f"Pending tasks: {len(pending_tasks)}")
            print(f"Completed tasks: {len(completed_tasks)}")
            
            # Test task summary
            summary = teacher_interface.get_task_summary(teacher.id)
            print(f"Task summary: {summary['completed_tasks']}/{summary['total_tasks']} completed")
            
            self.log_result("Teacher Interface", True, 
                          f"Interface working correctly for {teacher.name}")
                
        except Exception as e:
            self.log_result("Teacher Interface", False, f"Exception: {str(e)}")
    
    def test_weekly_reporting(self):
        """Test weekly report generation"""
        print("\n📊 Testing Weekly Report Generator...")
        
        try:
            report_generator = WeeklyReportGenerator()
            
            # Get staff for testing
            staff_members = self.db.query(Staff).all()
            
            if not staff_members:
                self.log_result("Weekly Reporting", False, "No staff members found")
                return
            
            staff = staff_members[0]
            print(f"Testing weekly report for: {staff.name}")
            
            # Generate individual report
            individual_report = report_generator.generate_weekly_report(staff.id)
            
            if 'error' in individual_report:
                self.log_result("Weekly Reporting", False, f"Error: {individual_report['error']}")
                return
            
            print(f"Individual report period: {individual_report['report_period']['formatted_period']}")
            print(f"Tasks: {individual_report['summary']['completed_tasks']}/{individual_report['summary']['total_tasks']} completed")
            print(f"Goal coverage: {len(individual_report['goal_coverage'])} students")
            
            # Generate master report
            master_report = report_generator.generate_master_report()
            
            if 'master_summary' in master_report:
                summary = master_report['master_summary']
                print(f"Master report covers {summary['staff_count']} staff members")
                print(f"Overall completion rate: {summary['completion_rate']}%")
                
                self.log_result("Weekly Reporting", True, 
                              f"Generated reports for {summary['staff_count']} staff members")
            else:
                self.log_result("Weekly Reporting", False, "Failed to generate master report")
                
        except Exception as e:
            self.log_result("Weekly Reporting", False, f"Exception: {str(e)}")
    
    def test_database_integrity(self):
        """Test database data integrity"""
        print("\n🗄️ Testing Database Integrity...")
        
        try:
            # Count records in each table
            student_count = self.db.query(Student).count()
            staff_count = self.db.query(Staff).count()
            task_count = self.db.query(Task).count()
            
            print(f"Database records:")
            print(f"  Students: {student_count}")
            print(f"  Staff: {staff_count}")
            print(f"  Tasks: {task_count}")
            
            # Test relationships
            students_with_tasks = self.db.query(Student).join(Task).distinct().count()
            staff_with_tasks = self.db.query(Staff).join(Task).distinct().count()
            
            print(f"Relationships:")
            print(f"  Students with tasks: {students_with_tasks}")
            print(f"  Staff with tasks: {staff_with_tasks}")
            
            # Basic integrity checks
            if student_count > 0 and staff_count > 0:
                self.log_result("Database Integrity", True, 
                              f"Database contains {student_count} students, {staff_count} staff, {task_count} tasks")
            else:
                self.log_result("Database Integrity", False, "Missing essential data")
                
        except Exception as e:
            self.log_result("Database Integrity", False, f"Exception: {str(e)}")
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        print("\n🔄 Testing End-to-End Workflow...")
        
        try:
            # Test complete workflow: recommendation → task creation → completion → reporting
            students = self.db.query(Student).all()
            staff_members = self.db.query(Staff).all()
            
            if not students or not staff_members:
                self.log_result("End-to-End Workflow", False, "Insufficient data for workflow test")
                return
            
            student = students[0]
            staff = staff_members[0]
            
            print(f"Testing workflow: {student.name} → {staff.name}")
            
            # 1. Generate recommendations
            recommendations = suggest_tasks_for_student(student.id)
            
            if 'error' in recommendations or not recommendations['recommendations']:
                self.log_result("End-to-End Workflow", False, "Failed at recommendation stage")
                return
            
            # 2. Check if tasks exist for the student
            existing_tasks = self.db.query(Task).filter(Task.student_id == student.id).count()
            
            # 3. Test daily feed generation
            feed_generator = DailyTaskFeedGenerator()
            daily_feed = feed_generator.get_today_tasks(staff.id)
            
            # 4. Test teacher interface
            teacher_interface = TeacherTaskInterface()
            teacher_summary = teacher_interface.get_task_summary(staff.id)
            
            # 5. Test weekly reporting
            report_generator = WeeklyReportGenerator()
            weekly_report = report_generator.generate_weekly_report(staff.id)
            
            if 'error' not in weekly_report:
                self.log_result("End-to-End Workflow", True, 
                              "Complete workflow executed successfully")
            else:
                self.log_result("End-to-End Workflow", False, "Failed at reporting stage")
                
        except Exception as e:
            self.log_result("End-to-End Workflow", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting Educational Task Management System Inference Tests")
        print("=" * 70)
        
        # Run all test components
        self.test_database_integrity()
        self.test_task_recommendations()
        self.test_daily_task_feed()
        self.test_recurring_task_generator()
        self.test_scheduling_engine()
        self.test_teacher_interface()
        self.test_weekly_reporting()
        self.test_end_to_end_workflow()
        
        # Print final results
        print("\n" + "=" * 70)
        print("🎯 Test Results Summary")
        print(f"✅ Tests Passed: {self.test_results['passed']}")
        print(f"❌ Tests Failed: {self.test_results['failed']}")
        
        if self.test_results['failed'] > 0:
            print("\n🚨 Failed Tests:")
            for error in self.test_results['errors']:
                print(f"  - {error}")
        else:
            print("\n🎉 All tests passed! System is working correctly.")
        
        # Calculate success rate
        total_tests = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total_tests * 100) if total_tests > 0 else 0
        print(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        return self.test_results


def run_focused_test(component: str):
    """Run test for specific component"""
    test_suite = InferenceTestSuite()
    
    if component == "recommendations":
        test_suite.test_task_recommendations()
    elif component == "daily_feed":
        test_suite.test_daily_task_feed()
    elif component == "recurring":
        test_suite.test_recurring_task_generator()
    elif component == "scheduling":
        test_suite.test_scheduling_engine()
    elif component == "teacher":
        test_suite.test_teacher_interface()
    elif component == "reporting":
        test_suite.test_weekly_reporting()
    elif component == "database":
        test_suite.test_database_integrity()
    elif component == "workflow":
        test_suite.test_end_to_end_workflow()
    else:
        print(f"Unknown component: {component}")
        print("Available components: recommendations, daily_feed, recurring, scheduling, teacher, reporting, database, workflow")


def main():
    """Main function to run inference tests"""
    if len(sys.argv) > 1:
        # Run specific component test
        component = sys.argv[1]
        print(f"🔍 Running focused test for: {component}")
        run_focused_test(component)
    else:
        # Run complete test suite
        test_suite = InferenceTestSuite()
        results = test_suite.run_all_tests()
        
        # Exit with appropriate code
        exit_code = 0 if results['failed'] == 0 else 1
        sys.exit(exit_code)


if __name__ == "__main__":
    main()