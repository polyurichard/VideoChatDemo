import streamlit as st
import json


def get_topics():
    # get topics from sample-data/topics.json
    with open("sample-data/topics_with_q.json") as f:
        topics = json.load(f)
    return topics

# Function to store selected topic data
def store_topic_data(topic_title, extract_transcript, get_discussion_prompt):
    all_topics = get_topics()
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
                "summary": topic.get("summary", ""),  # Add support for summary field
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

# Function to update selected timestamp and select the topic
def set_timestamp_and_topic(timestamp, topic_title, extract_transcript, get_discussion_prompt):
    # Convert timestamp in mm:ss to seconds
    # st.session_state.clicked_timestamp = True
    parts = timestamp.split(":")
    if len(parts) == 2:
        minutes = int(parts[0])
        seconds = int(parts[1])
        t = minutes * 60 + seconds
    elif len(parts) == 1:
        t = int(parts[0])
    st.session_state.selected_timestamp = t
    
    # If a topic title is provided, also select that topic
    if topic_title:
        store_topic_data(topic_title, extract_transcript, get_discussion_prompt)

def render_sidebar(all_topics, topic_timestamps, core_topics, youtube_url,extract_transcript, get_discussion_prompt):
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
            # Create clickable topic table - removed the Start column
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                st.subheader("Topics")
            
            with col2:
                st.subheader("Status")
                
            with col3:
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
                
                # Create a row for each topic - removed the Start column
                cols = st.columns([4, 1, 1])
                
                # First column (now topic button) - combined the functionality of previous columns 1 and 2
                with cols[0]:
                    topic_button = st.button(
                        topic,
                        key=f"topic_{topic}",
                        help=f"Click to select {topic} and set timestamp to {timestamp}",
                        on_click=set_timestamp_and_topic,
                        args=(timestamp, topic, extract_transcript, get_discussion_prompt)
                    )
                
                # Second column (previously third): Required/Optional status
                with cols[1]:
                    status_label = "🔷 Core" if is_required else "◻️ Optional"
                    st.write(status_label)
                
                # Third column (previously fourth): Points progress
                with cols[2]:
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