import streamlit as st

def display_mcq_quiz(all_topics):
    # Check if we need to proceed to the next question (from previous interaction)
    if st.session_state.get("proceed_to_next", False):
        # Clear the flag
        del st.session_state.proceed_to_next
        # Move to next question
        next_question()
        return

    # Get selected topic information
    if "selected_topic_data" not in st.session_state:
        st.error("No topic selected. Please select a topic first.")
        return
    
    topic_title = st.session_state.selected_topic_data.get("title", "Unknown Topic")
    
    
    # Filter only MCQ questions from the selected topic
    if "selected_topic_data" in st.session_state:
        all_questions = st.session_state.selected_topic_data.get("questions", [])
        mcq_questions = [q for q in all_questions if q.get("type") == "mcq"]
        
        # Initialize the MCQ state variables if not already set
        if "mcq_questions" not in st.session_state:
            st.session_state.mcq_questions = mcq_questions
            st.session_state.mcq_total_questions = len(mcq_questions)
            st.session_state.current_question_index = 0
            st.session_state.mcq_attempts = {}
            st.session_state.mcq_completed = False
            st.session_state.mcq_correct_answers = 0
    
    # Check if MCQ questions are available
    if not st.session_state.get("mcq_questions", []):
        st.warning(f"No MCQ questions available for topic: {topic_title}")
        if st.button("Return to Main"):
            return_to_main()
        return
    
    # Get the questions from session state
    questions = st.session_state.mcq_questions
    total_questions = len(questions)
    
    # Check if quiz is completed
    if st.session_state.get("mcq_completed", False):
        show_completion_screen()
        return
    
    # Get current question index
    current_idx = st.session_state.get("current_question_index", 0)
    
    # Make sure the index is valid
    if current_idx >= total_questions:
        st.session_state.mcq_completed = True
        show_completion_screen()
        return
    
    # Get the current question
    question = questions[current_idx]
    
    # Create a container for the question
    with st.container():
        # Display question number and progress
        st.subheader(f"Question {current_idx + 1} of {total_questions}")
        
        # Show progress bar
        progress = current_idx / total_questions
        st.progress(progress)
        
        # Display question text
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**{question.get('question', '')}**")
        
            # Get options
            options = question.get("options", [])
            if not options:
                st.error("No options available for this question.")
                if st.button("Skip to Next Question"):
                    next_question()
                return
            
            # Create a unique key for the radio button based on attempts
            attempts = len(st.session_state.mcq_attempts.get(current_idx, []))
            radio_key = f"q{current_idx}_attempt{attempts}"
            
            # Display options as radio buttons
            selected_option = st.radio(
                "Select your answer:",
                options,
                key=radio_key,
                index=None  # No default selection
            )
            
            # Show hint if user has already made an incorrect attempt
            if current_idx in st.session_state.mcq_attempts and len(st.session_state.mcq_attempts[current_idx]) > 0:
                hint_list = question.get('hints', [])
                if hint_list:
                    # Get a hint based on the number of attempts (cycle through available hints)
                    attempt_count = len(st.session_state.mcq_attempts[current_idx])
                    hint_idx = min(attempt_count - 1, len(hint_list) - 1)
                    hint = hint_list[hint_idx]
                else:
                    hint = question.get('explanation', 'Think carefully about this question.')
                
                # Move hint display to col2 instead of col1
        
        with col2: # for displaying feedback
            # Check if the user has submitted an answer for this question
            if current_idx in st.session_state.get("submitted_answers", {}):
                submitted_option = st.session_state.submitted_answers[current_idx]
                is_correct = submitted_option == question.get("correct_answer")
                
                # Store whether the answer is correct in session state
                if "correct_answers_by_question" not in st.session_state:
                    st.session_state.correct_answers_by_question = {}
                st.session_state.correct_answers_by_question[current_idx] = is_correct
                
                if is_correct:
                    st.success("✅ Correct! Well done!")
                    
                    # Show explanation if available
                    explanation = question.get("explanation", "")
                    if explanation:
                        st.info(f"Explanation: {explanation}")
                    

                else:
                    st.error("❌ That's incorrect. Please try again.")
                    
                    # Show hint after incorrect attempt
                    if current_idx in st.session_state.mcq_attempts and len(st.session_state.mcq_attempts[current_idx]) > 0:
                        st.info(f"Hint: {hint}")
            else:
                st.write("Submit your answer to see feedback.")
        
        # Only show navigation buttons if answer is not correct yet
        is_correct_answer = st.session_state.get("correct_answers_by_question", {}).get(current_idx, False)
        
        if not is_correct_answer:
    
            if st.button("Submit Answer", key=f"submit_{current_idx}"):
                if selected_option is None:
                    st.warning("Please select an answer before submitting.")
                else:
                    # Store the submitted answer in session state
                    if "submitted_answers" not in st.session_state:
                        st.session_state.submitted_answers = {}
                    
                    st.session_state.submitted_answers[current_idx] = selected_option
                    
                    # Call check_answer to evaluate but without displaying duplicate feedback
                    check_answer(selected_option, question, display_feedback=False)
                    
                    # Force rerun to update the feedback display
                    st.rerun()
                    

        else:
            # When answer is correct, only show a more prominent continue button
            st.write("")  # Add some spacing
            if st.button("Continue to Next Question →", key=f"continue_single_btn_{current_idx}", use_container_width=True):
                st.session_state.proceed_to_next = True
                st.rerun()

