import streamlit as st
import time
from llm import LLMService
import json
import re

discuss_prompt = ""


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
        transcript_text = extract_transcript(
            "sample-data/transcript.txt", 
            first_topic["start_timestamp"], 
            first_topic["end_timestamp"]
        )
        
        selected_topic_data = {
            "title": first_topic["title"],
            "learning_objectives": first_topic.get("learning_objectives", []),
            "start_timestamp": first_topic.get("start_timestamp", ""),
            "end_timestamp": first_topic.get("end_timestamp", ""),
            "detailed_content": first_topic.get("detailed_content", []),
            "questions": first_topic.get("questions", []),
            "discussion_items": first_topic.get("discussion_items", []),
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
    """Calculate the total available points for a given topic."""
    total_points = 0
    
    # Add points from questions
    if "questions" in topic_data:
        for question in topic_data["questions"]:
            if "point_value" in question:
                total_points += question["point_value"]
    
    # Add points from discussion items
    if "discussion_items" in topic_data:
        for item in topic_data["discussion_items"]:
            if "point_value" in item:
                total_points += item["point_value"]
    
    return total_points

def update_topic_points(topic_title):
    """Update the points earned for a topic based on LLM evaluation of answers."""
    # Ensure we have enough messages for evaluation (at least the last user question and AI response)
    if len(st.session_state.messages) < 3:
        return
    
    # Get the last user question and AI response
    last_two_messages = st.session_state.messages[-2:] # User message and AI response
    #print("---- Last two messages for evaluation:")  # Debugging line
    #print(last_two_messages)  # Debugging line
    
    # Format the conversation for the LLM evaluation in a plain text format
    # convert last_two_messages from a list of dicts to a formatted string
    #str_result =  json.dumps(last_two_messages, indent=2)

    formatted_conversation = f"User: {last_two_messages[0]['content']}\nAssistant: {last_two_messages[1]['content']}"
    
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
    
    # Extract the points from the LLM's response (expecting just a number)
    try:
        # Try to parse the response as an integer
        points_earned = int(evaluation.strip())

        print(f"Points earned from LLM evaluation: {points_earned}")
    except ValueError:
        # If parsing fails, default to 0 points
        print(f"Could not parse points from LLM response: {evaluation}")
        points_earned = 0
    
    # Update the points in the session state
    if "topic_points" in st.session_state:
        current_points = st.session_state.topic_points.get(topic_title, 0)
        st.session_state.topic_points[topic_title] = min(
            current_points + points_earned, 
            st.session_state.topic_total_points.get(topic_title, 100)  # Cap at max points
        )
        print(f"Updated points for {topic_title}: {st.session_state.topic_points[topic_title]}/{st.session_state.topic_total_points.get(topic_title, 100)}")



youtube_url = "https://www.youtube.com/watch?v=nKW8Ndu7Mjw"
all_topics = get_topics()

# Create a dictionary mapping topics to their timestamps
topics = []
topic_timestamps = {}
topic_total_points = {}

for i in all_topics["topics"]:
    title = i["title"]
    start_time = i["start_timestamp"]
    topics.append(title)
    topic_timestamps[title] = start_time
    # Calculate total points for each topic
    topic_total_points[title] = calculate_total_points(i)

# Initialize topic progress if not in session state
if "topic_progress" not in st.session_state:
    st.session_state.topic_progress = {topic: 0 for topic in topics}

# Initialize topic points tracking
if "topic_points" not in st.session_state:
    st.session_state.topic_points = {topic: 0 for topic in topics}

# Store total points for reference
if "topic_total_points" not in st.session_state:
    st.session_state.topic_total_points = topic_total_points

# Initialize selected topic data if not in session state
if "selected_topic_data" not in st.session_state:
    st.session_state.selected_topic_data = None
    # Auto-select the first topic when page loads if no topic is selected
    if len(all_topics.get("topics", [])) > 0:
        first_topic = all_topics["topics"][0]
        # Extract transcript for first topic
        transcript_text = extract_transcript(
            "sample-data/transcript.txt", 
            first_topic["start_timestamp"], 
            first_topic["end_timestamp"]
        )
        
        # Store all relevant topic data including title, objectives, timestamps, and content
        st.session_state.selected_topic_data = {
            "title": first_topic["title"],
            "learning_objectives": first_topic.get("learning_objectives", []),
            "start_timestamp": first_topic.get("start_timestamp", ""),
            "end_timestamp": first_topic.get("end_timestamp", ""),
            "detailed_content": first_topic.get("detailed_content", []),
            "questions": first_topic.get("questions", []),
            "discussion_items": first_topic.get("discussion_items", []),
            "transcript": transcript_text
        }

# Initialize discussion prompt if not in session state
if "discussion_prompt" not in st.session_state:
    st.session_state.discussion_prompt = get_discussion_prompt()

# Add custom CSS to make sidebar wider (40% of screen width)
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        min-width: 40%;
        max-width: 40%;
    }
