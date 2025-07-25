import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from models import Student, Staff, Task, get_db
from sqlalchemy import func
from sqlalchemy import Integer
from daily_task_feed import DailyTaskFeedGenerator
from task_recommender import TaskRecommendationEngine
from scheduling_engine import TaskSchedulingEngine
from recurring_task_generator import RecurringTaskGenerator
from teacher_interface import TeacherTaskInterface
from reporting_module import WeeklyReportGenerator

# Page configuration
st.set_page_config(
    page_title="Educational Task Management System",
    page_icon="📚",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Database session
db = get_db()

# Sidebar configuration
with st.sidebar:
    st.title('📚 Navigation')
    st.markdown('---')
    page = st.selectbox(
        'Choose a section',
        ['Dashboard', 'Daily Task Feed', 'Teacher Interface', 'Task Recommendations', 'Smart Scheduling', 'Recurring Tasks', 'Student Management', 'Staff Management', 'Task Management', 'Progress Tracking', 'Reports'],
        index=0
    )
    st.markdown('---')
    st.markdown('### Quick Stats')
    col1, col2 = st.columns(2)
    with col1:
        student_count = db.query(func.count(Student.id)).scalar()
        st.metric('Students', student_count)
    with col2:
        staff_count = db.query(func.count(Staff.id)).scalar()
        st.metric('Staff', staff_count)

    st.markdown('---')
    st.caption('Educational Task Management System v1.0')

def add_student():
    st.header('📝 Student Management')
    st.subheader('Add New Student')

    with st.form('student_form'):
        name = st.text_input('Student Name')
        col1, col2 = st.columns(2)
        with col1:
            goals = st.multiselect(
                'Educational Goals',
                ['Math', 'ELA', 'Social Skills', 'Science', 'Fine Motor Skills']
            )
        with col2:
            needs = st.multiselect(
                'Specific Needs',
                ['Reading Comprehension', 'Math Support', 'Behavioral Support', 'Fine Motor Skills']
            )
        
        ard_date = st.date_input('ARD Date (Optional)', value=None)

        submitted = st.form_submit_button('Add Student')
        if submitted:
            if name and goals and needs:
                new_student = Student(
                    name=name,
                    goals=','.join(goals),
                    needs=','.join(needs),
                    ard_date=ard_date
                )
                db.add(new_student)
                db.commit()
                st.success(f'✅ Student {name} added successfully!')
            else:
                st.error('❌ Please fill in all fields')

def add_staff():
    st.header('👥 Staff Management')
    st.subheader('Add New Staff Member')

    with st.form('staff_form'):
        name = st.text_input('Staff Name')
        expertise = st.multiselect(
            'Areas of Expertise',
            ['Math', 'ELA', 'Social Skills', 'Science', 'Fine Motor Skills',
             'Reading Comprehension', 'Behavioral Support']
        )

        submitted = st.form_submit_button('Add Staff Member')
        if submitted:
            if name and expertise:
                new_staff = Staff(
                    name=name,
                    expertise=','.join(expertise)
                )
                db.add(new_staff)
                db.commit()
                st.success(f'✅ Staff member {name} added successfully!')
            else:
                st.error('❌ Please fill in all fields')

def create_task():
    st.header('✔️ Task Management')
    st.subheader('Create New Task')

    staff_count = db.query(func.count(Staff.id)).scalar()
    student_count = db.query(func.count(Student.id)).scalar()

    if staff_count == 0 or student_count == 0:
        st.warning('⚠️ Please add both students and staff members before creating tasks.')
        return

    with st.form('task_form'):
        description = st.text_input('Task Description')
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox(
                'Task Category',
                ['Math', 'ELA', 'Social Skills', 'Science', 'Fine Motor Skills']
            )
            staff_list = db.query(Staff).all()
            staff = st.selectbox('Assign Staff', [s.name for s in staff_list])
        with col2:
            student_list = db.query(Student).all()
            student = st.selectbox('Select Student', [s.name for s in student_list])
            deadline = st.date_input(
                'Deadline',
                min_value=datetime.now().date(),
                max_value=datetime.now().date() + timedelta(days=365)
            )
        
        frequency = st.selectbox(
            'Task Frequency',
            ['Once', 'Daily', 'Once a Month', 'Every 9 Weeks', 'Once a Year']
        )

        submitted = st.form_submit_button('Create Task')
        if submitted:
            if description and category and staff and student and deadline:
                staff_obj = db.query(Staff).filter(Staff.name == staff).first()
                student_obj = db.query(Student).filter(Student.name == student).first()

                new_task = Task(
                    description=description,
                    category=category,
                    staff_id=staff_obj.id,
                    student_id=student_obj.id,
                    deadline=deadline,
                    frequency=frequency,
                    completed=False
                )
                db.add(new_task)
                db.commit()
                st.success('✅ Task created successfully!')
            else:
                st.error('❌ Please fill in all fields')

def track_progress():
    st.header('📊 Progress Tracking')

    tasks = db.query(Task).all()
    if not tasks:
        st.info('ℹ️ No tasks available to track')
        return

    for task in tasks:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📌 Task: {task.description}")
                st.caption(f"👤 Assigned to: {task.staff_member.name} | 👨‍🎓 Student: {task.student.name}")
            with col2:
                st.write(f"📅 Due: {task.deadline}")
            with col3:
                if st.checkbox('✓ Complete', value=task.completed, key=f'task_{task.id}'):
                    task.completed = True
                    db.commit()
                else:
                    task.completed = False
                    db.commit()

def generate_reports():
    st.header('📈 Reports Dashboard')
    
    # Create tabs for different report types
    tab1, tab2, tab3 = st.tabs(['📊 Overview Statistics', '📅 Weekly SPED Reports', '📋 Export Options'])
    
    with tab1:
        tasks = db.query(Task).all()
        if not tasks:
            st.info('ℹ️ No task data available for reporting')
            return

        # Task completion statistics
        staff_stats = db.query(
            Staff.name,
            func.count(Task.id).label('total_tasks'),
            func.sum(Task.completed.cast(Integer)).label('completed_tasks')
        ).join(Task).group_by(Staff.name).all()

        completion_stats = pd.DataFrame(
            [(s.name, s.total_tasks, s.completed_tasks) for s in staff_stats],
            columns=['Staff', 'Total Tasks', 'Completed Tasks']
        )
        completion_stats['Completion Rate'] = (completion_stats['Completed Tasks'] / completion_stats['Total Tasks'] * 100).round(2)

        # Display statistics
        st.subheader('📊 Staff Performance Summary')
        st.dataframe(completion_stats, use_container_width=True)

        # Create visualization
        fig = px.bar(
            completion_stats,
            x='Staff',
            y=['Total Tasks', 'Completed Tasks'],
            title='Task Completion by Staff Member',
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Student progress
        student_stats = db.query(
            Student.name,
            func.count(Task.id).label('total_tasks'),
            func.sum(Task.completed.cast(Integer)).label('completed_tasks')
        ).join(Task).group_by(Student.name).all()

        student_progress = pd.DataFrame(
            [(s.name, s.total_tasks, s.completed_tasks) for s in student_stats],
            columns=['Student', 'Total Tasks', 'Completed Tasks']
        )
        student_progress['Completion Rate'] = (student_progress['Completed Tasks'] / student_progress['Total Tasks'] * 100).round(2)
        st.subheader('👨‍🎓 Student Task Progress')
        st.dataframe(student_progress, use_container_width=True)
    
    with tab2:
        st.subheader('📅 Weekly SPED Task Reports')
        st.markdown('Generate comprehensive weekly reports for SPED staff with task completion summaries, missed tasks, and IEP goal coverage analysis.')
        
        # Initialize report generator
        report_generator = WeeklyReportGenerator()
        
        # Get all staff for dropdown
        all_staff = db.query(Staff).all()
        
        if not all_staff:
            st.warning('⚠️ No staff members found. Please add staff members first.')
            return
        
        # Report configuration
        col1, col2 = st.columns(2)
        
        with col1:
            report_type = st.selectbox(
                'Report Type',
                ['Individual Staff Report', 'Master Report (All Staff)'],
                help='Choose between individual staff report or master report for all staff'
            )
            
            if report_type == 'Individual Staff Report':
                selected_staff = st.selectbox(
                    'Select Staff Member',
                    options=all_staff,
                    format_func=lambda x: x.name,
                    help='Choose the staff member for the report'
                )
        
        with col2:
            weeks_back = st.selectbox(
                'Report Period',
                options=[0, 1, 2, 3, 4],
                format_func=lambda x: 'Current Week' if x == 0 else f'{x} Week(s) Ago',
                help='Select which week to generate the report for'
            )
        
        # Generate report button
        if st.button('🔄 Generate Report', type='primary'):
            with st.spinner('Generating weekly report...'):
                try:
                    # Get date range
                    start_date, end_date = report_generator.get_date_range(weeks_back)
                    
                    if report_type == 'Individual Staff Report':
                        # Generate individual report
                        report_data = report_generator.generate_weekly_report(
                            selected_staff.id, start_date, end_date
                        )
                        
                        if 'error' in report_data:
                            st.error(f'❌ Error generating report: {report_data["error"]}')
                        else:
                            # Display report
                            st.success('✅ Report generated successfully!')
                            
                            # Report header
                            st.markdown(f"## Weekly Report for {report_data['staff_name']}")
                            st.markdown(f"**Period:** {report_data['report_period']['formatted_period']}")
                            
                            # Summary metrics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric('Total Tasks', report_data['summary']['total_tasks'])
                            with col2:
                                st.metric('Completed', report_data['summary']['completed_tasks'])
                            with col3:
                                st.metric('Missed', report_data['summary']['missed_tasks'])
                            with col4:
                                st.metric('Completion Rate', f"{report_data['summary']['completion_rate']}%")
                            
                            # Completed tasks section
                            if report_data['completed_tasks']:
                                st.subheader('✅ Completed Tasks')
                                completed_df = pd.DataFrame([
                                    {
                                        'Student': task['student_name'],
                                        'Task': task['task_name'],
                                        'Category': task['category'],
                                        'Completed': task['completed_at'].strftime('%m/%d/%Y') if task['completed_at'] else 'Unknown',
                                        'Notes': task['completion_note'] or 'No notes'
                                    }
                                    for task in report_data['completed_tasks']
                                ])
                                st.dataframe(completed_df, use_container_width=True)
                            else:
                                st.info('ℹ️ No completed tasks for this period')
                            
                            # Missed tasks section
                            if report_data['missed_tasks']:
                                st.subheader('❌ Missed Tasks')
                                missed_df = pd.DataFrame([
                                    {
                                        'Student': task['student_name'],
                                        'Task': task['task_name'],
                                        'Category': task['category'],
                                        'Due Date': task['deadline'].strftime('%m/%d/%Y')
                                    }
                                    for task in report_data['missed_tasks']
                                ])
                                st.dataframe(missed_df, use_container_width=True)
                            else:
                                st.success('🎉 No missed tasks!')
                            
                            # IEP Goal Coverage
                            if report_data['goal_coverage']:
                                st.subheader('🎯 IEP Goal Coverage')
                                goal_df = pd.DataFrame([
                                    {
                                        'Student': student_name,
                                        'Goals Addressed': ', '.join([goal.replace('_', ' ').title() for goal in coverage['goals_addressed']]),
                                        'Tasks Completed': coverage['task_count']
                                    }
                                    for student_name, coverage in report_data['goal_coverage'].items()
                                ])
                                st.dataframe(goal_df, use_container_width=True)
                            else:
                                st.info('ℹ️ No goal coverage data available')
                            
                            # Store report data in session state for export
                            st.session_state['current_report'] = report_data
                    
                    else:
                        # Generate master report
                        master_data = report_generator.generate_master_report(start_date, end_date)
                        
                        # Display master report
                        st.success('✅ Master report generated successfully!')
                        
                        # Master report header
                        st.markdown(f"## Master Weekly Report - All Staff")
                        st.markdown(f"**Period:** {master_data['report_period']['formatted_period']}")
                        
                        # Master summary metrics
                        summary = master_data['master_summary']
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric('Staff Members', summary['staff_count'])
                        with col2:
                            st.metric('Total Tasks', summary['total_tasks'])
                        with col3:
                            st.metric('Completed', summary['completed_tasks'])
                        with col4:
                            st.metric('Missed', summary['missed_tasks'])
                        with col5:
                            st.metric('Overall Rate', f"{summary['completion_rate']}%")
                        
                        # Staff breakdown
                        st.subheader('👥 Staff Performance Breakdown')
                        staff_summary_df = pd.DataFrame([
                            {
                                'Staff Member': staff_report['staff_name'],
                                'Total Tasks': staff_report['summary']['total_tasks'],
                                'Completed': staff_report['summary']['completed_tasks'],
                                'Missed': staff_report['summary']['missed_tasks'],
                                'Completion Rate': f"{staff_report['summary']['completion_rate']}%",
                                'Students Served': staff_report['summary']['students_served']
                            }
                            for staff_report in master_data['staff_reports']
                        ])
                        st.dataframe(staff_summary_df, use_container_width=True)
                        
                        # Store master report data in session state for export
                        st.session_state['current_report'] = master_data
                        
                except Exception as e:
                    st.error(f'❌ Error generating report: {str(e)}')
    
    with tab3:
        st.subheader('📋 Export Options')
        st.markdown('Export your reports in various formats for sharing and record-keeping.')
        
        # Check if there's a current report to export
        if 'current_report' in st.session_state:
            report_data = st.session_state['current_report']
            
            # Export options
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('**📊 Detailed Report Export**')
                if st.button('📥 Download Detailed CSV'):
                    try:
                        with st.spinner('Preparing CSV export...'):
                            csv_filename = report_generator.export_report_to_csv(report_data)
                            st.success(f'✅ Report exported to: {csv_filename}')
                            
                            # Read the CSV file and offer download
                            with open(csv_filename, 'r') as f:
                                csv_content = f.read()
                            
                            st.download_button(
                                label='💾 Download CSV File',
                                data=csv_content,
                                file_name=csv_filename,
                                mime='text/csv'
                            )
                    except Exception as e:
                        st.error(f'❌ Export error: {str(e)}')
            
            with col2:
                st.markdown('**📈 Summary Export**')
                if st.button('📥 Download Summary CSV'):
                    try:
                        with st.spinner('Preparing summary export...'):
                            summary_filename = report_generator.export_summary_to_csv(report_data)
                            st.success(f'✅ Summary exported to: {summary_filename}')
                            
                            # Read the summary CSV file and offer download
                            with open(summary_filename, 'r') as f:
                                summary_content = f.read()
                            
                            st.download_button(
                                label='💾 Download Summary CSV',
                                data=summary_content,
                                file_name=summary_filename,
                                mime='text/csv'
                            )
                    except Exception as e:
                        st.error(f'❌ Export error: {str(e)}')
            
            # Text format export
            st.markdown('**📄 Text Format Export**')
            if st.button('📋 Generate Text Report'):
                formatted_text = report_generator.format_report_text(report_data)
                st.text_area(
                    'Report Text (Copy to clipboard)',
                    value=formatted_text,
                    height=400,
                    help='Copy this text to paste into emails or documents'
                )
                
                # Offer text download
                st.download_button(
                    label='💾 Download Text Report',
                    data=formatted_text,
                    file_name=f"weekly_report_{report_data['report_period']['start_date']}.txt",
                    mime='text/plain'
                )
        else:
            st.info('ℹ️ Generate a report first to access export options.')

def show_daily_task_feed():
    st.header('📅 Daily Task Feed')
    st.subheader('Tasks Due Today for All Staff')
    
    generator = DailyTaskFeedGenerator()
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button('🔄 Refresh Feed', type='primary'):
            st.rerun()
    
    with col1:
        st.write(f"**Today's Date:** {datetime.now().strftime('%Y-%m-%d')}")
    
    try:
        # Generate the daily feed
        feed_content = generator.generate_daily_feed()
        
        if "No tasks due today" in feed_content:
            st.info("✅ No tasks due today for any staff members.")
        else:
            # Display the feed content in a formatted way
            st.markdown("---")
            
            # Get all staff members and their tasks
            staff_members = db.query(Staff).all()
            
            if not staff_members:
                st.warning("⚠️ No staff members found. Please add staff members first.")
                return
            
            found_tasks = False
            
            for staff_member in staff_members:
                today_tasks = generator.get_today_tasks(staff_member.id)
                
                if today_tasks:
                    found_tasks = True
                    st.markdown(f"### 🧑‍🏫 {staff_member.name}")
                    
                    for task in today_tasks:
                        student_name = task.student.name if task.student else "Unknown Student"
                        
                        # Create task card
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                st.markdown(f"**{student_name}** → {task.description}")
                                if task.frequency and task.frequency.lower() != 'once':
                                    st.caption(f"Frequency: {task.frequency}")
                            
                            with col2:
                                if task.student and task.student.ard_date:
                                    days_until_ard = generator.get_days_until_ard(task.student.id)
                                    if days_until_ard is not None and days_until_ard <= 21:
                                        st.markdown(f"🔔 **ARD in {days_until_ard} days**")
                            
                            with col3:
                                st.caption(f"Category: {task.category}")
                        
                        st.markdown("---")
            
            if not found_tasks:
                st.info("✅ No tasks due today for any staff members.")
    
    except Exception as e:
        st.error(f"❌ Error generating daily task feed: {str(e)}")
    
    # Staff-specific task summary section
    st.markdown("---")
    st.subheader('📋 Staff-Specific Task Summary')
    
    staff_list = db.query(Staff).all()
    if staff_list:
        selected_staff = st.selectbox(
            'Select staff member to view their tasks:',
            [s.name for s in staff_list],
            key='staff_selector'
        )
        
        if selected_staff:
            staff_obj = db.query(Staff).filter(Staff.name == selected_staff).first()
            if staff_obj:
                try:
                    summary = generator.get_staff_task_summary(staff_obj.id)
                    st.markdown("```")
                    st.text(summary)
                    st.markdown("```")
                except Exception as e:
                    st.error(f"❌ Error generating staff summary: {str(e)}")

def show_task_recommendations():
    st.header('🎯 Task Recommendations')
    st.subheader('AI-Powered Task Suggestions Based on IEP Goals')
    
    # Get all students for selection
    students = db.query(Student).all()
    
    if not students:
        st.warning('⚠️ No students found. Please add students first to get task recommendations.')
        return
    
    # Student selection and recommendation generation
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_student_name = st.selectbox(
            'Select a student for task recommendations:',
            [s.name for s in students],
            key='recommendation_student_selector'
        )
    
    with col2:
        if st.button('🔄 Generate Recommendations', type='primary'):
            st.rerun()
    
    if selected_student_name:
        selected_student = db.query(Student).filter(Student.name == selected_student_name).first()
        
        if selected_student:
            try:
                engine = TaskRecommendationEngine()
                recommendations = engine.suggest_tasks_for_student(selected_student.id)
                
                if "error" in recommendations:
                    st.error(f"❌ {recommendations['error']}")
                    return
                
                # Display student information
                st.markdown("---")
                st.subheader(f"📋 Recommendations for {recommendations['student_name']}")
                
                # Student details in columns
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Suggestions", recommendations['total_suggestions'])
                
                with col2:
                    if recommendations.get('ard_date'):
                        days_until = (recommendations['ard_date'] - datetime.now().date()).days
                        if days_until >= 0:
                            st.metric("Days to ARD", days_until)
                        else:
                            st.metric("ARD Status", "Past Due")
                    else:
                        st.metric("ARD Date", "Not Set")
                
                with col3:
                    keywords_found = len(recommendations.get('keywords_found', []))
                    st.metric("Keywords Matched", keywords_found)
                
                # Display keywords found
                if recommendations.get('keywords_found'):
                    st.info(f"🔍 **Keywords Found:** {', '.join(recommendations['keywords_found'])}")
                
                # Display recommendations
                if recommendations['recommendations']:
                    st.markdown("---")
                    st.subheader("💡 Suggested Tasks")
                    
                    # Group recommendations by priority
                    high_priority = [r for r in recommendations['recommendations'] if r['priority'] == 'high']
                    medium_priority = [r for r in recommendations['recommendations'] if r['priority'] == 'medium']
                    
                    # High priority tasks
                    if high_priority:
                        st.markdown("### 🔥 High Priority Tasks")
                        for i, rec in enumerate(high_priority, 1):
                            with st.expander(f"{i}. {rec['task_name']}", expanded=True):
                                col1, col2 = st.columns([2, 1])
                                
                                with col1:
                                    st.write(f"**Reason:** {rec['reason']}")
                                    st.write(f"**Category:** {rec['category']}")
                                    st.write(f"**Suggested Frequency:** {rec['frequency']}")
                                    
                                    # Get staff recommendations
                                    staff_recs = engine.get_staff_recommendations(rec['category'])
                                    if staff_recs:
                                        st.write(f"**Recommended Staff:** {', '.join(staff_recs[:3])}")
                                
                                with col2:
                                    if st.button(f"✅ Create Task", key=f"create_high_{i}"):
                                        # Create the task automatically
                                        staff_list = db.query(Staff).all()
                                        if staff_list:
                                            # Try to assign to recommended staff or first available
                                            staff_to_assign = None
                                            if staff_recs:
                                                for staff_rec_name in staff_recs:
                                                    staff_obj = db.query(Staff).filter(Staff.name == staff_rec_name).first()
                                                    if staff_obj:
                                                        staff_to_assign = staff_obj
                                                        break
                                            
                                            if not staff_to_assign:
                                                staff_to_assign = staff_list[0]
                                            
                                            # Set deadline based on frequency
                                            if rec['frequency'] == 'Daily':
                                                deadline = datetime.now().date() + timedelta(days=1)
                                            elif rec['frequency'] == 'Once a Month':
                                                deadline = datetime.now().date() + timedelta(days=30)
                                            else:
                                                deadline = datetime.now().date() + timedelta(days=7)
                                            
                                            new_task = Task(
                                                description=rec['task_name'],
                                                category=rec['category'],
                                                staff_id=staff_to_assign.id,
                                                student_id=selected_student.id,
                                                deadline=deadline,
                                                frequency=rec['frequency'],
                                                completed=False
                                            )
                                            
                                            db.add(new_task)
                                            db.commit()
                                            st.success(f"✅ Task '{rec['task_name']}' created successfully!")
                                            st.rerun()
                    
                    # Medium priority tasks
                    if medium_priority:
                        st.markdown("### 📌 Medium Priority Tasks")
                        for i, rec in enumerate(medium_priority, 1):
                            with st.expander(f"{i}. {rec['task_name']}"):
                                col1, col2 = st.columns([2, 1])
                                
                                with col1:
                                    st.write(f"**Reason:** {rec['reason']}")
                                    st.write(f"**Category:** {rec['category']}")
                                    st.write(f"**Suggested Frequency:** {rec['frequency']}")
                                    
                                    # Get staff recommendations
                                    staff_recs = engine.get_staff_recommendations(rec['category'])
                                    if staff_recs:
                                        st.write(f"**Recommended Staff:** {', '.join(staff_recs[:3])}")
                                
                                with col2:
                                    if st.button(f"✅ Create Task", key=f"create_med_{i}"):
                                        # Same task creation logic as above
                                        staff_list = db.query(Staff).all()
                                        if staff_list:
                                            staff_to_assign = staff_list[0]  # Simplified for medium priority
                                            
                                            if rec['frequency'] == 'Daily':
                                                deadline = datetime.now().date() + timedelta(days=1)
                                            elif rec['frequency'] == 'Once a Month':
                                                deadline = datetime.now().date() + timedelta(days=30)
                                            else:
                                                deadline = datetime.now().date() + timedelta(days=7)
                                            
                                            new_task = Task(
                                                description=rec['task_name'],
                                                category=rec['category'],
                                                staff_id=staff_to_assign.id,
                                                student_id=selected_student.id,
                                                deadline=deadline,
                                                frequency=rec['frequency'],
                                                completed=False
                                            )
                                            
                                            db.add(new_task)
                                            db.commit()
                                            st.success(f"✅ Task '{rec['task_name']}' created successfully!")
                                            st.rerun()
                
                else:
                    st.info("✅ No new task recommendations at this time. All appropriate tasks may already be assigned.")
                
                # Show existing tasks for reference
                existing_tasks = db.query(Task).filter(
                    Task.student_id == selected_student.id,
                    Task.completed == False
                ).all()
                
                if existing_tasks:
                    st.markdown("---")
                    st.subheader("📋 Current Active Tasks")
                    for task in existing_tasks:
                        st.write(f"• {task.description} ({task.category}) - Due: {task.deadline}")
                
            except Exception as e:
                st.error(f"❌ Error generating recommendations: {str(e)}")
    
    # Bulk recommendations section
    st.markdown("---")
    st.subheader("📊 Bulk Recommendations")
    
    if st.button("🎯 Generate Recommendations for All Students"):
        try:
            engine = TaskRecommendationEngine()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            all_recommendations = {}
            
            for i, student in enumerate(students):
                status_text.text(f"Generating recommendations for {student.name}...")
                recommendations = engine.suggest_tasks_for_student(student.id)
                all_recommendations[student.name] = recommendations
                progress_bar.progress((i + 1) / len(students))
            
            status_text.text("Complete!")
            
            # Display summary
            st.subheader("📈 Recommendations Summary")
            
            summary_data = []
            for student_name, recs in all_recommendations.items():
                if "error" not in recs:
                    summary_data.append({
                        "Student": student_name,
                        "Total Recommendations": recs['total_suggestions'],
                        "High Priority": len([r for r in recs['recommendations'] if r['priority'] == 'high']),
                        "Medium Priority": len([r for r in recs['recommendations'] if r['priority'] == 'medium']),
                        "Keywords Found": len(recs.get('keywords_found', []))
                    })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Error generating bulk recommendations: {str(e)}")

def show_smart_scheduling():
    st.header('📅 Smart Scheduling')
    st.subheader('Intelligent Task Due Date Calculator')
    
    scheduling_engine = TaskSchedulingEngine()
    
    # Display grading periods
    st.markdown("---")
    st.subheader('🗓️ Academic Calendar')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Grading Periods:**")
        for period in scheduling_engine.grading_periods:
            st.write(f"Period {period['period']}: {period['start_date']} to {period['end_date']}")
    
    with col2:
        st.markdown("**Scheduling Rules:**")
        st.write("• **Daily**: Due today")
        st.write("• **Monthly**: 1st of each month")
        st.write("• **Every 9 Weeks**: End of grading period")
        st.write("• **Once a Year**: 3 weeks before ARD")
    
    # Task scheduling overview
    st.markdown("---")
    st.subheader('📊 Task Scheduling Overview')
    
    # Calculate all due dates
    all_calculations = scheduling_engine.calculate_all_task_due_dates()
    
    if all_calculations:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        today = datetime.now().date()
        overdue_count = len([c for c in all_calculations if c['due_date'] and c['due_date'] < today])
        urgent_count = len([c for c in all_calculations if c['due_date'] and 0 <= (c['due_date'] - today).days <= 3])
        soon_count = len([c for c in all_calculations if c['due_date'] and 4 <= (c['due_date'] - today).days <= 7])
        
        with col1:
            st.metric("Total Tasks", len(all_calculations))
        with col2:
            st.metric("Overdue", overdue_count)
        with col3:
            st.metric("Due in 1-3 Days", urgent_count)
        with col4:
            st.metric("Due in 4-7 Days", soon_count)
        
        # Tasks due soon section
        st.markdown("---")
        st.subheader('🚨 Tasks Due Soon')
        
        due_soon = scheduling_engine.get_tasks_due_soon(7)
        
        if due_soon:
            for task in due_soon:
                urgency_level = "🔴 URGENT" if task['urgency_days'] <= 3 else "🟡 SOON"
                
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{task['task_name']}** ({task['student_name']})")
                        st.caption(f"Reason: {task['reason']}")
                    
                    with col2:
                        st.write(f"Due: {task['due_date']}")
                        st.write(f"{urgency_level}")
                    
                    with col3:
                        if task['urgency_days'] >= 0:
                            st.write(f"In {task['urgency_days']} days")
                        else:
                            st.write(f"{abs(task['urgency_days'])} days ago")
                
                st.markdown("---")
        else:
            st.info("✅ No tasks due in the next 7 days.")
        
        # Detailed scheduling report
        st.markdown("---")
        st.subheader('📋 Detailed Scheduling Report')
        
        # Student filter
        students = db.query(Student).all()
        student_options = ['All Students'] + [s.name for s in students]
        selected_student = st.selectbox('Filter by student:', student_options)
        
        if st.button('📄 Generate Report'):
            if selected_student == 'All Students':
                report = scheduling_engine.generate_scheduling_report()
            else:
                student_obj = db.query(Student).filter(Student.name == selected_student).first()
                if student_obj:
                    report = scheduling_engine.generate_scheduling_report(student_obj.id)
                else:
                    report = "Student not found."
            
            st.text_area("Scheduling Report", report, height=400)
        
        # Deadline update functionality
        st.markdown("---")
        st.subheader('🔄 Update Task Deadlines')
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button('🔍 Preview Deadline Updates'):
                update_result = scheduling_engine.update_task_deadlines(auto_update=False)
                
                if update_result['tasks']:
                    st.write(f"**{update_result['updated_count']} tasks need deadline updates:**")
                    
                    for task in update_result['tasks']:
                        if task.get('needs_update'):
                            st.write(f"• **{task['task_name']}**")
                            st.write(f"  Current: {task['current_deadline']}")
                            st.write(f"  Suggested: {task['suggested_deadline']}")
                            st.write(f"  Reason: {task['reason']}")
                            st.write("")
                else:
                    st.success("✅ All task deadlines are up to date.")
        
        with col2:
            if st.button('⚡ Auto-Update All Deadlines', type='primary'):
                update_result = scheduling_engine.update_task_deadlines(auto_update=True)
                
                if update_result['updated_count'] > 0:
                    st.success(f"✅ Updated {update_result['updated_count']} task deadlines.")
                    
                    for task in update_result['tasks']:
                        st.write(f"• {task['task_name']}: {task['old_deadline']} → {task['new_deadline']}")
                    
                    st.rerun()
                else:
                    st.info("✅ All task deadlines were already up to date.")
        
        # Frequency distribution chart
        st.markdown("---")
        st.subheader('📈 Task Frequency Distribution')
        
        frequency_counts = {}
        for calc in all_calculations:
            freq = calc['frequency'] or 'Once'
            frequency_counts[freq] = frequency_counts.get(freq, 0) + 1
        
        if frequency_counts:
            freq_df = pd.DataFrame(
                list(frequency_counts.items()),
                columns=['Frequency', 'Count']
            )
            
            fig = px.pie(freq_df, values='Count', names='Frequency', 
                        title='Task Distribution by Frequency')
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No tasks found for scheduling analysis.")
    
    # Scheduling configuration
    st.markdown("---")
    st.subheader('⚙️ Scheduling Configuration')
    
    with st.expander("Advanced Settings"):
        st.write("**Current Settings:**")
        st.write(f"• School Year: {scheduling_engine.school_year_start} to {scheduling_engine.school_year_end}")
        st.write(f"• Monthly tasks due on: {scheduling_engine.monthly_day_preference}{'st' if scheduling_engine.monthly_day_preference == 1 else 'th'} of month")
        st.write(f"• ARD buffer: {scheduling_engine.ard_buffer_weeks} weeks before ARD date")
        
        st.info("Scheduling settings can be customized in the scheduling_engine.py file.")

def show_recurring_tasks():
    st.header('🔁 Recurring Task Automation')
    st.subheader('Automated Daily Task Generation')
    
    recurring_generator = RecurringTaskGenerator()
    
    # Current status section
    st.markdown("---")
    st.subheader('📊 System Status')
    
    col1, col2, col3 = st.columns(3)
    
    # Get system statistics
    session = db
    template_count = session.execute(text("SELECT COUNT(*) FROM recurring_task_templates")).scalar()
    exception_count = session.execute(text("SELECT COUNT(*) FROM task_exceptions")).scalar()
    calendar_count = session.execute(text("SELECT COUNT(*) FROM school_calendar")).scalar()
    
    with col1:
        st.metric("Recurring Templates", template_count)
    with col2:
        st.metric("Task Exceptions", exception_count)
    with col3:
        st.metric("Calendar Events", calendar_count)
    
    # Today's generation section
    st.markdown("---")
    st.subheader('🗓️ Today\'s Task Generation')
    
    today = datetime.now().date()
    is_school_day, reason = recurring_generator.is_school_day(today)
    
    if is_school_day:
        st.success(f"✅ Today is a school day")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button('🚀 Generate Today\'s Tasks', type='primary'):
                results = recurring_generator.generate_recurring_tasks(today)
                
                if results['generated_tasks']:
                    st.success(f"✅ Generated {len(results['generated_tasks'])} recurring tasks!")
                    
                    with st.expander("View Generated Tasks"):
                        for task in results['generated_tasks']:
                            st.write(f"• {task}")
                    
                    st.rerun()
                else:
                    st.info("No new tasks to generate today.")
                
                if results['skipped_tasks']:
                    with st.expander("Skipped Tasks"):
                        for task in results['skipped_tasks']:
                            st.write(f"• {task}")
        
        with col2:
            if st.button('📋 Preview Generation'):
                results = recurring_generator.generate_recurring_tasks(today)
                
                st.write("**Preview of tasks that would be generated:**")
                if results['generated_tasks']:
                    for task in results['generated_tasks']:
                        st.write(f"• {task}")
                else:
                    st.write("No tasks would be generated today.")
    else:
        st.warning(f"❌ Not a school day: {reason}")
    
    # Recurring templates management
    st.markdown("---")
    st.subheader('📝 Recurring Task Templates')
    
    # Filter by staff
    staff_members = session.query(Staff).all()
    staff_options = ['All Staff'] + [s.name for s in staff_members]
    selected_staff = st.selectbox('Filter by staff member:', staff_options)
    
    # Get templates
    if selected_staff == 'All Staff':
        templates = recurring_generator.get_recurring_templates()
    else:
        staff_obj = session.query(Staff).filter(Staff.name == selected_staff).first()
        if staff_obj:
            templates = recurring_generator.get_recurring_templates(staff_obj.id)
        else:
            templates = []
    
    if templates:
        # Display templates in a table format
        template_data = []
        for template in templates:
            template_id, task_name, category, frequency, is_active, staff_id, student_id, last_generated_date, created_at = template
            
            # Get staff name
            staff = session.query(Staff).filter(Staff.id == staff_id).first()
            staff_name = staff.name if staff else "Unknown"
            
            # Get student name if applicable
            if student_id:
                student = session.query(Student).filter(Student.id == student_id).first()
                student_name = student.name if student else "Unknown"
            else:
                student_name = "All Students"
            
            template_data.append({
                'Task Name': task_name,
                'Category': category,
                'Frequency': frequency,
                'Staff': staff_name,
                'Students': student_name,
                'Active': '✅' if is_active else '❌',
                'Last Generated': str(last_generated_date) if last_generated_date else 'Never'
            })
        
        df = pd.DataFrame(template_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No recurring task templates found.")
    
    # Add new template section
    st.markdown("---")
    st.subheader('➕ Add New Recurring Template')
    
    with st.expander("Create New Template"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_task_name = st.text_input('Task Name')
            new_category = st.selectbox('Category', ['Administrative', 'Therapy', 'Documentation', 'Assessment', 'General'])
            new_frequency = st.selectbox('Frequency', ['Daily', 'Weekly', 'Monthly', 'Every 9 Weeks'])
        
        with col2:
            staff_for_template = st.selectbox('Assign to Staff', [s.name for s in staff_members])
            student_for_template = st.selectbox('Assign to Student (optional)', ['All Students'] + [s.name for s in session.query(Student).all()])
        
        if st.button('Create Template'):
            if new_task_name and staff_for_template:
                # Get staff ID
                staff_obj = session.query(Staff).filter(Staff.name == staff_for_template).first()
                
                # Get student ID if specified
                student_id = None
                if student_for_template != 'All Students':
                    student_obj = session.query(Student).filter(Student.name == student_for_template).first()
                    if student_obj:
                        student_id = student_obj.id
                
                if staff_obj:
                    success = recurring_generator.add_recurring_task_template(
                        new_task_name, new_category, new_frequency, staff_obj.id, student_id
                    )
                    
                    if success:
                        st.success("✅ Template created successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to create template.")
                else:
                    st.error("❌ Staff member not found.")
            else:
                st.error("❌ Please fill in all required fields.")
    
    # Task exceptions management
    st.markdown("---")
    st.subheader('🚫 Task Exceptions')
    
    with st.expander("Add Task Exception"):
        col1, col2 = st.columns(2)
        
        with col1:
            exception_staff = st.selectbox('Staff Member', [s.name for s in staff_members], key='exception_staff')
            exception_task = st.text_input('Task Name to Skip')
            exception_date = st.date_input('Exception Date')
        
        with col2:
            exception_student = st.selectbox('Student (optional)', ['All Students'] + [s.name for s in session.query(Student).all()], key='exception_student')
            exception_reason = st.text_input('Reason for Exception')
        
        if st.button('Add Exception'):
            if exception_staff and exception_task and exception_reason:
                # Get staff ID
                staff_obj = session.query(Staff).filter(Staff.name == exception_staff).first()
                
                # Get student ID if specified
                student_id = None
                if exception_student != 'All Students':
                    student_obj = session.query(Student).filter(Student.name == exception_student).first()
                    if student_obj:
                        student_id = student_obj.id
                
                if staff_obj:
                    success = recurring_generator.add_task_exception(
                        staff_obj.id, exception_task, exception_date, exception_reason, student_id
                    )
                    
                    if success:
                        st.success("✅ Exception added successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to add exception.")
                else:
                    st.error("❌ Staff member not found.")
            else:
                st.error("❌ Please fill in all required fields.")
    
    # School calendar management
    st.markdown("---")
    st.subheader('📅 School Calendar')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Upcoming School Events:**")
        
        # Show next 10 calendar events
        upcoming_events = session.execute(text(
            "SELECT date, event_name, event_type FROM school_calendar WHERE date >= CURRENT_DATE ORDER BY date LIMIT 10"
        )).fetchall()
        
        if upcoming_events:
            for event in upcoming_events:
                event_date, event_name, event_type = event
                st.write(f"📅 {event_date}: {event_name} ({event_type})")
        else:
            st.info("No upcoming events scheduled.")
    
    with col2:
        with st.expander("Add Calendar Event"):
            cal_date = st.date_input('Event Date')
            cal_name = st.text_input('Event Name')
            cal_type = st.selectbox('Event Type', ['holiday', 'break', 'staff_development', 'other'])
            
            if st.button('Add Event'):
                if cal_name:
                    try:
                        session.execute(text(
                            "INSERT INTO school_calendar (date, event_name, event_type) VALUES (:date, :name, :type)"
                        ), {"date": cal_date, "name": cal_name, "type": cal_type})
                        session.commit()
                        st.success("✅ Event added to calendar!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding event: {str(e)}")
                else:
                    st.error("❌ Please enter an event name.")
    
    # Generation report
    st.markdown("---")
    st.subheader('📊 Generation Report')
    
    test_date = st.date_input('Generate report for date:', value=today)
    
    if st.button('📄 Generate Report'):
        report = recurring_generator.generate_summary_report(test_date)
        st.text_area("Recurring Task Report", report, height=400)

def show_teacher_interface():
    st.header('👩‍🏫 Teacher Task Interface')
    st.subheader('Daily Task Management & Completion')
    
    teacher_interface = TeacherTaskInterface()
    
    # Teacher selection
    st.markdown("---")
    st.subheader('👤 Select Teacher')
    
    teachers = teacher_interface.get_all_teachers()
    if not teachers:
        st.error("No teachers found in the system. Please add teachers first.")
        return
    
    teacher_options = [f"{t.name} ({t.expertise})" for t in teachers]
    selected_teacher_str = st.selectbox('Choose teacher:', teacher_options)
    
    # Get selected teacher
    selected_teacher_name = selected_teacher_str.split(' (')[0]
    selected_teacher = next((t for t in teachers if t.name == selected_teacher_name), None)
    
    if not selected_teacher:
        st.error("Teacher not found")
        return
    
    # Date selection
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        target_date = st.date_input('Task Date:', value=datetime.now().date())
    
    with col2:
        if st.button('🔄 Refresh Tasks'):
            st.rerun()
    
    # Display teacher dashboard
    st.markdown("---")
    st.subheader(f'📊 Dashboard for {selected_teacher.name}')
    
    summary = teacher_interface.get_task_summary(selected_teacher.id, target_date)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tasks", summary['total_tasks'])
    with col2:
        st.metric("Completed", summary['completed_tasks'], delta=f"{summary['completion_rate']:.1f}%")
    with col3:
        st.metric("Pending", summary['pending_tasks'])
    with col4:
        if summary['total_tasks'] > 0:
            progress = summary['completed_tasks'] / summary['total_tasks']
            st.progress(progress)
            st.caption(f"{summary['completion_rate']:.1f}% Complete")
    
    # Category breakdown
    if summary['categories']:
        st.markdown("---")
        st.subheader('📋 Tasks by Category')
        
        category_data = []
        for category, stats in summary['categories'].items():
            category_data.append({
                'Category': category,
                'Total': stats['total'],
                'Completed': stats['completed'],
                'Pending': stats['pending'],
                'Progress': f"{(stats['completed']/stats['total']*100):.1f}%" if stats['total'] > 0 else "0%"
            })
        
        if category_data:
            category_df = pd.DataFrame(category_data)
            st.dataframe(category_df, use_container_width=True)
    
    # Task management section
    st.markdown("---")
    st.subheader('✅ Task Management')
    
    # Get pending and completed tasks
    pending_tasks = teacher_interface.get_pending_tasks(selected_teacher.id, target_date)
    completed_tasks = teacher_interface.get_completed_tasks(selected_teacher.id, target_date)
    
    # Pending tasks section
    if pending_tasks:
        st.markdown("### ⏳ Pending Tasks")
        
        for i, task in enumerate(pending_tasks):
            with st.expander(f"📝 {task['task_name']} - {task['student_name']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Category:** {task['category']}")
                    st.write(f"**Student:** {task['student_name']}")
                    st.write(f"**Due Date:** {task['deadline']}")
                    st.write(f"**Frequency:** {task['frequency']}")
                
                with col2:
                    # Task completion form
                    completion_note = st.text_area(
                        'Completion Note (optional):',
                        key=f"note_{task['task_id']}",
                        height=80,
                        placeholder="e.g., 'Student was absent', 'Completed during small group'"
                    )
                    
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        if st.button('✅ Complete', key=f"complete_{task['task_id']}", type='primary'):
                            success = teacher_interface.mark_task_complete(
                                task['task_id'],
                                completion_note=completion_note if completion_note else None,
                                completed_by=selected_teacher.name
                            )
                            
                            if success:
                                st.success("Task completed!")
                                st.rerun()
                            else:
                                st.error("Failed to complete task")
                    
                    with col_b:
                        if completion_note and st.button('📝 Add Note', key=f"note_only_{task['task_id']}"):
                            success = teacher_interface.add_task_note(task['task_id'], completion_note)
                            
                            if success:
                                st.success("Note added!")
                                st.rerun()
                            else:
                                st.error("Failed to add note")
    else:
        st.success("🎉 All tasks completed for this date!")
    
    # Completed tasks section
    if completed_tasks:
        st.markdown("---")
        st.markdown("### ✅ Completed Tasks")
        
        for task in completed_tasks:
            with st.expander(f"✅ {task['task_name']} - {task['student_name']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Category:** {task['category']}")
                    st.write(f"**Student:** {task['student_name']}")
                    if task['completed_at']:
                        st.write(f"**Completed At:** {task['completed_at'].strftime('%Y-%m-%d %H:%M')}")
                    if task['completion_note']:
                        st.write(f"**Note:** {task['completion_note']}")
                
                with col2:
                    if st.button('↩️ Mark Incomplete', key=f"incomplete_{task['task_id']}"):
                        success = teacher_interface.mark_task_incomplete(task['task_id'])
                        
                        if success:
                            st.success("Task marked as incomplete!")
                            st.rerun()
                        else:
                            st.error("Failed to mark task as incomplete")
    
    # Quick stats
    st.markdown("---")
    st.subheader('📈 Quick Statistics')
    
    if summary['total_tasks'] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            # Completion rate chart
            completion_data = {
                'Status': ['Completed', 'Pending'],
                'Count': [summary['completed_tasks'], summary['pending_tasks']]
            }
            
            if completion_data['Count'][0] > 0 or completion_data['Count'][1] > 0:
                fig_pie = px.pie(
                    values=completion_data['Count'],
                    names=completion_data['Status'],
                    title='Task Completion Status',
                    color_discrete_map={'Completed': '#00CC96', 'Pending': '#FFA15A'}
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Category breakdown chart
            if summary['categories']:
                category_names = list(summary['categories'].keys())
                category_counts = [summary['categories'][cat]['total'] for cat in category_names]
                
                fig_bar = px.bar(
                    x=category_names,
                    y=category_counts,
                    title='Tasks by Category',
                    labels={'x': 'Category', 'y': 'Number of Tasks'}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
    
    # Export functionality
    st.markdown("---")
    st.subheader('📄 Export & Reports')
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button('📊 Generate Daily Report'):
            dashboard_text = teacher_interface.display_teacher_dashboard(selected_teacher.id, target_date)
            st.text_area('Daily Report', dashboard_text, height=300)
    
    with col2:
        if summary['total_tasks'] > 0:
            # Prepare task data for export
            all_tasks = summary['tasks']
            export_data = []
            
            for task in all_tasks:
                export_data.append({
                    'Task': task['task_name'],
                    'Category': task['category'],
                    'Student': task['student_name'],
                    'Due Date': str(task['deadline']),
                    'Completed': 'Yes' if task['completed'] else 'No',
                    'Completed At': str(task['completed_at']) if task['completed_at'] else '',
                    'Note': task['completion_note'] if task['completion_note'] else ''
                })
            
            if export_data:
                export_df = pd.DataFrame(export_data)
                csv = export_df.to_csv(index=False)
                
                st.download_button(
                    label='📥 Download CSV Report',
                    data=csv,
                    file_name=f'{selected_teacher.name.replace(" ", "_")}_tasks_{target_date}.csv',
                    mime='text/csv'
                )

def show_dashboard():
    st.header('🎯 Educational Task Management Dashboard')
    st.write('Welcome to the Educational Task Management System! This platform helps you manage and track educational tasks for students and staff.')

    col1, col2, col3 = st.columns(3)
    with col1:
        student_count = db.query(func.count(Student.id)).scalar()
        st.metric('Total Students', student_count)
    with col2:
        staff_count = db.query(func.count(Staff.id)).scalar()
        st.metric('Total Staff', staff_count)
    with col3:
        total_tasks = db.query(func.count(Task.id)).scalar()
        completed_tasks = db.query(func.count(Task.id)).filter(Task.completed == True).scalar()
        st.metric('Tasks', f'{completed_tasks}/{total_tasks} Complete')

    st.markdown('---')

    recent_tasks = db.query(Task).order_by(Task.deadline).limit(5).all()
    if recent_tasks:
        st.subheader('📅 Recent Tasks')
        for task in recent_tasks:
            st.write(f"• {task.description} - Due: {task.deadline}")
    else:
        st.info('ℹ️ No tasks created yet. Start by adding students and staff members!')

# Page routing
if page == 'Dashboard':
    show_dashboard()
elif page == 'Student Management':
    add_student()
    students = db.query(Student).all()
    if students:
        st.markdown('---')
        st.subheader('📚 Current Students')
        student_df = pd.DataFrame([(s.name, s.goals, s.needs) for s in students], 
                                columns=['name', 'goals', 'needs'])
        st.dataframe(student_df, use_container_width=True)
elif page == 'Staff Management':
    add_staff()
    staff = db.query(Staff).all()
    if staff:
        st.markdown('---')
        st.subheader('👥 Current Staff')
        staff_df = pd.DataFrame([(s.name, s.expertise) for s in staff],
                              columns=['name', 'expertise'])
        st.dataframe(staff_df, use_container_width=True)
elif page == 'Task Management':
    create_task()
    tasks = db.query(Task).all()
    if tasks:
        st.markdown('---')
        st.subheader('📋 Current Tasks')
        task_df = pd.DataFrame(
            [(t.description, t.category, t.staff_member.name, t.student.name, t.deadline, t.completed) 
             for t in tasks],
            columns=['description', 'category', 'staff_assigned', 'student', 'deadline', 'completed']
        )
        st.dataframe(task_df, use_container_width=True)
elif page == 'Daily Task Feed':
    show_daily_task_feed()
elif page == 'Teacher Interface':
    show_teacher_interface()
elif page == 'Task Recommendations':
    show_task_recommendations()
elif page == 'Smart Scheduling':
    show_smart_scheduling()
elif page == 'Recurring Tasks':
    show_recurring_tasks()
elif page == 'Progress Tracking':
    track_progress()
elif page == 'Reports':
    generate_reports()