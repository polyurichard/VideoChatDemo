import streamlit as st
import json

def submit_answer(current_idx, selected_option, question, llm_service):
    st.session_state.current_action = "submit_answer"
    st.session_state.submit_answer = True

    # Initialize necessary session state variables if they don't exist yet
    if "submitted_answers" not in st.session_state:
        st.session_state.submitted_answers = {}
    
    # Store the submitted answer in session state
    st.session_state.submitted_answers[current_idx] = selected_option
    
    # Initialize mcq_attempts for this question if not already done
    if "mcq_attempts" not in st.session_state:
        st.session_state.mcq_attempts = {}
    if current_idx not in st.session_state.mcq_attempts:
        st.session_state.mcq_attempts[current_idx] = []
        
    # Add this attempt to the attempts list for this question
    st.session_state.mcq_attempts[current_idx].append(selected_option)
    
    # Get point value for this question
    point_value = question.get("point_value", 1)
    
    # Evaluate the answer based on question type
    if question["type"] == "mcq":
        is_correct = evaluate_mcq_answer(selected_option, question, llm_service)
        score = point_value if is_correct else 0
        
        # Generate feedback message for MCQ
        if is_correct:
            # Include explanation if available when answer is correct
            explanation = question.get('explanation', '')
            explanation_text = f"\n\n**Explanation:** {explanation}" if explanation else ""
            feedback = f"✅ Correct! You earned {score} points.{explanation_text}"
        else:
            # If incorrect, provide hint based on number of attempts
            hint_list = question.get('hints', [])
            if hint_list:
                # Get a hint based on the number of attempts (cycle through available hints)
                attempt_count = len(st.session_state.mcq_attempts[current_idx])
                hint_idx = min(attempt_count - 1, len(hint_list) - 1)
                hint = hint_list[hint_idx]
                feedback = f"❌ Incorrect. Try again.\n\n**Hint:** {hint}"
            else:
                explanation = question.get('explanation', 'Think carefully about this question.')
                feedback = f"❌ Incorrect. Try again.\n\n**Tip:** {explanation}"
                
        # Add feedback to chat
        st.session_state.messages.append({"role": "user", "content": f"My answer: {selected_option}"})
        st.session_state.messages.append({"role": "assistant", "content": feedback})
    else:
        is_correct, score, feedback = evaluate_answer(selected_option, question, llm_service, current_idx)
        # For open-ended questions, the evaluate_answer function already adds messages to chat
    
    # Update the question score in session state - only if new score is better
    update_question_score(current_idx, question, score)
    
    # Update the topic's total points
    update_topic_score()
    
    


def return_to_main():
    st.session_state.current_page = "main_page"
    
