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
        # Create a filter for question types - now using the new 'type' field
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
            
        # Display each question individually for editing - without expanders
        for i, question in enumerate(filtered_questions):
            # Add a separator before each question (except the first one)
            if i > 0:
                st.markdown("---")
            
            q_id = f"{question.get('topic_title')}_{question.get('type')}_{i}"
            
            # Question header with number
            st.subheader(f"Question {i+1}")
            
            # Create columns for question details
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
                
                # Question type - updated options to match new structure
                q_type = st.selectbox(
                    "Question type", 
                    ["mcq", "open-ended", "short_question", "reflective"],
                    index=["mcq", "open-ended", "short_question", "reflective"].index(question.get("type", "open-ended")) 
                    if question.get("type") in ["mcq", "open-ended", "short_question", "reflective"] else 0,
                    key=f"q_type_{q_id}"
                )

                # Question nature - new field
                q_nature = st.selectbox(
                    "Question nature", 
                    ["interest", "remember", "understand", "apply", "analyze", "evaluate", "create", "integration", "basic"],
                    index=["interest", "remember", "understand", "apply", "analyze", "evaluate", "create", "integration", "basic"].index(question.get("question_nature", "basic"))
                    if question.get("question_nature") in ["interest", "remember", "understand", "apply", "analyze", "evaluate", "create", "integration", "basic"] else 0,
                    key=f"q_nature_{q_id}"
                )
                
            with cols[1]:
                # Points
                q_points = st.number_input(
                    "Points", 
                    min_value=1, 
                    max_value=10, 
                    value=question.get("point_value", 5),
                    key=f"q_points_{q_id}"
                )
                
                # Required status
                q_required = st.checkbox(
                    "Required", 
                    value=question.get("required", False),
                    key=f"q_required_{q_id}"
                )
                
                # Reference timestamp is now in the reference_text structure
                # Display a generic field for compatibility
                q_timestamp = st.text_input(
                    "Reference timestamp", 
                    ", ".join([ref.get("timestamp", "") for ref in question.get("reference_text", [])]) 
                    if isinstance(question.get("reference_text", []), list) else "",
                    key=f"q_timestamp_{q_id}"
                )

            # Reference text section - new structure handling
            st.subheader("Reference Text")
            if isinstance(question.get("reference_text", []), list):
                for idx, ref in enumerate(question.get("reference_text", [])):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.text_area(
                            f"Reference {idx+1}", 
                            ref.get("text", ""),
                            height=68,
                            key=f"ref_text_{q_id}_{idx}"
                        )
                    with col2:
                        st.text_input(
                            "Timestamp", 
                            ref.get("timestamp", ""),
                            key=f"ref_ts_{q_id}_{idx}"
                        )
            
            # For MCQ questions, show options as individual fields
            if q_type == "mcq":
                st.subheader("Options")
                
                # Initialize options in session state if not already present
                option_key = f"options_{q_id}"
                if option_key not in st.session_state:
                    st.session_state[option_key] = question.get("options", ["Option 1", "Option 2", "Option 3", "Option 4"])
                
                # Current correct answer
                correct_answer = question.get("correct_answer", "")
                
                # Display each option with its own text field
                new_options = []
                
                # Create a checkbox for selecting the correct answer for each option
                options_to_remove = []
                correct_option = st.text_input("Correct Answer", correct_answer, key=f"correct_input_{q_id}")
                
                st.write("Enter each option below. Mark the correct one in the field above.")
                for idx, option in enumerate(st.session_state[option_key]):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        option_text = st.text_input(
                            f"Option {idx+1}", 
                            option,
                            key=f"option_{q_id}_{idx}"
                        )
                        new_options.append(option_text)
                    
                    with col2:
                        if st.button("Remove", key=f"remove_option_{q_id}_{idx}"):
                            options_to_remove.append(idx)
                
                # Handle option removal
                if options_to_remove:
                    # Remove options in reverse order to avoid index shifts
                    for idx in sorted(options_to_remove, reverse=True):
                        st.session_state[option_key].pop(idx)
                    st.rerun()
                
                # Add new option button
                if st.button("Add Option", key=f"add_option_{q_id}"):
                    st.session_state[option_key].append(f"New Option {len(st.session_state[option_key])+1}")
                    st.rerun()
                
            else:
                # For non-MCQ questions, show sample answer or answer structure based on type
                if q_type == "short_question":
                    # Short question uses direct answer
                    sample_answer = st.text_area(
                        "Sample answer", 
                        question.get("answer", ""),
                        height=100,
                        key=f"q_sample_{q_id}"
                    )
                else:
                    # Open ended uses criteria structure or could be rubric-based
                    if isinstance(question.get("answer"), list):
                        st.subheader("Answer Criteria")
                        for idx, criterion in enumerate(question.get("answer", [])):
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.text_input(
                                    f"Criterion {idx+1}",
                                    criterion.get("criteria", ""),
                                    key=f"criterion_{q_id}_{idx}"
                                )
                            with col2:
                                st.number_input(
                                    "Points",
                                    min_value=0,
                                    max_value=5,
                                    value=criterion.get("points", 1),
                                    key=f"criterion_pts_{q_id}_{idx}"
                                )
                    else:
                        # Handle string answer for backward compatibility
                        sample_answer = st.text_area(
                            "Sample answer or rubric", 
                            question.get("answer", ""),
                            height=100,
                            key=f"q_sample_{q_id}"
                        )
                
                correct_answer = ""
                new_options = []
            
            # Explanation for all question types
            explanation = st.text_area(
                "Explanation", 
                question.get("explanation", ""),
                height=100,
                key=f"q_explanation_{q_id}"
            )
            
            # Hints as individual fields
            st.subheader("Hints")
            
            # Initialize hints in session state if not already present
            hint_key = f"hints_{q_id}"
            if hint_key not in st.session_state:
                st.session_state[hint_key] = question.get("hints", ["Hint 1"])
            
            # Display each hint with its own text field
            new_hints = []
            hints_to_remove = []
            
            for idx, hint in enumerate(st.session_state[hint_key]):
                col1, col2 = st.columns([5, 1])
                with col1:
                    hint_text = st.text_area(
                        f"Hint {idx+1}", 
                        hint,
                        height=68,  # Increased from 50 to 68 to meet Streamlit's minimum height requirement
                        key=f"hint_{q_id}_{idx}"
                    )
                    new_hints.append(hint_text)
                
                with col2:
                    if st.button("Remove", key=f"remove_hint_{q_id}_{idx}"):
                        hints_to_remove.append(idx)
            
            # Handle hint removal
            if hints_to_remove:
                # Remove hints in reverse order to avoid index shifts
                for idx in sorted(hints_to_remove, reverse=True):
                    st.session_state[hint_key].pop(idx)
                st.rerun()
            
            # Add new hint button
            if st.button("Add Hint", key=f"add_hint_{q_id}"):
                st.session_state[hint_key].append(f"Hint {len(st.session_state[hint_key])+1}")
                st.rerun()
            
            # Save button for this question
            if st.button("Save Changes", key=f"save_{q_id}"):
                # Store all edits in session state
                st.session_state.edited_questions[q_id] = {
                    "topic_title": question.get("topic_title"),
                    "question": q_text,
                    "type": q_type,
                    "question_nature": q_nature,  # Add the new field
                    "point_value": q_points,
                    "required": q_required,
                    "reference_timestamp": q_timestamp,
                    "explanation": explanation,
                    "hints": new_hints,
                }
                
                # Add type-specific fields
                if q_type == "mcq":
                    st.session_state.edited_questions[q_id]["options"] = new_options
                    st.session_state.edited_questions[q_id]["correct_answer"] = correct_option
                else:
                    # Handle different answer formats based on question type
                    if q_type == "short_question":
                        st.session_state.edited_questions[q_id]["answer"] = sample_answer
                    else:
                        # For more complex answers, maintain the structure if it exists
                        if isinstance(question.get("answer"), list):
                            st.session_state.edited_questions[q_id]["answer"] = question.get("answer", [])
                        else:
                            st.session_state.edited_questions[q_id]["sample_answer"] = sample_answer
                
                st.success("Question updated successfully!")
        
        # Add a final separator after the last question
        st.markdown("---")
        
        # Add export button at the bottom
        if st.button("Export All Questions"):
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
