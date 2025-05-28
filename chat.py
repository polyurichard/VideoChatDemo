import streamlit as st
import time
from llm import LLMService
import json
import re
from question_bank import show_question_bank
from welcome import welcome_page
from mcq_quiz import display_mcq_quiz

def get_topics():
    # get topics from sample-data/topics.json
    with open("sample-data/topics_with_q.json") as f:
        topics = json.load(f)
    return topics

# Load topics data early before any functions that need it
all_topics = get_topics()

# Initialize LLM service
gpt_version = "gpt-4o-mini"  # Default version
#gpt_version = "gpt-4.1-mini"  # Use gpt-4.1-mini for now
@st.cache_resource
def get_llm_service():
    return LLMService(
        config_path=".env",
        temperature=0,
        gpt_version=gpt_version
    )

# Get LLM service instance
llm_service = get_llm_service()

# Initialize messages list if not in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

def start_mcq_panel():
    """
    Initialize the MCQ quiz for the selected topic.
    Prepares the necessary session state variables and transitions to the MCQ quiz page.
    """
    # Store the current topic's questions in session state
    if "selected_topic_data" in st.session_state and st.session_state.selected_topic_data:
        selected_topic = st.session_state.selected_topic_data
        
        # Filter for only MCQ questions from the current selected topic
        all_questions = selected_topic.get("questions", [])
        mcq_questions = [q for q in all_questions if q.get("type") == "mcq"]
        
        if not mcq_questions:
            st.error(f"No MCQ questions available for topic: {selected_topic.get('title', '')}")
            return
            
        # Reset MCQ state to start fresh
        if "mcq_questions" in st.session_state:
            del st.session_state.mcq_questions
        if "mcq_attempts" in st.session_state:
            del st.session_state.mcq_attempts
        if "submitted_answers" in st.session_state:
            del st.session_state.submitted_answers
        if "correct_answers_by_question" in st.session_state:
            del st.session_state.correct_answers_by_question
            
        # Initialize fresh MCQ session variables
        st.session_state.mcq_questions = mcq_questions
        st.session_state.mcq_total_questions = len(mcq_questions)
        st.session_state.current_question_index = 0
        st.session_state.mcq_attempts = {}
        st.session_state.mcq_completed = False
        st.session_state.mcq_correct_answers = 0
        
        # Switch to MCQ quiz page
        st.session_state.current_page = "mcq_quiz"

    else:
        st.error("Please select a topic first.")

def extract_transcript(filename, start_timestamp, end_timestamp=None):
    """
   extract a section of the transcript based on start and end timestamps.
    """
    try:
        with open(filename, 'r') as f:
            transcript_text = f.read()
        
        # Convert timestamps to seconds for comparison
        def to_seconds(ts):
            if isinstance(ts, str):
                parts = ts.split(":")
                if len(parts) == 2:
                    return int(parts[0]) * 60 + int(parts[1])
                return int(ts)
            return ts
        
        start_seconds = to_seconds(start_timestamp)
        end_seconds = to_seconds(end_timestamp) if end_timestamp else float('inf')
        
        # Find all timestamp markers and their positions in the text
        timestamp_pattern = r'\((\d{2}):(\d{2})\)'
        matches = list(re.finditer(timestamp_pattern, transcript_text))
        
        # Extract the section that matches our timestamp range
        section_text = ""
        for i, match in enumerate(matches):
            current_minutes = int(match.group(1))
            current_seconds = int(match.group(2))
            current_total_seconds = current_minutes * 60 + current_seconds
            
            if current_total_seconds >= start_seconds:
                # Found the starting position
                start_pos = match.start()
                
                # Find the end position (either next timestamp outside our range or end of text)
                end_pos = len(transcript_text)
                for j in range(i+1, len(matches)):
                    next_minutes = int(matches[j].group(1))
                    next_seconds = int(matches[j].group(2))
                    next_total_seconds = next_minutes * 60 + next_seconds
                    
                    if next_total_seconds > end_seconds:
                        end_pos = matches[j].start()
                        break
                
                section_text = transcript_text[start_pos:end_pos].strip()
                break
                
        return section_text
    except Exception as e:
        return f"Error extracting transcript: {str(e)}"