def display_mcq_quiz(all_topics, render_chat_ui, llm_service=None):

    
    # Check if we need to proceed to the next question (from previous interaction)
    if st.session_state.get("proceed_to_next", False):
        # Clear the flag
        del st.session_state.proceed_to_next
        # Move to next question
        next_question(llm_service)
        return

    # Get selected topic information
    if "selected_topic_data" not in st.session_state:
        st.error("No topic selected. Please select a topic first.")
        return
    
    topic_title = st.session_state.selected_topic_data.get("title", "Unknown Topic")
    
    
  
    
    # Get the questions from session state
    
    questions = st.session_state.selected_topic_data["questions"]
    total_questions = len(questions)
    
    # Check if quiz is completed
    if st.session_state.get("mcq_completed", False):
        show_completion_screen()
        return
    
    # Get current question index
    current_idx = st.session_state.get("current_question_index", 0)

    # reset message context if this is the first question or if the user has moved to next question    
    if "mcq_started"  in st.session_state:
        if  st.session_state.mcq_started == True:
            # Reset message context on quiz start
            reset_message_context(llm_service, questions[current_idx])
            st.session_state.mcq_started = False
            # Store the questions and total count in session state for later reference
            st.session_state.mcq_questions = questions
            st.session_state.mcq_total_questions = total_questions
    if "next_question_called" in st.session_state:
        if st.session_state.next_question_called:
            # Reset message context when moving to next question
            reset_message_context(llm_service, questions[current_idx])
            st.session_state.next_question_called = False


    # Make sure the index is valid
    if current_idx >= total_questions:
        st.session_state.mcq_completed = True
        show_completion_screen()
        return
    
    # Get the current question
    question = questions[current_idx]


    
    # Create a container for the question
    with st.container():
        
        # Display question text
        col1, col2 = st.columns([1, 1])

        with col1:
            # Display question number and progress
 
            if question["required"]:
                required = "[Required]"
            else:
                required = ""

            st.subheader(f"Question {current_idx + 1} of {total_questions} " + required)
                        
            st.markdown(f"**{question.get('question', '')}**")
            st.markdown(f"Point Value: {question.get('point_value', 1)}")



            if question["type"] == "mcq":
                # Get options
                options = question.get("options", [])
                
                # Ensure options is a list of strings
                if isinstance(options, list) and options:
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
                    answer_value = selected_option
                else:
                    st.error("No options available for this question")
                    selected_option = None
                    answer_value = None
            else : # open-ended question
                # show a text area 
                selected_option = st.text_area(
                    "Your answer:",
                    key=f"q{current_idx}_text_area",
                    placeholder="Type your answer here..."
                )
                answer_value = selected_option


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
            submit_button = st.button("Submit Answer", key=f"submit_{current_idx}", on_click=submit_answer, args=(current_idx, answer_value, question, llm_service))

            if "submit_answer" in st.session_state and st.session_state.submit_answer:
                st.write("Answer submitted!")
                st.session_state.submit_answer = False  # Reset after submission
           
                with st.expander("Prompt", expanded=False):
                    if st.session_state.evaluate_prompt != "":
                        st.text(st.session_state.evaluate_prompt)
                #st.session_state.current_action = None  # Reset action after displaying prompt
                #st.session_state.evaluate_prompt = ""
        with col2: # the chat UI
            messages = st.container(height=500)
            with messages:
                render_chat_ui()
            
        # Remove the duplicate Next Question button
        # This button is already defined within the submitted answers condition above
        
        # Always show a skip/next button at the bottom to allow progression without answering
        st.markdown("---")
        if st.button("Next Question", key=f"skip_{current_idx}"):
            st.session_state.proceed_to_next = True
            st.rerun()

def evaluate_mcq_answer(selected_option, question, llm_service):
    is_correct = selected_option == question.get("correct_answer")
    return is_correct  # Return the boolean result
    