def check_answer(selected_option, question, display_feedback=True):
    current_idx = st.session_state.current_question_index
    correct_answer = question.get("correct_answer")
    
    # Create a two-column layout for the question and feedback
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Left column - show the question again for context
        st.markdown(f"**{question.get('question', '')}**")
        st.write(f"Your answer: {selected_option}")
    
    with col2:
        # Right column - show the feedback
        if selected_option == correct_answer:
            # Answer is correct
            st.success("✅ Correct! Well done!")
            
            # Increment correct answers count
            st.session_state.mcq_correct_answers += 1
            
            # Update topic points
            update_topic_score()
            
            # Show explanation if available
            explanation = question.get("explanation", "")
            if explanation:
                st.info(f"Explanation: {explanation}")
            
            
        else:
            # Answer is incorrect
            st.error("❌ That's incorrect. Please try again.")
            
            # Track this attempt
            if current_idx not in st.session_state.mcq_attempts:
                st.session_state.mcq_attempts[current_idx] = []
            
            st.session_state.mcq_attempts[current_idx].append(selected_option)
            
            # Rerun to show hint
            st.rerun()

def next_question():
    """
    Advances to the next question or completes the quiz if all questions are answered.
    """
    # Increment the question index
    st.session_state.current_question_index += 1
    
    # Check if this was the last question
    total_questions = len(st.session_state.mcq_questions)
    if st.session_state.current_question_index >= total_questions:
        # Set completed flag and update any completion metrics
        st.session_state.mcq_completed = True
        # Make sure completion status is updated
        update_topic_completion()
    
    # Rerun the app to display the next question or completion screen
    st.rerun()

def show_completion_screen():
    """
    Displays the quiz completion screen with results and options.
    """
    st.success("🎉 Congratulations! You've completed the quiz!")
    
    # Display score
    total_questions = st.session_state.mcq_total_questions
    correct_answers = st.session_state.mcq_correct_answers
    
    st.write(f"Your score: {correct_answers} out of {total_questions} correct")
    
    # Calculate percentage
    percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    st.progress(percentage / 100)
    st.write(f"{percentage:.1f}% correct")
    
    # Provide feedback based on score
    if percentage == 100:
        st.balloons()
        st.markdown("### 🌟 Perfect score! Outstanding work!")
    elif percentage >= 80:
        st.markdown("### Excellent work! You've mastered this topic.")
    elif percentage >= 60:
        st.write("Good job! You have a solid understanding of this topic.")
    else:
        st.write("You might want to review this topic again to improve your understanding.")
    
    # Update topic completion status
    update_topic_completion()
    
    # Options for the user
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Try Again", key="retry_quiz"):
            # Use the reset function
            reset_mcq_quiz()
            # Force rerun to restart quiz from the beginning
            st.rerun()
    
    with col2:
        if st.button("Return to Main", key="return_main_completion"):
            return_to_main()


def reset_mcq_quiz():
    """
    Resets all MCQ quiz state variables to start the quiz from the beginning.
    """
    # Reset basic quiz state
    st.session_state.current_question_index = 0
    st.session_state.mcq_attempts = {}
    st.session_state.mcq_completed = False
    st.session_state.mcq_correct_answers = 0
    
    # Clear additional states for a complete reset
    if "submitted_answers" in st.session_state:
        del st.session_state.submitted_answers
    if "correct_answers_by_question" in st.session_state:
        del st.session_state.correct_answers_by_question
    if "proceed_to_next" in st.session_state:
        del st.session_state.proceed_to_next


def update_topic_score():
    """
    Updates the topic score based on quiz performance.
    """
    if "selected_topic_data" in st.session_state and st.session_state.selected_topic_data:
        topic_title = st.session_state.selected_topic_data.get("title", "")
        
        # Calculate points based on number of correct answers
        if "topic_points" in st.session_state and "topic_total_points" in st.session_state:
            # Calculate what percentage of the max points should be awarded
            total_questions = st.session_state.mcq_total_questions
            correct_answers = st.session_state.mcq_correct_answers
            
            # Calculate percentage complete and award proportional points
            completion_percentage = correct_answers / total_questions if total_questions > 0 else 0
            total_possible_points = st.session_state.topic_total_points.get(topic_title, 0)
            points_earned = int(completion_percentage * total_possible_points)
            
            # Update points in session state (only if higher than current points)
            current_points = st.session_state.topic_points.get(topic_title, 0)
            if points_earned > current_points:
                st.session_state.topic_points[topic_title] = points_earned

def update_topic_completion():
    """
    Updates the topic completion status when all questions are answered correctly.
    """
    if "selected_topic_data" in st.session_state and st.session_state.selected_topic_data:
        topic_title = st.session_state.selected_topic_data.get("title", "")
        
        # If all questions correct, mark topic as completed
        if st.session_state.mcq_correct_answers == st.session_state.mcq_total_questions:
            if "topic_points" in st.session_state and "topic_total_points" in st.session_state:
                # Award full points
                st.session_state.topic_points[topic_title] = st.session_state.topic_total_points.get(topic_title, 0)
                
                # Check if this is a required topic and update completed topics count
                if (st.session_state.selected_topic_data.get("required", False) and 
                    "completed_topics_count" in st.session_state):
                    # Only increment if this topic wasn't already counted as complete
                    current_points = st.session_state.topic_points.get(topic_title, 0)
                    core_points = st.session_state.topic_core_points.get(topic_title, 0)
                    
                    if current_points < core_points:
                        st.session_state.completed_topics_count += 1

def return_to_main():
    """
    Returns to the main page.
    """
    st.session_state.current_page = "chat"
    st.rerun()