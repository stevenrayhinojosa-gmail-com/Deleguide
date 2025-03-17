import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# Initialize session state for data storage
if 'students_df' not in st.session_state:
    st.session_state.students_df = pd.DataFrame(columns=['name', 'goals', 'needs'])
if 'staff_df' not in st.session_state:
    st.session_state.staff_df = pd.DataFrame(columns=['name', 'expertise'])
if 'tasks_df' not in st.session_state:
    st.session_state.tasks_df = pd.DataFrame(columns=['description', 'category', 'staff_assigned', 'student', 'deadline', 'completed'])

# Main app title
st.title('Educational Task Management System')

# Sidebar navigation
page = st.sidebar.selectbox('Navigation', 
    ['Student Management', 'Staff Management', 'Task Management', 'Progress Tracking', 'Reports'])

def add_student():
    st.subheader('Add New Student')
    name = st.text_input('Student Name')
    goals = st.multiselect('Educational Goals', 
        ['Math', 'ELA', 'Social Skills', 'Science', 'Fine Motor Skills'])
    needs = st.multiselect('Specific Needs',
        ['Reading Comprehension', 'Math Support', 'Behavioral Support', 'Fine Motor Skills'])
    
    if st.button('Add Student'):
        if name and goals and needs:
            new_student = pd.DataFrame({
                'name': [name],
                'goals': [','.join(goals)],
                'needs': [','.join(needs)]
            })
            st.session_state.students_df = pd.concat([st.session_state.students_df, new_student], ignore_index=True)
            st.success(f'Student {name} added successfully!')
        else:
            st.error('Please fill in all fields')

def add_staff():
    st.subheader('Add New Staff Member')
    name = st.text_input('Staff Name')
    expertise = st.multiselect('Areas of Expertise',
        ['Math', 'ELA', 'Social Skills', 'Science', 'Fine Motor Skills', 
         'Reading Comprehension', 'Behavioral Support'])
    
    if st.button('Add Staff Member'):
        if name and expertise:
            new_staff = pd.DataFrame({
                'name': [name],
                'expertise': [','.join(expertise)]
            })
            st.session_state.staff_df = pd.concat([st.session_state.staff_df, new_staff], ignore_index=True)
            st.success(f'Staff member {name} added successfully!')
        else:
            st.error('Please fill in all fields')

def create_task():
    st.subheader('Create New Task')
    description = st.text_input('Task Description')
    category = st.selectbox('Task Category', 
        ['Math', 'ELA', 'Social Skills', 'Science', 'Fine Motor Skills'])
    
    if not st.session_state.staff_df.empty:
        staff = st.selectbox('Assign Staff', st.session_state.staff_df['name'].tolist())
    else:
        st.warning('No staff members available. Please add staff first.')
        return
    
    if not st.session_state.students_df.empty:
        student = st.selectbox('Select Student', st.session_state.students_df['name'].tolist())
    else:
        st.warning('No students available. Please add students first.')
        return
    
    deadline = st.date_input('Deadline', 
        min_value=datetime.now().date(),
        max_value=datetime.now().date() + timedelta(days=365))
    
    if st.button('Create Task'):
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
            st.success('Task created successfully!')
        else:
            st.error('Please fill in all fields')

def track_progress():
    st.subheader('Task Progress Tracking')
    
    if not st.session_state.tasks_df.empty:
        for idx, task in st.session_state.tasks_df.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"Task: {task['description']} (Assigned to: {task['staff_assigned']})")
            with col2:
                st.write(f"Due: {task['deadline']}")
            with col3:
                if st.checkbox('Completed', value=task['completed'], key=f'task_{idx}'):
                    st.session_state.tasks_df.at[idx, 'completed'] = True
                else:
                    st.session_state.tasks_df.at[idx, 'completed'] = False
    else:
        st.info('No tasks available to track')

def generate_reports():
    st.subheader('Reports Dashboard')
    
    if not st.session_state.tasks_df.empty:
        # Task completion statistics
        completion_stats = st.session_state.tasks_df.groupby('staff_assigned')['completed'].agg(['count', 'sum']).reset_index()
        completion_stats.columns = ['Staff', 'Total Tasks', 'Completed Tasks']
        completion_stats['Completion Rate'] = (completion_stats['Completed Tasks'] / completion_stats['Total Tasks'] * 100).round(2)
        
        # Display statistics
        st.write("Staff Performance Summary")
        st.dataframe(completion_stats)
        
        # Create visualization
        fig = px.bar(completion_stats, 
                    x='Staff', 
                    y=['Total Tasks', 'Completed Tasks'],
                    title='Task Completion by Staff Member',
                    barmode='group')
        st.plotly_chart(fig)
        
        # Student progress
        st.write("Student Task Progress")
        student_progress = st.session_state.tasks_df.groupby('student')['completed'].agg(['count', 'sum']).reset_index()
        student_progress.columns = ['Student', 'Total Tasks', 'Completed Tasks']
        student_progress['Completion Rate'] = (student_progress['Completed Tasks'] / student_progress['Total Tasks'] * 100).round(2)
        st.dataframe(student_progress)
    else:
        st.info('No task data available for reporting')

# Page routing
if page == 'Student Management':
    add_student()
    if not st.session_state.students_df.empty:
        st.subheader('Current Students')
        st.dataframe(st.session_state.students_df)

elif page == 'Staff Management':
    add_staff()
    if not st.session_state.staff_df.empty:
        st.subheader('Current Staff')
        st.dataframe(st.session_state.staff_df)

elif page == 'Task Management':
    create_task()
    if not st.session_state.tasks_df.empty:
        st.subheader('Current Tasks')
        st.dataframe(st.session_state.tasks_df)

elif page == 'Progress Tracking':
    track_progress()

elif page == 'Reports':
    generate_reports()