# evaluate answer by LLM
def evaluate_answer(input, question, llm_service, question_idx):
    print("question: ", question["question"])
    print("answer:", question["answer"])
    point_value = question["point_value"]
    print("point_value: ", point_value)
    context ={
        "topic_title": st.session_state.selected_topic_data["title"],
        "summary": st.session_state.selected_topic_data.get("summary", ""),
        "start_timestamp": st.session_state.selected_topic_data.get("start_timestamp", ""),
        "end_timestamp": st.session_state.selected_topic_data.get("end_timestamp", ""),
        "detailed_content": st.session_state.selected_topic_data.get("detailed_content", ""),
    }

    # read prompt from ./prompts/answer_evaluate.txt
    with open("./prompts/answer_evaluate.txt", "r") as f:
        prompt = f.read()
    prompt = prompt.replace("{context}", json.dumps(context))
    prompt = prompt.replace("{question}", question["question"])
    prompt = prompt.replace("{answer}", json.dumps(question["answer"], indent = 4))
    prompt = prompt.replace("{input}", input)
    prompt = prompt.replace("{", "{{").replace("}", "}}")
    print("prompt: ", prompt)

    st.session_state.evaluate_prompt = prompt


    msg = [
        ("user", prompt)
    ]
    response = llm_service.send_message(msg)
    print("-- response json ---")
    print(response)    
    # convert response from string to json
    try:
        response_json = json.loads(response)

        score = response_json["score"]
        feedback = response_json["feedback"]

        # Add user submission to chat
        st.session_state.messages.append({"role": "user", "content": "My answer:\n\n" + input})
        
        # Create enhanced feedback message
        if score >= point_value:
            # Full score - correct answer - add explanation if available
            explanation = question.get('explanation', '')
            explanation_text = f"\n\n**Explanation:** {explanation}" if explanation else ""
            assistant_feedback = f"✅ **Feedback:** {feedback}\n\n**Score:** {score}/{point_value} points{explanation_text}"
        else:
            # Partial or no score - provide hint
            hint_text = ""
            hint_list = question.get('hints', [])
            if hint_list:
                # Get a hint based on the number of attempts
                attempt_count = len(st.session_state.mcq_attempts.get(question_idx, []))
                hint_idx = min(attempt_count - 1, len(hint_list) - 1)
                hint = hint_list[hint_idx]
                hint_text = f"\n\n**Hint:** {hint}"
            
            assistant_feedback = f"⚠️ **Feedback:** {feedback}\n\n**Score:** {score}/{point_value} points{hint_text}"
        
        # Add assistant feedback to chat
        st.session_state.messages.append({"role": "assistant", "content": assistant_feedback})
    except ValueError:
        st.error("Error parsing response from LLM. Please try again.")
        return False, 0, "Error"


    if score >= point_value:
        # If score is greater than or equal to point value, consider it correct
        return True, score, feedback
    else:
        return False, score, feedback




def next_question(llm_service=None):
    st.session_state.next_question_called = True
    """
    Advances to the next question or completes the quiz if all questions are answered.
    """
    # Increment the question index
    st.session_state.current_question_index += 1
    
    # Check if this was the last question
    # Use mcq_questions from session state if available, otherwise fall back to selected_topic_data
    if "mcq_questions" in st.session_state:
        total_questions = len(st.session_state.mcq_questions)
    elif "selected_topic_data" in st.session_state:
        total_questions = len(st.session_state.selected_topic_data["questions"])
    else:
        total_questions = 0
        
    if st.session_state.current_question_index >= total_questions:
        # Set completed flag and update any completion metrics
        st.session_state.mcq_completed = True
        # Make sure completion status is updated
        update_topic_completion()
    else:
        # Only try to access the next question if we're not at the end
        if "mcq_questions" in st.session_state:
            current_question = st.session_state.mcq_questions[st.session_state.current_question_index]
        else:
            current_question = st.session_state.selected_topic_data["questions"][st.session_state.current_question_index]
        # Reset message context for the new question
        reset_message_context(llm_service, current_question)
    
    # Rerun the app to display the next question or completion screen
    st.rerun()

def show_completion_screen():
    """
    Displays the quiz completion screen with results and options.
    """
    # st.success("🎉 Congratulations! You've completed the quiz!")
    
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
    if "question_scores" in st.session_state:
        del st.session_state.question_scores
    if "proceed_to_next" in st.session_state:
        del st.session_state.proceed_to_next


def reset_message_context(llm_service, current_question):
    
    # Reset message count
    st.session_state.message_count = 0
    st.session_state.messages = []
    question = current_question
    # Add system message with the discussion prompt
    # read system message file prompts/config 3-chat_question.txt
    with open("prompts/3-chat_question.txt", "r") as f:
        system_message = f.read().strip()
    # replace {question} in system_prompt with the actual question
    system_message = system_message.replace("{question}", str(question))
    print("question: ", question)
    # replace { and } with {{ and }}
    system_message = system_message.replace("{", "{{").replace("}", "}}")
    msg = [
        ("system", system_message),
        ("user", "Let's start")
    ]
    #response = llm_service.send_message(msg)
    response = "Hello, I'm your AI assistant to help you with this question."

    # Clear previous messages and set new context
    st.session_state.messages = []
    st.session_state.messages.append({"role": "system", "content": system_message})
    st.session_state.messages.append({"role": "user", "content": "Let's start"})
    st.session_state.messages.append({"role": "assistant", "content": response})

