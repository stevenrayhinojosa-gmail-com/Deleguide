from datetime import datetime, date
from sqlalchemy.orm import sessionmaker
from models import engine, Student, Staff, Task
import re
from typing import List, Dict, Tuple

class TaskRecommendationEngine:
    def __init__(self):
        self.Session = sessionmaker(bind=engine)
        
        # Comprehensive goal-to-task mapping dictionary
        self.goal_task_map = {
            "reading fluency": [
                "Collect reading fluency data",
                "Prepare adapted reading materials",
                "Track reading comprehension progress",
                "Administer reading assessments"
            ],
            "reading comprehension": [
                "Collect reading comprehension data",
                "Create reading comprehension worksheets",
                "Track reading progress",
                "Prepare reading intervention materials"
            ],
            "behavior": [
                "Track ABC data",
                "Run social skills group",
                "Monitor behavior intervention plan",
                "Document behavior incidents",
                "Implement behavior support strategies"
            ],
            "social skills": [
                "Run social skills group",
                "Track social interaction data",
                "Document peer interaction progress",
                "Facilitate group activities"
            ],
            "math": [
                "Modify math assignments",
                "Collect math progress data",
                "Prepare adapted math materials",
                "Track math skill development"
            ],
            "writing": [
                "Collect writing samples",
                "Track writing progress",
                "Modify writing assignments",
                "Prepare writing intervention materials"
            ],
            "communication": [
                "Track communication goals",
                "Document speech progress",
                "Prepare communication aids",
                "Monitor AAC device usage"
            ],
            "fine motor": [
                "Track fine motor progress",
                "Prepare fine motor activities",
                "Document handwriting improvement",
                "Monitor occupational therapy goals"
            ],
            "gross motor": [
                "Track gross motor development",
                "Document physical therapy progress",
                "Monitor mobility goals",
                "Prepare adaptive PE activities"
            ],
            "independent living": [
                "Track daily living skills",
                "Monitor self-care progress",
                "Document independence goals",
                "Prepare life skills activities"
            ]
        }
        
        # Service-to-task category mapping
        self.service_task_map = {
            "resource support": [
                "Log service minutes in XLogs",
                "Prepare adapted materials",
                "Track academic progress",
                "Modify assignments"
            ],
            "behavior support": [
                "Track behavior data",
                "Implement behavior plans",
                "Monitor behavioral goals",
                "Document incidents"
            ],
            "speech therapy": [
                "Track communication goals",
                "Document speech progress",
                "Prepare communication materials",
                "Monitor therapy goals"
            ],
            "occupational therapy": [
                "Track fine motor progress",
                "Document OT goals",
                "Prepare adaptive materials",
                "Monitor therapy progress"
            ],
            "physical therapy": [
                "Track gross motor goals",
                "Document PT progress",
                "Monitor mobility goals",
                "Prepare adaptive activities"
            ],
            "counseling": [
                "Track emotional goals",
                "Document counseling progress",
                "Monitor social-emotional development",
                "Implement coping strategies"
            ]
        }
        
        # Task categories with associated roles/staff expertise
        self.task_categories = {
            "Math": ["Math", "Resource Support", "Special Education"],
            "ELA": ["ELA", "Reading", "Special Education"],
            "Social Skills": ["Behavior Support", "Counseling", "Social Skills"],
            "Science": ["Science", "Resource Support"],
            "Fine Motor Skills": ["Occupational Therapy", "Fine Motor Skills"],
            "Behavioral Support": ["Behavior Support", "Counseling"],
            "Communication": ["Speech Therapy", "Communication"],
            "Life Skills": ["Independent Living", "Life Skills"]
        }
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text for matching"""
        if not text:
            return []
        
        text = text.lower()
        keywords = []
        
        # Check for each goal pattern in the text
        for goal_key in self.goal_task_map.keys():
            if goal_key in text:
                keywords.append(goal_key)
        
        # Check for service patterns
        for service_key in self.service_task_map.keys():
            if service_key in text:
                keywords.append(service_key)
        
        return keywords
    
    def get_existing_tasks(self, student_id: int) -> List[str]:
        """Get list of already assigned task descriptions for a student"""
        session = self.Session()
        try:
            existing_tasks = session.query(Task).filter(
                Task.student_id == student_id,
                Task.completed == False
            ).all()
            return [task.description for task in existing_tasks]
        finally:
            session.close()
    
    def suggest_tasks_for_student(self, student_id: int) -> Dict:
        """Main function to suggest tasks for a specific student"""
        session = self.Session()
        
        try:
            # Get student information
            student = session.query(Student).filter(Student.id == student_id).first()
            if not student:
                return {"error": "Student not found"}
            
            # Get existing tasks to avoid duplicates (unless recurring)
            existing_tasks = self.get_existing_tasks(student_id)
            
            # Extract keywords from goals and needs
            goal_keywords = self.extract_keywords(student.goals)
            need_keywords = self.extract_keywords(student.needs)
            
            all_keywords = list(set(goal_keywords + need_keywords))
            
            recommendations = []
            
            # Generate task recommendations based on goals
            for keyword in goal_keywords:
                if keyword in self.goal_task_map:
                    for task_name in self.goal_task_map[keyword]:
                        if task_name not in existing_tasks:  # Avoid duplicates
                            recommendations.append({
                                "task_name": task_name,
                                "reason": f"matched to goal: {keyword}",
                                "category": self._determine_category(task_name),
                                "frequency": self._suggest_frequency(task_name, keyword),
                                "priority": "high" if "data" in task_name.lower() else "medium"
                            })
            
            # Generate task recommendations based on needs/services
            for keyword in need_keywords:
                if keyword in self.service_task_map:
                    for task_name in self.service_task_map[keyword]:
                        if task_name not in existing_tasks:
                            # Check if already recommended
                            if not any(rec["task_name"] == task_name for rec in recommendations):
                                recommendations.append({
                                    "task_name": task_name,
                                    "reason": f"matched to service/need: {keyword}",
                                    "category": self._determine_category(task_name),
                                    "frequency": self._suggest_frequency(task_name, keyword),
                                    "priority": "medium"
                                })
            
            # Add ARD-related tasks if ARD date is approaching
            if student.ard_date:
                days_until_ard = (student.ard_date - date.today()).days
                if 0 <= days_until_ard <= 30:  # ARD within 30 days
                    ard_tasks = [
                        "Prepare ARD paperwork",
                        "Collect progress data for ARD",
                        "Review and update IEP goals",
                        "Schedule ARD meeting"
                    ]
                    for task_name in ard_tasks:
                        if task_name not in existing_tasks:
                            recommendations.append({
                                "task_name": task_name,
                                "reason": f"ARD approaching in {days_until_ard} days",
                                "category": "Administrative",
                                "frequency": "Once",
                                "priority": "high"
                            })
            
            # Remove duplicates and sort by priority
            unique_recommendations = []
            seen_tasks = set()
            
            for rec in recommendations:
                if rec["task_name"] not in seen_tasks:
                    unique_recommendations.append(rec)
                    seen_tasks.add(rec["task_name"])
            
            # Sort by priority (high first, then medium)
            unique_recommendations.sort(key=lambda x: (x["priority"] != "high", x["task_name"]))
            
            return {
                "student_name": student.name,
                "student_id": student_id,
                "recommendations": unique_recommendations,
                "total_suggestions": len(unique_recommendations),
                "ard_date": student.ard_date,
                "keywords_found": all_keywords
            }
            
        finally:
            session.close()
    
    def _determine_category(self, task_name: str) -> str:
        """Determine appropriate category for a task"""
        task_lower = task_name.lower()
        
        if any(word in task_lower for word in ["math", "calculation", "number"]):
            return "Math"
        elif any(word in task_lower for word in ["reading", "writing", "ela", "comprehension"]):
            return "ELA"
        elif any(word in task_lower for word in ["behavior", "social", "interaction"]):
            return "Social Skills"
        elif any(word in task_lower for word in ["motor", "physical", "movement"]):
            return "Fine Motor Skills"
        elif any(word in task_lower for word in ["communication", "speech", "aac"]):
            return "Communication"
        elif any(word in task_lower for word in ["ard", "iep", "paperwork", "meeting"]):
            return "Administrative"
        else:
            return "General"
    
    def _suggest_frequency(self, task_name: str, keyword: str) -> str:
        """Suggest appropriate frequency for a task"""
        task_lower = task_name.lower()
        
        if "data" in task_lower or "track" in task_lower:
            return "Daily"
        elif "prepare" in task_lower or "create" in task_lower:
            return "Once"
        elif "ard" in task_lower or "meeting" in task_lower:
            return "Once"
        elif "group" in task_lower:
            return "Daily"
        else:
            return "Once a Month"
    
    def get_staff_recommendations(self, task_category: str) -> List[str]:
        """Recommend appropriate staff members for a task category"""
        session = self.Session()
        
        try:
            if task_category in self.task_categories:
                required_expertise = self.task_categories[task_category]
                
                suitable_staff = []
                all_staff = session.query(Staff).all()
                
                for staff_member in all_staff:
                    staff_expertise = [exp.strip() for exp in staff_member.expertise.split(',')]
                    
                    # Check if staff has any of the required expertise
                    if any(req_exp in staff_expertise for req_exp in required_expertise):
                        suitable_staff.append(staff_member.name)
                
                return suitable_staff
            
            return []
            
        finally:
            session.close()
    
    def generate_recommendation_report(self, student_id: int) -> str:
        """Generate a formatted recommendation report"""
        recommendations = self.suggest_tasks_for_student(student_id)
        
        if "error" in recommendations:
            return f"❌ {recommendations['error']}"
        
        report = []
        report.append(f"🎯 Suggested Tasks for Student: {recommendations['student_name']}")
        report.append("=" * 60)
        
        if recommendations['ard_date']:
            days_until = (recommendations['ard_date'] - date.today()).days
            if days_until >= 0:
                report.append(f"📅 ARD Date: {recommendations['ard_date']} ({days_until} days)")
            else:
                report.append(f"📅 ARD Date: {recommendations['ard_date']} (Past due)")
        
        report.append(f"🔍 Keywords Found: {', '.join(recommendations['keywords_found'])}")
        report.append(f"📊 Total Suggestions: {recommendations['total_suggestions']}")
        report.append("")
        
        if recommendations['recommendations']:
            for i, rec in enumerate(recommendations['recommendations'], 1):
                priority_icon = "🔥" if rec['priority'] == 'high' else "📌"
                report.append(f"{priority_icon} {i}. {rec['task_name']}")
                report.append(f"   Reason: {rec['reason']}")
                report.append(f"   Category: {rec['category']} | Frequency: {rec['frequency']}")
                
                # Add staff recommendations
                staff_recs = self.get_staff_recommendations(rec['category'])
                if staff_recs:
                    report.append(f"   Suggested Staff: {', '.join(staff_recs[:3])}")  # Show top 3
                
                report.append("")
        else:
            report.append("✅ No new task recommendations at this time.")
        
        return "\n".join(report)

def suggest_tasks_for_student(student_id: int):
    """Standalone function for task recommendations"""
    engine = TaskRecommendationEngine()
    return engine.suggest_tasks_for_student(student_id)

def generate_recommendation_report(student_id: int):
    """Standalone function for recommendation report"""
    engine = TaskRecommendationEngine()
    return engine.generate_recommendation_report(student_id)

def recommend_tasks_for_all_students():
    """Generate recommendations for all students"""
    from models import SessionLocal
    
    session = SessionLocal()
    try:
        students = session.query(Student).all()
        engine = TaskRecommendationEngine()
        
        all_recommendations = {}
        
        for student in students:
            recommendations = engine.suggest_tasks_for_student(student.id)
            all_recommendations[student.name] = recommendations
        
        return all_recommendations
        
    finally:
        session.close()

if __name__ == "__main__":
    # CLI interface for testing
    print("🎯 Task Recommendation Engine")
    print("=" * 40)
    
    from models import SessionLocal
    session = SessionLocal()
    
    try:
        students = session.query(Student).all()
        
        if not students:
            print("❌ No students found in database.")
        else:
            print("\n📋 Available Students:")
            for i, student in enumerate(students, 1):
                print(f"{i}. {student.name} (ID: {student.id})")
            
            try:
                choice = input("\nEnter student number to get recommendations (or 'all' for all students): ").strip()
                
                if choice.lower() == 'all':
                    print("\n" + "="*60)
                    print("📊 RECOMMENDATIONS FOR ALL STUDENTS")
                    print("="*60)
                    
                    engine = TaskRecommendationEngine()
                    for student in students:
                        print(f"\n{engine.generate_recommendation_report(student.id)}")
                        print("-" * 60)
                
                else:
                    student_num = int(choice)
                    if 1 <= student_num <= len(students):
                        selected_student = students[student_num - 1]
                        
                        engine = TaskRecommendationEngine()
                        report = engine.generate_recommendation_report(selected_student.id)
                        print(f"\n{report}")
                    else:
                        print("❌ Invalid student number.")
                        
            except (ValueError, KeyboardInterrupt):
                print("\n👋 Goodbye!")
    
    finally:
        session.close()