import streamlit as st
import json

def show_question_bank(all_topics):
   
    st.header("Question Bank")
    
    # Collect all questions from all topics
    all_questions = []
    for topic in all_topics["topics"]:
        topic_title = topic["title"]
        for question in topic.get("questions", []):
            # Add topic title to the question for reference
            question["topic_title"] = topic_title
            all_questions.append(question)
            
    # Create filter selectors in two columns
    filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 1])
    
    with filter_col1:
        # Create a filter for topics
        topic_titles = ["All Topics"] + list(set(topic["title"] for topic in all_topics["topics"]))
        selected_topic = st.selectbox("Filter by topic:", topic_titles)
    
    with filter_col2:
        # Create a filter for question types
        question_types = ["All Types"] + sorted(list(set(q.get("type", "unknown") for q in all_questions)))
        selected_type = st.selectbox("Filter by question type:", question_types)
    
    with filter_col3:
        # Create a filter for required/optional
        required_filter = st.radio("Show questions:", ["All", "Required Only", "Optional Only"], horizontal=True)
    
    # Apply filters
    filtered_questions = all_questions
    
    if selected_topic != "All Topics":
        filtered_questions = [q for q in filtered_questions if q.get("topic_title") == selected_topic]
        
    if selected_type != "All Types":
        filtered_questions = [q for q in filtered_questions if q.get("type") == selected_type]
    
    if required_filter == "Required Only":
        filtered_questions = [q for q in filtered_questions if q.get("required", False)]
    elif required_filter == "Optional Only":
        filtered_questions = [q for q in filtered_questions if not q.get("required", False)]
    
    # Show results count
    st.write(f"Showing {len(filtered_questions)} questions")
    
    # Check if we have questions to display
    if not filtered_questions:
        st.info("No questions match your selected filters.")
    else:
        # Initialize session state for edited questions if not already present
        if "edited_questions" not in st.session_state:
            st.session_state.edited_questions = {}
            
        # Create an editable table of questions
        edited = False
        
        # Use a form to capture edits
        with st.form("question_table_form"):
            for i, question in enumerate(filtered_questions):
                q_id = f"{question.get('topic_title')}_{question.get('type')}_{i}"
                st.subheader(f"Question {i+1}")
                
                # Create a container for each question with columns
                cols = st.columns([3, 1])
                
                with cols[0]:
                    # Question text
                    q_text = st.text_area(
                        "Question text", 
                        question.get("question", ""), 
                        key=f"q_text_{q_id}",
                        height=100
                    )
                    
                    # Topic title (non-editable)
                    st.text_input(
                        "Topic", 
                        question.get("topic_title", ""), 
                        disabled=True,
                        key=f"topic_{q_id}" 
                    )
                    
                    # Question type
                    q_type = st.selectbox(
                        "Question type", 
                        ["mcq", "discussion", "short", "reflective"],
                        index=["mcq", "discussion", "short", "reflective"].index(question.get("type", "discussion")),
                        key=f"q_type_{q_id}"
                    )
                    
                with cols[1]:
                    # Points
                    q_points = st.number_input(
                        "Points", 
                        min_value=1, 
                        max_value=10, 
                        value=question.get("point_value", 1),
                        key=f"q_points_{q_id}"
                    )
                    
                    # Required status
                    q_required = st.checkbox(
                        "Required", 
                        value=question.get("required", False),
                        key=f"q_required_{q_id}"
                    )
                    
                    # Reference timestamp
                    q_timestamp = st.text_input(
                        "Reference timestamp", 
                        question.get("reference_timestamp", ""),
                        key=f"q_timestamp_{q_id}"
                    )
                
                # For MCQ questions, show options
                if q_type == "mcq":
                    # Options as a multi-line text area, one per line
                    options_text = "\n".join(question.get("options", ["Option 1", "Option 2", "Option 3", "Option 4"]))
                    new_options_text = st.text_area(
                        "Options (one per line)", 
                        options_text,
                        height=100,
                        key=f"q_options_{q_id}"
                    )
                    new_options = [opt.strip() for opt in new_options_text.split("\n") if opt.strip()]
                    
                    # Correct answer
                    correct_idx = 0
                    if question.get("correct_answer") in question.get("options", []):
                        correct_idx = question.get("options", []).index(question.get("correct_answer", ""))
                    
                    correct_answer = st.selectbox(
                        "Correct answer", 
                        new_options if new_options else [""],
                        index=min(correct_idx, len(new_options)-1) if new_options else 0,
                        key=f"q_correct_{q_id}"
                    )
                else:
                    # For non-MCQ questions, show sample answer
                    sample_answer = st.text_area(
                        "Sample answer", 
                        question.get("sample_answer", ""),
                        height=100,
                        key=f"q_sample_{q_id}"
                    )
                
                # Explanation for all question types
                explanation = st.text_area(
                    "Explanation", 
                    question.get("explanation", ""),
                    height=100,
                    key=f"q_explanation_{q_id}"
                )
                
                # Hints as a multi-line text area, one per line
                hints_text = "\n".join(question.get("hints", []))
                new_hints_text = st.text_area(
                    "Hints (one per line)", 
                    hints_text,
                    height=100,
                    key=f"q_hints_{q_id}"
                )
                new_hints = [hint.strip() for hint in new_hints_text.split("\n") if hint.strip()]
                
                # Store all edits in session state
                st.session_state.edited_questions[q_id] = {
                    "topic_title": question.get("topic_title"),
                    "question": q_text,
                    "type": q_type,
                    "point_value": q_points,
                    "required": q_required,
                    "reference_timestamp": q_timestamp,
                    "explanation": explanation,
                    "hints": new_hints,
                }
                
                # Add type-specific fields
                if q_type == "mcq":
                    st.session_state.edited_questions[q_id]["options"] = new_options
                    st.session_state.edited_questions[q_id]["correct_answer"] = correct_answer
                else:
                    st.session_state.edited_questions[q_id]["sample_answer"] = sample_answer
                
                st.markdown("---")
            
            # Submit button for all edits
            submit_button = st.form_submit_button("Save All Changes")
            if submit_button:
                st.success("Changes saved successfully!")
                # Here you would implement the logic to save the edits back to your data source
                # This would typically involve updating your topics_with_q.json file
                
        # Add export button outside the form
        if st.button("Export Questions"):
            # Create a JSON string of all edited questions
            export_data = json.dumps(list(st.session_state.edited_questions.values()), indent=2)
            st.download_button(
                label="Download JSON",
                data=export_data,
                file_name="exported_questions.json",
                mime="application/json"
            )
    
    # Add close button at the bottom
    if st.button("Close Question Bank", key="close_question_bank"):
        return False  # Signal to close the question bank
    
    return None  # Continue showing question bank