def get_discussion_prompt():
    selected_topic_data = st.session_state.get("selected_topic_data", None)
    #print(f"Selected topic data: {selected_topic_data}")  # Debugging line
    # If no topic is selected, use the first topic
    if selected_topic_data is None and len(all_topics.get("topics", [])) > 0:
        # Extract transcript for first topic
        first_topic = all_topics["topics"][0]
        
        # Get end timestamp with a default value (next topic's start time or None)
        end_timestamp = first_topic.get("end_timestamp")
        if end_timestamp is None and len(all_topics["topics"]) > 1:
            # If no end timestamp and there's a next topic, use next topic's start time
            end_timestamp = all_topics["topics"][1].get("start_timestamp")
        
        transcript_text = extract_transcript(
            "sample-data/transcript.txt", 
            first_topic["start_timestamp"], 
            end_timestamp
        )
        
        # Extract reference texts from questions for additional context
        reference_texts = []
        if "questions" in first_topic:
            for question in first_topic["questions"]:
                if "reference_text" in question and isinstance(question["reference_text"], list):
                    for ref in question["reference_text"]:
                        if "text" in ref and "timestamp" in ref:
                            reference_texts.append(f"({ref['timestamp']}) {ref['text']}")
        
        selected_topic_data = {
            "title": first_topic["title"],
            "required": first_topic.get("required", False),
            "learning_objectives": first_topic.get("learning_objectives", []),
            "summary": first_topic.get("summary", ""),
            "start_timestamp": first_topic.get("start_timestamp", ""),
            "end_timestamp": first_topic.get("end_timestamp", ""),
            "detailed_content": first_topic.get("detailed_content", []),
            "questions": first_topic.get("questions", []),
            "transcript": transcript_text,
            "reference_texts": reference_texts  # Add extracted reference texts
        }
    
    # Read prompt template from file
    try:
        with open("prompts/topic-discuss.txt", "r") as f:
            prompt_template = f.read()
    except Exception as e:
        return f"Error reading prompt template: {str(e)}"
    
    # Format topic data as JSON string
    import json
    topic_json = json.dumps(selected_topic_data, indent=2)

    prompt_template = prompt_template.replace("{topic_and_questions}", topic_json)

    # Replace single curly braces with double curly braces (for Streamlit f-string escaping)
    prompt_template = prompt_template.replace("{", "{{").replace("}", "}}")    
    
    print(f"Generated discussion prompt: {prompt_template}")  # Debugging line
    
    return prompt_template

def calculate_total_points(topic_data):
    core_points = 0
    total_points = 0
    
    # Add points from questions
    if "questions" in topic_data:
        for question in topic_data["questions"]:
            if "point_value" in question:
                point_value = question["point_value"]
                total_points += point_value
                
                # Only add to core points if question is required
                if question.get("required", False):
                    core_points += point_value
    
    return (core_points, total_points)

def start_exercise():
    """Start the practice session with AI assistance."""
    st.session_state.start_exercise_clicked = True
    print("Start exercise button clicked")  # Debugging line

