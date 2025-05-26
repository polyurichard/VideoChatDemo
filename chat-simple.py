import streamlit as st
import time
from llm import LLMService
import json
import re

# Initialize LLM service
@st.cache_resource
def get_llm_service():
    return LLMService(
        config_path=".env",
        openai_api_version="2024-12-01-preview",
        azure_deployment="gpt-4o-mini",
        temperature=0,
    )

# Get LLM service instance
llm_service = get_llm_service()

# Initialize messages list if not in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# print("start page")

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
        
        selected_topic_data = {
            "title": first_topic["title"],
            "required": first_topic.get("required", False),
            "learning_objectives": first_topic.get("learning_objectives", []),
            "start_timestamp": first_topic.get("start_timestamp", ""),
            "end_timestamp": first_topic.get("end_timestamp", ""),
            "detailed_content": first_topic.get("detailed_content", []),
            "questions": first_topic.get("questions", []),
            "transcript": transcript_text
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

def get_topics():
    # get topics from sample-data/topics.json
    with open("sample-data/topics_with_q.json") as f:
        topics = json.load(f)
    return topics


def calculate_total_points(topic_data):
    """Calculate the points for a given topic.
    Returns a tuple of (core_points, total_points) where:
    - core_points: Sum of points for required questions
    - total_points: Sum of points for all questions (core + optional)
    """
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
        print(f"Completed core topics: {st.session_state.completed_topics_count}/{len(core_topics)}")



# Initialize page state if not already set
if "current_page" not in st.session_state:
    st.session_state.current_page = "welcome"

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

# Function to display the main chat page (existing functionality)
def main_chat_page():
    youtube_url = "https://www.youtube.com/watch?v=nKW8Ndu7Mjw"
    all_topics = get_topics()

    # Create a dictionary mapping topics to their timestamps
    topics = []
    topic_timestamps = {}
    topic_core_points = {}
    topic_total_points = {}
    core_topics = []

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
            max-width: 60%;
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

    # Add a "return to home" button at the top of the page
    if st.button("← Return to Home", key="return_home"):
        st.session_state.current_page = "welcome"
        st.rerun()

    # Function to update selected timestamp without rerun
    def set_timestamp(timestamp):
        # convert timestamp in mm:ss to seconds
        st.session_state.clicked_timestamp = True
        parts = timestamp.split(":")
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = int(parts[1])
            t = minutes * 60 + seconds
        elif len(parts) == 1:
            t = int(parts[0])
        st.session_state.selected_timestamp = t
        # Remove st.rerun() as it's a no-op in callbacks

    # Function to store selected topic data
    def store_topic_data(topic_title):
        # clear conversation history
        st.session_state.messages = []

        # Find the topic data in all_topics
        for i, topic in enumerate(all_topics["topics"]):
            if topic["title"] == topic_title:
                # Get end timestamp with a default value (next topic's start time or None)
                end_timestamp = topic.get("end_timestamp")
                if end_timestamp is None and i < len(all_topics["topics"]) - 1:
                    # If no end timestamp and there's a next topic, use next topic's start time
                    end_timestamp = all_topics["topics"][i+1].get("start_timestamp")
                
                # Extract transcript for this topic
                transcript_text = extract_transcript(
                    "sample-data/transcript.txt", 
                    topic["start_timestamp"], 
                    end_timestamp
                )
                
                # Store all relevant topic data including title, objectives, timestamps, and content
                st.session_state.selected_topic_data = {
                    "title": topic["title"],
                    "required": topic.get("required", False),
                    "learning_objectives": topic.get("learning_objectives", []),
                    "start_timestamp": topic.get("start_timestamp", ""),
                    "end_timestamp": topic.get("end_timestamp", ""),
                    "detailed_content": topic.get("detailed_content", []),
                    "questions": topic.get("questions", []),
                    "transcript": transcript_text
                }
                
                # Generate discussion prompt for the selected topic
                st.session_state.discussion_prompt = get_discussion_prompt()
                
                # reset conversation history
                st.session_state.messages = []
                break

    # Add sidebar with metrics and progress
    with st.sidebar:
        # Display all metrics in a single row with 4 columns
        metrics_cols = st.columns(4)
        with metrics_cols[0]:
            st.metric("Messages", st.session_state.message_count)
        with metrics_cols[1]:
            st.metric("Questions", st.session_state.question_count)
        with metrics_cols[2]:
            st.metric("Answers", st.session_state.correct_answers_count)
        with metrics_cols[3]:
            core_topics_count = len(core_topics)
            st.metric("Core Topics Completed", f"{st.session_state.completed_topics_count}/{core_topics_count}")
        
        # Topic Dashboard Panel (now collapsible with expander)
        with st.expander("Progress", expanded=True):
            # Create clickable topic table
            col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
            
            with col1:
                st.subheader("Start")
            
            with col2:
                st.subheader("Topics")
            
            with col3:
                st.subheader("Status")
                
            with col4:
                st.subheader("Progress")
              # Display each topic with progress and link in table rows
            for topic_idx, topic_data in enumerate(all_topics["topics"]):
                topic = topic_data["title"]
                is_required = topic_data.get("required", False)
                timestamp = topic_timestamps.get(topic, 0)
                points_earned = st.session_state.topic_points.get(topic, 0)
                core_points = st.session_state.topic_core_points.get(topic, 0)
                total_points = st.session_state.topic_total_points.get(topic, 1)
                
                # Calculate progress as percentage of points earned compared to core points
                if core_points > 0:
                    progress_pct = min(100, int((points_earned / core_points) * 100))
                else:
                    progress_pct = 100 if points_earned > 0 else 0
                    
                st.session_state.topic_progress[topic] = progress_pct
                
                # Create a row for each topic
                cols = st.columns([1, 3, 1, 1])
                
                # First column: Start button with emoji
                with cols[0]:
                    start_button = st.button(
                        "▶️",
                        key=f"start_{topic}",
                        help=f"Start learning this topic",
                        on_click=store_topic_data,
                        args=(topic,)
                    )
                
                # Second column: Topic button
                with cols[1]:
                    topic_button = st.button(
                        topic,
                        key=f"topic_{topic}",
                        help=f"Click to jump to {topic} at {timestamp} seconds",
                        on_click=set_timestamp,
                        args=(timestamp,)
                    )
                
                # Third column: Required/Optional status
                with cols[2]:
                    status_label = "🔷 Core" if is_required else "◻️ Optional"
                    st.write(status_label)
                
                # Fourth column: Points progress
                with cols[3]:
                    # Show both points and emoji indicator
                    points_earned = st.session_state.topic_points.get(topic, 0)
                    core_points = st.session_state.topic_core_points.get(topic, 0)
                    
                    # A topic is completed when all core questions are answered (points >= core_points)
                    completed = points_earned >= core_points if core_points > 0 else points_earned > 0
                    emoji_indicator = "✅" if completed else "⏳"
                    
                    # Display points as: earned/core (total)
                    if core_points < total_points:
                        st.write(f"{points_earned}/{core_points} {emoji_indicator}")
                    else:
                        # If all questions are core, just show as earned/total
                        st.write(f"{points_earned}/{total_points} {emoji_indicator}")
        
        # Add YouTube video with timestamp
        if "selected_timestamp" in st.session_state:
            # check if clicked_timestamp is set
            if "clicked_timestamp"  in st.session_state and st.session_state.clicked_timestamp:
                # Use the selected timestamp from session state
                st.video(youtube_url, start_time=st.session_state.selected_timestamp, autoplay=True)
            else:
                st.video(youtube_url, start_time=st.session_state.selected_timestamp, autoplay=False)
            
        else:
            st.video(youtube_url)
        st.session_state.clicked_timestamp = False  # Reset clicked state after video load

    def display_topic_details():
            
        # Display selected topic data at the top of the main content area
        if st.session_state.selected_topic_data:
            required_status = "Core" if st.session_state.selected_topic_data.get("required", False) else "Optional"
            with st.expander(f"Topic: {st.session_state.selected_topic_data['title']} ({required_status})", expanded=False):
                # Add tabs for different content
                tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Questions", "Transcript", "Discussion Prompt"])
                
                with tab1:
                    start = st.session_state.selected_topic_data.get("start_timestamp", "")
                    end = st.session_state.selected_topic_data.get("end_timestamp", "")
                    if start != "" :
                        st.write(f"Start Timestamp: {start}")
                    if end != "":
                        st.write(f"End Timestamp: {end}")
                                        
                    # Display topic overview information
                    st.subheader("Learning Objectives")
                    for i, objective in enumerate(st.session_state.selected_topic_data.get("learning_objectives", [])):
                        st.write(f"- {objective}")
                        

                    st.subheader("Detailed Content")
                    for content_item in st.session_state.selected_topic_data.get("detailed_content", []):
                        timestamp = content_item.get("timestamp", "")
                        content = content_item.get("content", "")
                        st.write(f"**({timestamp})** {content}")
                
                with tab2:
                    # Create two columns for Required and Optional questions
                    required_questions = [q for q in st.session_state.selected_topic_data.get("questions", []) if q.get("required", False)]
                    optional_questions = [q for q in st.session_state.selected_topic_data.get("questions", []) if not q.get("required", False)]
                    
                    # Display required questions first with a header
                    if required_questions:
                        st.subheader("Core Questions")
                        for i, question in enumerate(required_questions):
                            q_type = question.get("type", "Unknown")
                            st.write(f"**{q_type.capitalize()} Question {i+1}:** {question['question']}")
                            st.write(f"Points: {question['point_value']}")
                            
                            # If it's a multiple-choice question, show options with correct answer selected by default
                            if q_type == "mcq" and "options" in question:
                                options = question["options"]
                                # Get the index of correct answer in options list
                                default_index = 0
                                if "correct_answer" in question:
                                    try:
                                        default_index = options.index(question["correct_answer"])
                                    except ValueError:
                                        default_index = 0
                                
                                # Display radio buttons with correct answer pre-selected - MOVED INSIDE THE IF BLOCK
                                st.radio(
                                    f"Options for Q{i+1}", 
                                    options, 
                                    key=f"req_question_{i}",
                                    index=default_index  # Pre-select correct answer
                                )
                                
                                # Show the correct answer and explanation automatically
                                if "correct_answer" in question:
                                    st.success(f"**Correct Answer:** {question['correct_answer']}")
                                    if "explanation" in question:
                                        st.info(f"**Explanation:** {question['explanation']}")
                            else:
                                # For non-MCQ questions, show sample answer automatically
                                if "sample_answer" in question:
                                    st.success(f"**Sample Answer:** {question['sample_answer']}")
                                    if "explanation" in question:
                                        st.info(f"**Explanation:** {question['explanation']}")
                            
                            # Add hints directly without toggle button
                            if "hints" in question:
                                st.markdown("**Hints:**")
                                for hint in question["hints"]:
                                    st.write(f"- {hint}")
                            
                            # Add reference timestamp if available
                            if "reference_timestamp" in question:
                                st.write(f"**Reference:** {question['reference_timestamp']}")
                                
                            # Add separator between questions
                            st.markdown("---")

                    # Then display optional questions
                    if optional_questions:
                        st.subheader("Optional Questions")
                        for i, question in enumerate(optional_questions):
                            q_type = question.get("type", "Unknown")
                            st.write(f"**{q_type.capitalize()} Question {i+1}:** {question['question']}")
                            st.write(f"Points: {question['point_value']}")
                            
                            # Same display logic for optional questions
                            if q_type == "mcq" and "options" in question:
                                options = question["options"]
                                default_index = 0
                                if "correct_answer" in question:
                                    try:
                                        default_index = options.index(question["correct_answer"])
                                    except ValueError:
                                        default_index = 0
                                
                                # Display radio buttons with correct answer pre-selected
                                st.radio(
                                    f"Options for Q{i+1}", 
                                    options, 
                                    key=f"opt_question_{i}",
                                    index=default_index
                                )
                                
                                # Show the correct answer and explanation automatically
                                if "correct_answer" in question:
                                    st.success(f"**Correct Answer:** {question['correct_answer']}")
                                    if "explanation" in question:
                                        st.info(f"**Explanation:** {question['explanation']}")
                            else:
                                # For non-MCQ questions, show sample answer automatically
                                if "sample_answer" in question:
                                    st.success(f"**Sample Answer:** {question['sample_answer']}")
                                    if "explanation" in question:
                                        st.info(f"**Explanation:** {question['explanation']}")
                            
                            # Add hints directly without toggle button
                            if "hints" in question:
                                st.markdown("**Hints:**")
                                for hint in question["hints"]:
                                    st.write(f"- {hint}")
                            
                            # Add reference timestamp if available
                            if "reference_timestamp" in question:
                                st.write(f"**Reference:** {question['reference_timestamp']}")
                                
                            # Add separator between questions
                            st.markdown("---")
                
                with tab3:
                    # Display transcript
                    if "transcript" in st.session_state.selected_topic_data:
                        st.markdown("### Transcript")
                        st.text_area("Transcript", st.session_state.selected_topic_data["transcript"], 
                                    height=300, key="transcript_text", disabled=True, label_visibility="collapsed")
                
                with tab4:
                    # Display the discussion prompt as plain text
                    st.markdown("### Discussion Prompt")
                    st.markdown("This is the prompt used by the AI to guide discussion about this topic:")
                    
                    st.text_area("Discussion Prompt", st.session_state.discussion_prompt, 
                                height=400, key="discussion_prompt_text", disabled=True, label_visibility="collapsed")    

    # Add a button to start a discussion with this prompt
    # Print current topic

    def start_chat():
        # Clear existing messages
        st.session_state.messages = []
        
        # Reset message count
        st.session_state.message_count = 0
        
        # Add system message with the discussion prompt
        system_message =  st.session_state.discussion_prompt
        msg = [
            ("system",  system_message),
            ("user", "Let's discuss this topic.")
        ]
        response = llm_service.send_message(msg)
        #print(f"Response from LLM: {response}")  # Debugging line


        st.session_state.messages.append({"role": "system", "content": system_message})
        st.session_state.messages.append({"role": "user", "content": "Let's discuss this topic."})
        st.session_state.messages.append({"role": "assistant", "content": response})
        

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
        
        # Call LLM to evaluate the conversation and determine points
        evaluation = llm_service.send_message([("user", score_prompt)])
        print("---- LLM evaluation prompt--:")  # Debugging line
        print(score_prompt)  # Debugging line
        print("--- Result ---")  # Debugging line
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
            print(f"Completed core topics: {st.session_state.completed_topics_count}/{len(core_topics)}")


    def start_exercise():
        st.session_state.start_exercise_clicked = True
        print("Start exercise button clicked")  # Debugging line
        



    # handle the start exercise button click
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
        # response = " mock result from start exercise"
        st.session_state.messages.append({"role": "assistant", "content": response})
        # remove the key from session state
        del st.session_state.start_exercise_clicked



    st.subheader("Topic: " + st.session_state.selected_topic_data.get("title", "No Topic Selected") + 
                 (" (Core)" if st.session_state.selected_topic_data.get("required", False) else " (Optional)"))
    display_topic_details()
    start_button = st.button("Start Discussion", key="start_discussion_btn", on_click = start_chat)


    if "messages" in st.session_state and len(st.session_state.messages) > 0:
        
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
            # response = "Mock 2"

            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)
            
            update_topic_points(st.session_state.selected_topic_data.get("title", ""))
            st.rerun()


        start_exercise = st.button("Start Practice", key="start_exercise_btn", on_click=start_exercise)

# Main code - determine which page to show
if st.session_state.current_page == "welcome":
    welcome_page()
else:
    main_chat_page()