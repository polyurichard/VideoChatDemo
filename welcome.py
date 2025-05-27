import streamlit as st

# Function for the welcome page
def welcome_page():
    st.title("Interactive Video Learning")
    
    # Add YouTube video embed at the top
    youtube_url = "https://www.youtube.com/watch?v=nKW8Ndu7Mjw"
    st.video(youtube_url)
    
    # Add a brief introduction to the video content
    st.write("""
    In this interactive learning module, you'll explore the fundamentals of machine learning through a practical example.
    The video above introduces how machine learning works by walking through a simple classification problem: distinguishing
    between wine and beer. You'll learn about key concepts like data collection, preparation, model training, evaluation,
    and prediction - the core steps in any machine learning workflow.
    """)
    
 
    # Start button
    st.write("")  # Add some space
    start_col1, start_col2, start_col3 = st.columns([1, 2, 1])
    with start_col2:
        if st.button("Start Learning", key="start_learning_btn", use_container_width=True):
            st.session_state.current_page = "main"
            st.rerun()