def update_topic_points(topic_title):
    """Update the points earned for a topic based on LLM evaluation of answers."""
    # Ensure we have enough messages for evaluation (at least the last user question and AI response)
    if len(st.session_state.messages) < 3:
        return
    
    # Get the last 4 messages if available (2 exchanges), otherwise get what we have
    # Skip system messages as they're not part of the visible conversation
    visible_messages = [msg for msg in st.session_state.messages if msg["role"] != "system"]
    
    # Get up to last 4 messages (or fewer if not available)
    context_messages = visible_messages[-4:] if len(visible_messages) >= 4 else visible_messages
    
    print(f"---- Using {len(context_messages)} messages for evaluation:")  # Debugging line
    print(context_messages)  # Debugging line
    
    # Format the conversation for the LLM evaluation in a plain text format
    formatted_conversation = ""
    for msg in context_messages:
        role_prefix = "User: " if msg["role"] == "user" else "Assistant: "
        formatted_conversation += f"{role_prefix}{msg['content']}\n"
    
    # Load the scoring prompt template
    try:
        with open("prompts/score_update.txt", "r") as f:
            score_prompt = f.read()
            # Replace the placeholder with the actual conversation
            score_prompt = score_prompt.replace("{conversation}", formatted_conversation)
    except Exception as e:
        print(f"Error reading score update prompt: {str(e)}")
        return
    
    # print score_prompt for debugging
    print("---- Score update prompt:")  # Debugging line
    print(score_prompt)  # Debugging line

    # Call LLM to evaluate the conversation and determine points
    evaluation = llm_service.send_message([("user", score_prompt)])
    print("---- LLM evaluation response:")  # Debugging line
    print(evaluation)  # Debugging line
    
    # Extract the points from the LLM's response (expecting JSON)
    try:
        # Try to parse the response as JSON
        evaluation_data = json.loads(evaluation.strip())
        
        # Extract score from the parsed JSON
        points_earned = evaluation_data.get("score", 0)
        user_input_type = evaluation_data.get("user_input_classification", "unknown")
        
        # Update question count if the user input was classified as a question
        if user_input_type == "question":
            st.session_state.question_count += 1
            print(f"Question count updated: {st.session_state.question_count}")
        
        # Update correct answers count if user got points for their answer
        if user_input_type == "answer" and points_earned > 0:
            st.session_state.correct_answers_count += 1
            print(f"Correct answers count updated: {st.session_state.correct_answers_count}")
        
        print(f"Points earned from LLM evaluation: {points_earned}")
        print(f"User input classified as: {user_input_type}")
        
    except json.JSONDecodeError:
        # If JSON parsing fails, try to extract just a number as fallback
        print(f"Could not parse JSON from LLM response. Trying to extract just the number.")
        try:
            # Look for digits in the response
            import re
            match = re.search(r'\d+', evaluation)
            if match:
                points_earned = int(match.group())
                print(f"Extracted points from text: {points_earned}")
            else:
                points_earned = 0
                print("No numeric value found in response.")
        except Exception as e:
            print(f"Error extracting score: {str(e)}")
            points_earned = 0
    except Exception as e:
        # Handle any other errors
        print(f"Error processing evaluation response: {str(e)}")
        points_earned = 0
    
    # Update the points in the session state
    if "topic_points" in st.session_state:
        current_points = st.session_state.topic_points.get(topic_title, 0)
        st.session_state.topic_points[topic_title] = min(
            current_points + points_earned, 
            st.session_state.topic_total_points.get(topic_title, 100)  # Cap at max points
        )
        
        # Check if this is a core topic and if all core questions are answered
        new_points = st.session_state.topic_points[topic_title]
        core_points = st.session_state.topic_core_points.get(topic_title, 0)
        is_required = st.session_state.selected_topic_data.get("required", False)
        
        # Topic is completed if it's earned at least as many points as core questions are worth
        if is_required and current_points < core_points and new_points >= core_points:
            # This core topic just became completed
            st.session_state.completed_topics_count += 1
        
        print(f"Updated points for {topic_title}: {new_points}/{st.session_state.topic_core_points.get(topic_title, 0)} (core) - {st.session_state.topic_total_points.get(topic_title, 100)} (total)")
        
        # Fix: Use st.session_state.core_topics instead of core_topics
        if "core_topics" in st.session_state:
            print(f"Completed core topics: {st.session_state.completed_topics_count}/{len(st.session_state.core_topics)}")
        else:
            print(f"Completed core topics: {st.session_state.completed_topics_count}/unknown")



# Initialize page state if not already set
if "current_page" not in st.session_state:
    st.session_state.current_page = "welcome"

