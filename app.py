import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from models import Student, Staff, Task, get_db
from sqlalchemy import func
from sqlalchemy import Integer
from daily_task_feed import DailyTaskFeedGenerator
from task_recommender import TaskRecommendationEngine

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
        ['Dashboard', 'Daily Task Feed', 'Task Recommendations', 'Student Management', 'Staff Management', 'Task Management', 'Progress Tracking', 'Reports'],
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
elif page == 'Task Recommendations':
    show_task_recommendations()
elif page == 'Progress Tracking':
    track_progress()
elif page == 'Reports':
    generate_reports()