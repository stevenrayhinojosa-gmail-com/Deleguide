import unittest
from models import Student, Staff, Task
from datetime import datetime, timedelta

class TestModels(unittest.TestCase):
    def test_student_creation(self):
        student = Student(
            name="Test Student",
            goals="Math,Science",
            needs="Reading Comprehension"
        )
        self.assertEqual(student.name, "Test Student")
        self.assertEqual(student.goals, "Math,Science")
        self.assertEqual(student.needs, "Reading Comprehension")

    def test_staff_creation(self):
        staff = Staff(
            name="Test Staff",
            expertise="Math,Science"
        )
        self.assertEqual(staff.name, "Test Staff")
        self.assertEqual(staff.expertise, "Math,Science")

    def test_task_creation(self):
        task = Task(
            description="Test Task",
            category="Math",
            deadline=datetime.now().date(),
            completed=False
        )
        self.assertEqual(task.description, "Test Task")
        self.assertEqual(task.category, "Math")
        self.assertEqual(task.completed, False)

if __name__ == '__main__':
    unittest.main()
