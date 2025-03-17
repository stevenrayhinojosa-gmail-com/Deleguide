import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

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

# Initialize session state for data storage
if 'students_df' not in st.session_state:
    st.session_state.students_df = pd.DataFrame(columns=['name', 'goals', 'needs'])
if 'staff_df' not in st.session_state:
    st.session_state.staff_df = pd.DataFrame(columns=['name', 'expertise'])
if 'tasks_df' not in st.session_state:
    st.session_state.tasks_df = pd.DataFrame(columns=['description', 'category', 'staff_assigned', 'student', 'deadline', 'completed'])

# Sidebar configuration
with st.sidebar:
    st.title('📚 Navigation')
    st.markdown('---')
    page = st.selectbox(
        'Choose a section',
        ['Dashboard', 'Student Management', 'Staff Management', 'Task Management', 'Progress Tracking', 'Reports'],
        index=0
    )
    st.markdown('---')
    st.markdown('### Quick Stats')
    col1, col2 = st.columns(2)
    with col1:
        st.metric('Students', len(st.session_state.students_df))
    with col2:
        st.metric('Staff', len(st.session_state.staff_df))

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

        submitted = st.form_submit_button('Add Student')
        if submitted:
            if name and goals and needs:
                new_student = pd.DataFrame({
                    'name': [name],
                    'goals': [','.join(goals)],
                    'needs': [','.join(needs)]
                })
                st.session_state.students_df = pd.concat([st.session_state.students_df, new_student], ignore_index=True)
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
                new_staff = pd.DataFrame({
                    'name': [name],
                    'expertise': [','.join(expertise)]
                })
                st.session_state.staff_df = pd.concat([st.session_state.staff_df, new_staff], ignore_index=True)
                st.success(f'✅ Staff member {name} added successfully!')
            else:
                st.error('❌ Please fill in all fields')

def create_task():
    st.header('✔️ Task Management')
    st.subheader('Create New Task')

    if st.session_state.staff_df.empty or st.session_state.students_df.empty:
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
            staff = st.selectbox('Assign Staff', st.session_state.staff_df['name'].tolist())
        with col2:
            student = st.selectbox('Select Student', st.session_state.students_df['name'].tolist())
            deadline = st.date_input(
                'Deadline',
                min_value=datetime.now().date(),
                max_value=datetime.now().date() + timedelta(days=365)
            )

        submitted = st.form_submit_button('Create Task')
        if submitted:
            if description and category and staff and student and deadline:
                new_task = pd.DataFrame({
                    'description': [description],
                    'category': [category],
                    'staff_assigned': [staff],
                    'student': [student],
                    'deadline': [deadline],
                    'completed': [False]
                })
                st.session_state.tasks_df = pd.concat([st.session_state.tasks_df, new_task], ignore_index=True)
                st.success('✅ Task created successfully!')
            else:
                st.error('❌ Please fill in all fields')

def track_progress():
    st.header('📊 Progress Tracking')

    if st.session_state.tasks_df.empty:
        st.info('ℹ️ No tasks available to track')
        return

    for idx, task in st.session_state.tasks_df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📌 Task: {task['description']}")
                st.caption(f"👤 Assigned to: {task['staff_assigned']} | 👨‍🎓 Student: {task['student']}")
            with col2:
                st.write(f"📅 Due: {task['deadline']}")
            with col3:
                if st.checkbox('✓ Complete', value=task['completed'], key=f'task_{idx}'):
                    st.session_state.tasks_df.at[idx, 'completed'] = True
                else:
                    st.session_state.tasks_df.at[idx, 'completed'] = False

def generate_reports():
    st.header('📈 Reports Dashboard')

    if st.session_state.tasks_df.empty:
        st.info('ℹ️ No task data available for reporting')
        return

    # Task completion statistics
    completion_stats = st.session_state.tasks_df.groupby('staff_assigned')['completed'].agg(['count', 'sum']).reset_index()
    completion_stats.columns = ['Staff', 'Total Tasks', 'Completed Tasks']
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
    st.subheader('👨‍🎓 Student Task Progress')
    student_progress = st.session_state.tasks_df.groupby('student')['completed'].agg(['count', 'sum']).reset_index()
    student_progress.columns = ['Student', 'Total Tasks', 'Completed Tasks']
    student_progress['Completion Rate'] = (student_progress['Completed Tasks'] / student_progress['Total Tasks'] * 100).round(2)
    st.dataframe(student_progress, use_container_width=True)

def show_dashboard():
    st.header('🎯 Educational Task Management Dashboard')
    st.write('Welcome to the Educational Task Management System! This platform helps you manage and track educational tasks for students and staff.')

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('Total Students', len(st.session_state.students_df))
    with col2:
        st.metric('Total Staff', len(st.session_state.staff_df))
    with col3:
        total_tasks = len(st.session_state.tasks_df)
        completed_tasks = st.session_state.tasks_df['completed'].sum()
        st.metric('Tasks', f'{completed_tasks}/{total_tasks} Complete')

    st.markdown('---')

    if not st.session_state.tasks_df.empty:
        st.subheader('📅 Recent Tasks')
        recent_tasks = st.session_state.tasks_df.sort_values('deadline').head(5)
        for _, task in recent_tasks.iterrows():
            st.write(f"• {task['description']} - Due: {task['deadline']}")
    else:
        st.info('ℹ️ No tasks created yet. Start by adding students and staff members!')

# Page routing
if page == 'Dashboard':
    show_dashboard()
elif page == 'Student Management':
    add_student()
    if not st.session_state.students_df.empty:
        st.markdown('---')
        st.subheader('📚 Current Students')
        st.dataframe(st.session_state.students_df, use_container_width=True)
elif page == 'Staff Management':
    add_staff()
    if not st.session_state.staff_df.empty:
        st.markdown('---')
        st.subheader('👥 Current Staff')
        st.dataframe(st.session_state.staff_df, use_container_width=True)
elif page == 'Task Management':
    create_task()
    if not st.session_state.tasks_df.empty:
        st.markdown('---')
        st.subheader('📋 Current Tasks')
        st.dataframe(st.session_state.tasks_df, use_container_width=True)
elif page == 'Progress Tracking':
    track_progress()
elif page == 'Reports':
    generate_reports()