def update_topic_score():
    """
    Updates the topic score based on accumulated question scores.
    """
    if "selected_topic_data" in st.session_state and "question_scores" in st.session_state:
        topic_title = st.session_state.selected_topic_data.get("title", "")
        
        # Calculate total points from all questions in this topic
        if "question_scores" in st.session_state:
            # Sum up scores for all questions that belong to the current quiz
            total_points = 0
            for idx, score in st.session_state.question_scores.items():
                # Only count questions that are part of the current topic's quiz
                if idx < len(st.session_state.mcq_questions):
                    total_points += score
            
            if "topic_points" in st.session_state:
                # Update points in session state for this topic only
                st.session_state.topic_points[topic_title] = total_points
                print(f"Updated total points for {topic_title}: {total_points}")
                
                # Check if this update completes a core topic
                core_points = st.session_state.topic_core_points.get(topic_title, 0)
                is_required = st.session_state.selected_topic_data.get("required", False)
                
                # Track if this update newly completes the topic
                key = f"completed_{topic_title}"
                previously_completed = st.session_state.get(key, False)
                newly_completed = is_required and not previously_completed and total_points >= core_points
                
                if newly_completed:
                    st.session_state[key] = True
                    st.session_state.completed_topics_count += 1
                    print(f"Topic {topic_title} newly completed! Points: {total_points}/{core_points}")
        
        # Update topic completion status
        update_topic_completion()

def update_topic_completion():
    """
    Updates topic completion status based on accumulated points.
    """
    if "selected_topic_data" in st.session_state and "question_scores" in st.session_state:
        topic_title = st.session_state.selected_topic_data.get("title", "")
        is_required = st.session_state.selected_topic_data.get("required", False)
        
        # Calculate total earned points for this topic
        if "question_scores" in st.session_state:
            # Calculate sum of scores for current topic's questions
            total_points = 0
            for idx, score in st.session_state.question_scores.items():
                if idx < len(st.session_state.mcq_questions):
                    total_points += score
        else:
            total_points = 0
        
        # Get core points threshold from session state
        core_points = st.session_state.topic_core_points.get(topic_title, 0)
        
        # Update topic points
        if "topic_points" in st.session_state:
            st.session_state.topic_points[topic_title] = total_points
        
        # Check if this topic is newly completed
        # A topic is completed when earned points >= core points
        key = f"completed_{topic_title}"
        previously_completed = st.session_state.get(key, False)
        
        if is_required and not previously_completed and total_points >= core_points:
            # Mark this topic as completed
            st.session_state[key] = True
            
            # Increment completed topics count
            if "completed_topics_count" in st.session_state:
                st.session_state.completed_topics_count += 1
                print(f"Marked topic {topic_title} as completed with {total_points}/{core_points} points")

def update_question_score(current_idx, question, score):
    """
    Updates the question score in session state, only if the new score is higher.
    
    Parameters:
        current_idx (int): The index of the current question
        question (dict): The question data dictionary
        score (float): The score achieved for this attempt
    """
    # Initialize question scores in session state if not exists
    if "question_scores" not in st.session_state:
        st.session_state.question_scores = {}
        
    # Get current score for this question (default 0 if not set)
    current_score = st.session_state.question_scores.get(current_idx, 0)
    
    # Only update if new score is higher than current score
    if score > current_score:
        st.session_state.question_scores[current_idx] = score
        print(f"Updated score for question {current_idx}: {score} (was {current_score})")
    
    # Calculate and update total correct answers count
    point_value = question.get("point_value", 1)
    is_fully_correct = st.session_state.question_scores.get(current_idx, 0) >= point_value
    
    # Update the mcq_correct_answers count for completion screen
    correct_count = sum(1 for q_idx, score in st.session_state.question_scores.items() 
                     if score >= st.session_state.mcq_questions[q_idx].get("point_value", 1))
    st.session_state.mcq_correct_answers = correct_count