# Function to display the main chat page (existing functionality)
def main_chat_page():
    youtube_url = "https://www.youtube.com/watch?v=nKW8Ndu7Mjw"
    
    # Create a dictionary mapping topics to their timestamps
    topics = []
    topic_timestamps = {}
    topic_core_points = {}
    topic_total_points = {}
    core_topics = []  # This variable is local to main_chat_page

    for i in all_topics["topics"]:
        title = i["title"]
        start_time = i["start_timestamp"]
        is_required = i.get("required", False)
        
        topics.append(title)
        topic_timestamps[title] = start_time
        
        # Calculate core and total points for each topic
        core_points, total_points = calculate_total_points(i)
        topic_core_points[title] = core_points
        topic_total_points[title] = total_points
        
        if is_required:
            core_topics.append(title)

    # Store core_topics in session state so it's available in update_topic_points
    st.session_state.core_topics = core_topics
    
    # Initialize topic progress if not in session state
    if "topic_progress" not in st.session_state:
        st.session_state.topic_progress = {topic: 0 for topic in topics}

    # Initialize topic points tracking
    if "topic_points" not in st.session_state:
        st.session_state.topic_points = {topic: 0 for topic in topics}

    # Store points for reference
    if "topic_core_points" not in st.session_state:
        st.session_state.topic_core_points = topic_core_points
        
    if "topic_total_points" not in st.session_state:
        st.session_state.topic_total_points = topic_total_points

    # Initialize selected topic data if not in session state
    if "selected_topic_data" not in st.session_state:
        st.session_state.selected_topic_data = None
        # Auto-select the first topic when page loads if no topic is selected
        if len(all_topics.get("topics", [])) > 0:
            first_topic = all_topics["topics"][0]
            
            # Get end timestamp with a default value (next topic's start time or None)
            end_timestamp = first_topic.get("end_timestamp")
            if end_timestamp is None and len(all_topics["topics"]) > 1:
                # If no end timestamp and there's a next topic, use next topic's start time
                end_timestamp = all_topics["topics"][1].get("start_timestamp")
            
            # Extract transcript for first topic
            transcript_text = extract_transcript(
                "sample-data/transcript.txt", 
                first_topic["start_timestamp"], 
                end_timestamp
            )
            
            # Store all relevant topic data including title, objectives, timestamps, and content
            st.session_state.selected_topic_data = {
                "title": first_topic["title"],
                "required": first_topic.get("required", False),
                "learning_objectives": first_topic.get("learning_objectives", []),
                "summary": first_topic.get("summary", ""),  # Add support for summary field
                "start_timestamp": first_topic.get("start_timestamp", ""),
                "end_timestamp": first_topic.get("end_timestamp", ""),
                "detailed_content": first_topic.get("detailed_content", []),
                "questions": first_topic.get("questions", []),
                "transcript": transcript_text
            }

    # Initialize discussion prompt if not in session state
    if "discussion_prompt" not in st.session_state:
        st.session_state.discussion_prompt = get_discussion_prompt()

    # Add custom CSS to make sidebar narrower and main content area wider
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            min-width: 35%;
            max-width: 35%;
        }
        .main .block-container {
            max-width: 70%;
            padding-top: 3rem;
            padding-right: 1rem;
            padding-left: 1rem;
            padding-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialize message count if not already in session state
    if "message_count" not in st.session_state:
        st.session_state.message_count = 0

    # Initialize question count if not already in session state
    if "question_count" not in st.session_state:
        st.session_state.question_count = 0

    # Initialize correct answers count
    if "correct_answers_count" not in st.session_state:
        st.session_state.correct_answers_count = 0

    # Initialize completed topics count
    if "completed_topics_count" not in st.session_state:
        st.session_state.completed_topics_count = 0

    # Initialize selected timestamp if not in session_state
    if "selected_timestamp" not in st.session_state:
        st.session_state.selected_timestamp = 0

    # Initialize question bank visibility state
    if "show_question_bank" not in st.session_state:
        st.session_state.show_question_bank = False

    # Add navigation buttons at the top of the page in a row
    top_col1, top_col2, top_col3, top_col5 = st.columns([1, 1, 1, 1])
    
    with top_col3:
        if st.button("← Home", key="return_home button"):
            st.session_state.current_page = "welcome"
            st.rerun()
            
    with top_col2:
        # Add button to toggle Question Bank visibility
        if st.button("📚 Question Bank", key="toggle_question_bank"):
            st.session_state.show_question_bank = True
            st.rerun()
            
    with top_col1:
        # Add button to return to chat view
        if st.button("💬 Chat", key="toggle_chat"):
            st.session_state.show_question_bank = False
            st.rerun()

    # Add sidebar with metrics and progress - use the imported function
    from sidebar import render_sidebar
    render_sidebar(all_topics, topic_timestamps, core_topics, youtube_url, extract_transcript, get_discussion_prompt)

    def start_chat():
        st.session_state.current_page = "chat_page"
        # Clear existing messages
        st.session_state.messages = []
        
        # Reset message count
        st.session_state.message_count = 0
        
        # Add system message with the discussion prompt
        system_message = st.session_state.discussion_prompt
        msg = [
            ("system", system_message),
            ("user", "Let's discuss this topic.")
        ]
        response = llm_service.send_message(msg)

        st.session_state.messages.append({"role": "system", "content": system_message})
        st.session_state.messages.append({"role": "user", "content": "Let's discuss this topic."})
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Check if Question Bank should be shown
    if st.session_state.show_question_bank:
        # Call the extracted show_question_bank function
        close_question_bank = show_question_bank(all_topics)
        
        # If the function returns False, close the question bank
        if close_question_bank is False:
            st.session_state.show_question_bank = False
            st.rerun()
    else:
        # Only show the topic info and chat when not in Question Bank mode
        topic_title = st.session_state.selected_topic_data.get("title", "No Topic Selected")
        timestamp = st.session_state.selected_topic_data.get("start_timestamp", "00:00")
        
        # Create a row with topic title and play button
        st.subheader(f"Topic: {topic_title}")
            
        # Display topic info in tabs directly instead of using an expander
        if st.session_state.selected_topic_data:
            # Create tabs for different content - added a new Questions tab
            overview_tab, transcript_tab, questions_tab = st.tabs(["Overview", "Transcript", "Questions"])
            
            with overview_tab:
                # Display topic overview information
                start = st.session_state.selected_topic_data.get("start_timestamp", "")
                end = st.session_state.selected_topic_data.get("end_timestamp", "")
                st.write(f"Timestamp: {start} - {end}")
                
                # Show detailed_summary



                # Add a button to play the video at the topic's timestamp
                if st.button("▶️ View Video", key="play_video_btn"):
                    # Set timestamp and autoplay flag
                    st.session_state.clicked_timestamp = True
                    parts = timestamp.split(":")
                    if len(parts) == 2:
                        minutes = int(parts[0])
                        seconds = int(parts[1])
                        t = minutes * 60 + seconds
                    else:
                        t = int(timestamp)
                    st.session_state.selected_timestamp = t
                    st.rerun()  # Refresh to start video
                
                if st.session_state.selected_topic_data.get("summary"):
                    st.markdown("### Topic Summary")
                    # Display summary in info box
                    st.info(st.session_state.selected_topic_data.get("summary"))
                
                if st.session_state.selected_topic_data.get("detailed_content"):
                    st.markdown("### Detailed Content")
                    for content_item in st.session_state.selected_topic_data.get("detailed_content", []):
                        timestamp = content_item.get("timestamp", "")
                        content = content_item.get("content", "")
                        st.write(f"**({timestamp})** {content}")
            
            with transcript_tab:
                # Display transcript
                if "transcript" in st.session_state.selected_topic_data:
                    st.markdown("### Transcript")
                    st.text_area("Transcript", st.session_state.selected_topic_data["transcript"], 
                                height=300, key="transcript_text", disabled=True, label_visibility="collapsed")
            
            # Added new Questions tab with two-column layout - without any expanders
            with questions_tab:
                # Display questions - handling the new structure
                if st.session_state.selected_topic_data.get("questions"):
                    st.markdown("### Topic Questions")
                    questions = st.session_state.selected_topic_data.get("questions", [])
                    
                    # Group questions by nature for better organization
                    question_by_nature = {}
                    for q in questions:
                        nature = q.get("question_nature", "Other")
                        if nature not in question_by_nature:
                            question_by_nature[nature] = []
                        question_by_nature[nature].append(q)
                    
                    # Display questions by nature directly without expanders
                    for nature, q_list in question_by_nature.items():
                        st.markdown(f"## {nature.title()} Questions ({len(q_list)})")
                        
                        for idx, q in enumerate(q_list):
                            # Create two columns for question and answer
                            q_col, a_col = st.columns([2, 3])
                            
                            with q_col:
                                # Add badge to show if question is required
                                required_badge = "🔴 Required" if q.get("required", False) else "⚪ Optional"
                                st.markdown(f"**Q{idx+1}: {q.get('question')}** <span style='color: {'red' if q.get('required', False) else 'gray'}; font-size: 0.8em;'>{required_badge}</span>", unsafe_allow_html=True)
                                
                                # Display MCQ options if question is MCQ type
                                if q.get("type") == "mcq":
                                    options = q.get("options", [])
                                    correct_answer = q.get("correct_answer", "")
                                    st.markdown("**Options:**")
                                    for i, option in enumerate(options):
                                        is_correct = option == correct_answer
                                        # Use a checkmark for the correct answer
                                        option_marker = "✅" if is_correct else f"{i+1}."
                                        st.markdown(f"{option_marker} {option}")
                            
                            with a_col:
                                
                                # Handle different answer formats based on question type
                                if q.get("type") == "mcq":
                                    st.markdown(f"**Correct Answer:** {q.get('correct_answer', '')}")
                                    if q.get("explanation"):
                                        st.markdown(f"**Explanation:** {q.get('explanation')}")
                                elif q.get("type") == "short_question":
                                    # Properly handle short_question answers
                                    if isinstance(q.get("answer"), list):
                                        st.markdown("**Grading Criteria:**")
                                        for criterion in q.get("answer", []):
                                            st.markdown(f"- {criterion.get('criteria', '')}: {criterion.get('points', 0)} points")
                                    else:
                                        st.markdown(f"**Answer:** {q.get('answer', '')}")
                                elif isinstance(q.get("answer"), list):
                                    # Ensure list-type answers are displayed as grading criteria
                                    st.markdown("**Grading Criteria:**")
                                    for criterion in q.get("answer", []):
                                        st.markdown(f"- {criterion.get('criteria', '')}: {criterion.get('points', 0)} points")
                                else:
                                    # Handle any other formats
                                    st.markdown(f"**Answer:** {q.get('answer', '')}")
                                
                                # Always display hints for all question types
                                if q.get("hints"):
                                    st.markdown("**Hints:**")
                                    for i, hint in enumerate(q.get("hints", [])):
                                        st.markdown(f"- **Hint {i+1}:** {hint}")
                                
                                # Display reference texts if available
                                if q.get("reference_text"):
                                    st.markdown("**Reference Text:**")
                                    for ref in q.get("reference_text", []):
                                        st.markdown(f"- **({ref.get('timestamp', '')})** {ref.get('text', '')}")

                        # Add extra spacing between question categories
                        if nature != list(question_by_nature.keys())[-1]:
                            st.markdown("<br><br>", unsafe_allow_html=True)
                else:
                    st.info("No questions available for this topic.")

        # Create discussion interface - MOVED THIS SECTION TO INSIDE THE OVERVIEW TAB
        with overview_tab:
            # Display chat interface after the content
            st.markdown("### Discussion")
            
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            with col1:
                if "messages" not in st.session_state or len(st.session_state.messages) == 0:
                    start_button = st.button("Start Chat", key="start_discussion_btn", on_click=start_chat)
                else:
                    start_button = st.button("Restart Chat", key="continue_discussion_btn", on_click=start_chat)

            with col2:
                if st.session_state.current_page == "chat_page" and ("messages" not in st.session_state or len(st.session_state.messages) > 0):
                    start_exercise_button = st.button("Start Practice", key="start_exercise_btn", on_click=start_exercise)

            with col3: 
                start_mcq_button = st.button("Start MCQ", key="start_mcq_btn", on_click=start_mcq_panel)
            
            # Show chat messages only in the overview tab
            if st.session_state.current_page == "chat_page" and "messages" in st.session_state and len(st.session_state.messages) > 0:
                # Display chat messages from history on app rerun
                for message in st.session_state.messages:
                    if message["role"] != "system": #hide the system message in chat
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])

                user_input = st.chat_input("Input your message here...")
                
                if user_input:
                    # Add user message to chat history
                    st.session_state.messages.append({"role": "user", "content": user_input})
                    # Update message count when user sends a message
                    st.session_state.message_count += 1
                    
                    with st.chat_message("user"):
                        st.markdown(user_input)        
                    formatted_messages = []
                    for msg in st.session_state.messages:
                        if msg["role"] == "user":
                            formatted_messages.append(("user", msg["content"]))
                        elif msg["role"] == "assistant":
                            formatted_messages.append(("assistant", msg["content"]))
                        elif msg["role"] == "system":
                            formatted_messages.append(("system", msg["content"]))
                                
                    response = llm_service.send_message(formatted_messages)

                    st.session_state.messages.append({"role": "assistant", "content": response})
                    with st.chat_message("assistant"):
                        st.markdown(response)
                    
                    update_topic_points(st.session_state.selected_topic_data.get("title", ""))
                    st.rerun()

        # Handle the start exercise button click (KEEP THIS OUTSIDE THE TAB)
        if "start_exercise_clicked" in st.session_state:
            user_input = "Let's start the practice session."
            st.session_state.messages.append({"role": "user", "content": user_input})

            formatted_messages = []
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    formatted_messages.append(("user", msg["content"]))
                elif msg["role"] == "assistant":
                    formatted_messages.append(("assistant", msg["content"]))
                elif msg["role"] == "system":
                    formatted_messages.append(("system", msg["content"]))
                    
            response = llm_service.send_message(formatted_messages)
            st.session_state.messages.append({"role": "assistant", "content": response})
            # remove the key from session state
            del st.session_state.start_exercise_clicked
            st.rerun()

        # Display MCQ quiz if in MCQ mode
        if st.session_state.current_page == "mcq_quiz":
            # Display MCQ quiz
            display_mcq_quiz(all_topics)

# Main code - determine which page to show
if st.session_state.current_page == "welcome":
    welcome_page()
else:
    main_chat_page()