</style>
""", unsafe_allow_html=True)


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

# Initialize message count if not already in session state
if "message_count" not in st.session_state:
    st.session_state.message_count = 0

# Initialize selected timestamp if not in session state
if "selected_timestamp" not in st.session_state:
    st.session_state.selected_timestamp = 0

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
    # Find the topic data in all_topics
    for topic in all_topics["topics"]:
        if topic["title"] == topic_title:
            # Extract transcript for this topic
            transcript_text = extract_transcript(
                "sample-data/transcript.txt", 
                topic["start_timestamp"], 
                topic["end_timestamp"]
            )
            
            # Store all relevant topic data including title, objectives, timestamps, and content
            st.session_state.selected_topic_data = {
                "title": topic["title"],
                "learning_objectives": topic.get("learning_objectives", []),
                "start_timestamp": topic.get("start_timestamp", ""),
                "end_timestamp": topic.get("end_timestamp", ""),
                "detailed_content": topic.get("detailed_content", []),
                "questions": topic.get("questions", []),
                "discussion_items": topic.get("discussion_items", []),
                "transcript": transcript_text
            }
            
            # Generate discussion prompt for the selected topic
            st.session_state.discussion_prompt = get_discussion_prompt()
            
            # reset conversation history
            st.session_state.messages = []
            break

# Add sidebar with message count
with st.sidebar:
    st.metric("Messages Sent", st.session_state.message_count)
    
    # Topic Dashboard Panel (now collapsible with expander)
    with st.expander("Progress", expanded=True):
        # Create clickable topic table
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            st.subheader("Start")
        
        with col2:
            st.subheader("Topics")
        
        with col3:
            st.subheader("Progress")
          # Display each topic with progress and link in table rows
        for topic in topics:
            timestamp = topic_timestamps.get(topic, 0)
            points_earned = st.session_state.topic_points.get(topic, 0)
            total_points = st.session_state.topic_total_points.get(topic, 1)
            
            # Calculate progress as percentage of points earned
            progress_pct = int((points_earned / total_points) * 100) if total_points > 0 else 0
            st.session_state.topic_progress[topic] = progress_pct
            
            # Create a row for each topic
            cols = st.columns([1, 3, 1])
            
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
            
            # Third column: Points progress
            with cols[2]:
                # Show both points and emoji indicator
                points_earned = st.session_state.topic_points.get(topic, 0)
                total_points = st.session_state.topic_total_points.get(topic, 1)
                emoji_indicator = "✅" if points_earned >= 3 else "⏳"
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
    
# Display selected topic data at the top of the main content area
if st.session_state.selected_topic_data:
    with st.expander(f"Topic: {st.session_state.selected_topic_data['title']}", expanded=False):
        # Add tabs for different content, including a new "Discussion Prompt" tab
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Questions", "Discussion Items", "Transcript", "Discussion Prompt"])
        
        with tab1:
            # Display topic overview information
            st.subheader("Learning Objectives")
            for i, objective in enumerate(st.session_state.selected_topic_data.get("learning_objectives", [])):
                st.write(f"- {objective}")
                
            st.subheader("Time Range")
            start = st.session_state.selected_topic_data.get("start_timestamp", "")
            end = st.session_state.selected_topic_data.get("end_timestamp", "")
            st.write(f"From {start} to {end}")
            
            st.subheader("Detailed Content")
            for content_item in st.session_state.selected_topic_data.get("detailed_content", []):
                timestamp = content_item.get("timestamp", "")
                content = content_item.get("content", "")
                st.write(f"**({timestamp})** {content}")
        
        with tab2:
            # Display questions
            if st.session_state.selected_topic_data.get("questions"):
                for i, question in enumerate(st.session_state.selected_topic_data["questions"]):
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
                        
                        # Display radio buttons with correct answer pre-selected
                        st.radio(
                            f"Options for Q{i+1}", 
                            options, 
                            key=f"question_{i}",
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
                    
                    # Add separator between questions
                    st.markdown("---")
        
        with tab3:
            # Display discussion items
            if st.session_state.selected_topic_data.get("discussion_items"):
                for i, item in enumerate(st.session_state.selected_topic_data["discussion_items"]):
                    st.write(f"**Question {i+1}:** {item['question']}")
                    st.write(f"Points: {item['point_value']}")
                    
                    # Show sample answer automatically without toggle button
                    if "sample_answer" in item:
                        st.success(f"**Sample Answer:** {item['sample_answer']}")
                    
                    # Add hints directly without toggle button
                    if "hints" in item:
                        st.markdown("**Hints:**")
                        for hint in item["hints"]:
                            st.write(f"- {hint}")
                    
                    # Add separator between discussion items
                    st.markdown("---")
        with tab4:
            # Display transcript
            if "transcript" in st.session_state.selected_topic_data:
                st.markdown("### Transcript")
                st.text_area("Transcript", st.session_state.selected_topic_data["transcript"], 
                             height=300, key="transcript_text", disabled=True, label_visibility="collapsed")
        
        with tab5:            # Display the discussion prompt as plain text instead of markdown
            st.markdown("### Discussion Prompt")
            st.markdown("This is the prompt used by the AI to guide discussion about this topic:")
            
            # Using text_area to display the prompt as plain text
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
    print(f"Response from LLM: {response}")  # Debugging line
    
    st.session_state.messages.append({"role": "system", "content": system_message})
    st.session_state.messages.append({"role": "user", "content": "Let's discuss this topic."})
    st.session_state.messages.append({"role": "assistant", "content": response})
    


st.header("Topic: " + st.session_state.selected_topic_data.get("title", "No Topic Selected"))
start_button = st.button("Start Discussion", key="start_discussion_btn", on_click = start_chat)

# check if messages exist in session state
if "messages"  in st.session_state and st.session_state.messages != []:
    # Initialize chat history
    #if "messages" not in st.session_state:
    #    st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        if message["role"] != "system": #skip system message in chat display
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Create a container for input area with columns for input and button
    input_container = st.container()
    with input_container:
        col1, col2 = st.columns([5, 1])  # 5:1 ratio for input box to button
        
        with col1:
            # Accept user input
            prompt = st.chat_input("Input your message")
        
        with col2:            # Add a button to clear the chat history
            if st.button("Clear Chat", key="clear_chat_main"):
                st.session_state.messages = []
                st.session_state.message_count = 0
                st.session_state.topic_progress = {topic: 0 for topic in topics}
                st.session_state.topic_points = {topic: 0 for topic in topics}
                st.rerun()

    # Process user input 
    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Update message count for user message only
        st.session_state.message_count += 1
        
        # Display user message in chat message container
        #with st.chat_message("user"):
        #    st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            # Format messages for LLMService
            formatted_messages = []
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    formatted_messages.append(("user", msg["content"]))
                elif msg["role"] == "assistant":
                    formatted_messages.append(("assistant", msg["content"]))
                elif msg["role"] == "system":
                    formatted_messages.append(("system", msg["content"]))

            message_placeholder = st.empty()

            # Get response from LLM
            #print("formatted_messages:", formatted_messages)  # Debugging line
            response = llm_service.send_message(formatted_messages)

            # Display the complete response with markdown support
            message_placeholder.markdown(response)        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        update_topic_points(st.session_state.selected_topic_data.get("title", ""))
        # Update message count for assistant response

        # Update topic points based on interaction
        #current_topic = st.session_state.selected_topic_data.get("title", "")
        #if current_topic:
            # Add points for meaningful interaction (1 point per interaction)
        #    update_topic_points(current_topic)
        
        # Force a rerun to update the sidebar
        st.rerun()

def calculate_total_points(topic_data):
    """Calculate the total available points for a given topic."""
    total_points = 0
    
    # Add points from questions
    if "questions" in topic_data:
        for question in topic_data["questions"]:
            if "point_value" in question:
                total_points += question["point_value"]
    
    # Add points from discussion items
    if "discussion_items" in topic_data:
        for item in topic_data["discussion_items"]:
            if "point_value" in item:
                total_points += item["point_value"]
    
    return total_points

