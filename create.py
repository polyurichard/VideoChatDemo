import streamlit as st
import pandas as pd
import json
import os
import re
from io import StringIO
import tempfile
import uuid

# Mock function to replace API calls for transcript/text extraction
def extract_text_from_url(url):
    """Mock function to extract text from URL"""
    if "youtube" in url.lower():
        # read transcript from ./sample-data/transcript.txt
        with open("./sample-data/transcript.txt", "r") as f:
            transcript =  f.read()
        return transcript
    
    else:
        return """This is mock text from a webpage.
        The article discusses climate change impacts.
        Global temperatures are rising at an alarming rate.
        Polar ice caps are melting, causing sea levels to rise.
        Extreme weather events are becoming more frequent.
        Carbon dioxide emissions continue to increase globally.
        Renewable energy adoption is growing but not fast enough.
        Conservation efforts are crucial for ecosystem preservation.
        International cooperation is needed to address climate challenges.
        Individual actions can collectively make a difference."""

def extract_text_from_pdf(pdf_file):
    """Mock function to extract text from PDF"""
    return """This is mock text extracted from a PDF file.
    The document explores quantum computing fundamentals.
    Qubits can exist in multiple states simultaneously due to superposition.
    Quantum entanglement allows particles to be correlated across distances.
    Quantum algorithms can solve certain problems exponentially faster than classical computers.
    Quantum error correction is a major challenge in building reliable quantum computers.
    Decoherence occurs when quantum systems interact with their environment.
    Quantum supremacy refers to quantum computers outperforming classical ones.
    Major tech companies are investing heavily in quantum computing research.
    Practical applications include cryptography, drug discovery, and optimization problems."""

# Mock function to generate questions from text
def generate_questions(text, num_questions=10):
    """Mock function to generate questions from text"""
    # Create a list of mock questions based on the text content
    questions = []
    
    if "artificial intelligence" in text.lower() or "machine learning" in text.lower():
        questions = [
            {"question": "What is the difference between supervised and unsupervised learning?", 
             "answer": "Supervised learning uses labeled data while unsupervised learning finds patterns without labels.",
             "type": "open"},
            {"question": "Explain how deep learning differs from traditional machine learning.", 
             "answer": "Deep learning uses neural networks with many layers to learn hierarchical representations of data.",
             "type": "open"},
            {"question": "What ethical concerns arise from AI implementation?", 
             "answer": "Concerns include bias, privacy, job displacement, security, and autonomous decision-making.",
             "type": "open"},
            {"question": "What are the main applications of natural language processing?", 
             "answer": "Applications include machine translation, sentiment analysis, chatbots, and information extraction.",
             "type": "open"},
            {"question": "How does reinforcement learning work?", 
             "answer": "Agents learn optimal behaviors through trial and error by receiving rewards or penalties.",
             "type": "open"},
            {"question": "Which of the following is NOT a type of machine learning?", 
             "options": ["Supervised learning", "Unsupervised learning", "Differential learning", "Reinforcement learning"],
             "answer": "Differential learning",
             "type": "mcq"},
            {"question": "What is the primary goal of computer vision?", 
             "options": ["Creating digital art", "Enabling computers to understand visual information", "Improving display resolution", "Tracking user eye movements"],
             "answer": "Enabling computers to understand visual information",
             "type": "mcq"},
            {"question": "Which technology is most associated with understanding human language?", 
             "options": ["Computer vision", "Natural language processing", "Genetic algorithms", "Robotic process automation"],
             "answer": "Natural language processing",
             "type": "mcq"},
            {"question": "What is bias in AI systems?", 
             "answer": "Systematic errors that create unfair outcomes for certain groups, often reflecting historical or societal prejudices.",
             "type": "open"},
            {"question": "Describe a real-world application of deep learning.", 
             "answer": "Examples include image recognition, speech recognition, recommendation systems, or autonomous vehicles.",
             "type": "open"},
        ]
    elif "climate change" in text.lower() or "global temperatures" in text.lower():
        questions = [
            {"question": "What are the main causes of climate change?", 
             "answer": "Greenhouse gas emissions, deforestation, industrial processes, and agricultural practices.",
             "type": "open"},
            {"question": "Explain the relationship between carbon dioxide and global warming.", 
             "answer": "Carbon dioxide traps heat in the atmosphere, creating a greenhouse effect that raises global temperatures.",
             "type": "open"},
            {"question": "How do rising sea levels impact coastal communities?", 
             "answer": "Impacts include flooding, erosion, contamination of freshwater, displacement of people, and damage to infrastructure.",
             "type": "open"},
            {"question": "What international agreements address climate change?", 
             "answer": "Agreements include the Paris Agreement, Kyoto Protocol, and UN Framework Convention on Climate Change.",
             "type": "open"},
            {"question": "Describe three individual actions that can reduce carbon footprint.", 
             "answer": "Actions may include reducing meat consumption, using renewable energy, minimizing air travel, using public transportation, and reducing waste.",
             "type": "open"},
            {"question": "Which gas is the most abundant greenhouse gas in Earth's atmosphere?", 
             "options": ["Carbon dioxide", "Methane", "Water vapor", "Nitrous oxide"],
             "answer": "Water vapor",
             "type": "mcq"},
            {"question": "What is the primary cause of sea level rise?", 
             "options": ["Thermal expansion of oceans", "Melting sea ice", "Melting land ice", "Increased precipitation"],
             "answer": "Melting land ice",
             "type": "mcq"},
            {"question": "Which energy source has the lowest carbon footprint?", 
             "options": ["Natural gas", "Nuclear", "Coal", "Solar"],
             "answer": "Solar",
             "type": "mcq"},
            {"question": "How do extreme weather events relate to climate change?", 
             "answer": "Climate change increases the frequency and intensity of extreme weather events by altering atmospheric conditions and energy balance.",
             "type": "open"},
            {"question": "What is renewable energy and why is it important for addressing climate change?", 
             "answer": "Renewable energy comes from naturally replenished sources like sun and wind. It's important because it produces little to no greenhouse gas emissions.",
             "type": "open"},
        ]
    elif "quantum computing" in text.lower() or "qubits" in text.lower():
        questions = [
            {"question": "What is quantum superposition?", 
             "answer": "The ability of quantum systems to exist in multiple states simultaneously until measured.",
             "type": "open"},
            {"question": "Explain quantum entanglement and its significance.", 
             "answer": "Quantum entanglement is when particles become correlated so the quantum state of each cannot be described independently. It enables quantum communication and computing advantages.",
             "type": "open"},
            {"question": "What are qubits and how do they differ from classical bits?", 
             "answer": "Qubits are quantum bits that can exist in superpositions of 0 and 1 states, unlike classical bits which must be either 0 or 1.",
             "type": "open"},
            {"question": "What is quantum decoherence and why is it a challenge?", 
             "answer": "Decoherence is the loss of quantum behavior when a system interacts with its environment. It causes errors in quantum computations.",
             "type": "open"},
            {"question": "Describe a potential application of quantum computing.", 
             "answer": "Applications include cryptography, drug discovery, optimization problems, materials science, and complex simulations.",
             "type": "open"},
            {"question": "Which principle allows quantum computers to process multiple possibilities simultaneously?", 
             "options": ["Entanglement", "Superposition", "Decoherence", "Quantum tunneling"],
             "answer": "Superposition",
             "type": "mcq"},
            {"question": "What is quantum supremacy?", 
             "options": ["When quantum computers can solve any problem", "When quantum computers outperform classical computers on specific tasks", "When quantum computers replace all classical computers", "When quantum computers achieve consciousness"],
             "answer": "When quantum computers outperform classical computers on specific tasks",
             "type": "mcq"},
            {"question": "Which algorithm demonstrates quantum computational advantage for integer factorization?", 
             "options": ["Grover's algorithm", "Shor's algorithm", "Deutsch-Jozsa algorithm", "Quantum Fourier Transform"],
             "answer": "Shor's algorithm",
             "type": "mcq"},
            {"question": "What is the significance of quantum error correction?", 
             "answer": "Quantum error correction allows quantum computers to function despite inevitable errors caused by decoherence and other quantum noise.",
             "type": "open"},
            {"question": "Compare and contrast quantum computing with classical computing.", 
             "answer": "Classical computing uses bits (0 or 1) and sequential operations, while quantum computing uses qubits (superpositions of states) and can perform parallel computations through quantum effects.",
             "type": "open"},
        ]
    else:
        # Generic questions if no specific topic is detected
        questions = [
            {"question": "Summarize the main points discussed in the text.", 
             "answer": "The answer should cover key concepts from the document with supporting details.",
             "type": "open"},
            {"question": "What are the implications of the ideas presented?", 
             "answer": "The answer should discuss potential consequences or applications of the concepts presented.",
             "type": "open"},
            {"question": "Identify and explain a key challenge mentioned in the text.", 
             "answer": "The answer should clearly identify a challenge and explain its significance.",
             "type": "open"},
            {"question": "How might the concepts in this text develop in the future?", 
             "answer": "The answer should provide reasonable predictions based on information in the text.",
             "type": "open"},
            {"question": "Compare and contrast two main ideas from the text.", 
             "answer": "The answer should identify similarities and differences between two major concepts.",
             "type": "open"},
            {"question": "Which statement best represents the main idea of the text?", 
             "options": ["Option A - general statement", "Option B - specific detail", "Option C - main theme", "Option D - tangential point"],
             "answer": "Option C - main theme",
             "type": "mcq"},
            {"question": "What is the primary purpose of this text?", 
             "options": ["To inform", "To persuade", "To entertain", "To instruct"],
             "answer": "To inform",
             "type": "mcq"},
            {"question": "Based on the text, which conclusion is most accurate?", 
             "options": ["Conclusion A", "Conclusion B", "Conclusion C", "Conclusion D"],
             "answer": "Conclusion B",
             "type": "mcq"},
            {"question": "What evidence supports the main argument of the text?", 
             "answer": "The answer should cite specific examples or evidence from the text that support the central argument.",
             "type": "open"},
            {"question": "Apply the concepts from the text to solve a real-world problem.", 
             "answer": "The answer should demonstrate understanding by applying concepts to a practical situation.",
             "type": "open"},
        ]
    
    # Add unique IDs to each question
    for i, q in enumerate(questions):
        q["id"] = str(uuid.uuid4())
        q["point_value"] = 10  # Default point value
    
    return questions

# Mock function to group questions into topics
def group_questions_into_topics(selected_questions):
    """Mock function to group questions into topics"""
    # Simple logic to group questions based on content
    topics = []
    
    # Group 1: Check for AI/ML related questions
    ai_questions = [q for q in selected_questions if any(keyword in q["question"].lower() 
                    for keyword in ["ai", "machine learning", "deep learning", "neural", "language processing"])]
    if ai_questions:
        topics.append({
            "title": "Artificial Intelligence Fundamentals",
            "required": True,
            "learning_objectives": ["Understand key AI concepts", "Differentiate AI approaches"],
            "questions": ai_questions,
            "start_timestamp": "00:00"
        })
    
    # Group 2: Check for climate related questions
    climate_questions = [q for q in selected_questions if any(keyword in q["question"].lower() 
                         for keyword in ["climate", "carbon", "global", "weather", "temperature"])]
    if climate_questions:
        topics.append({
            "title": "Climate Change and Environmental Impact",
            "required": True,
            "learning_objectives": ["Understand climate change mechanisms", "Identify environmental solutions"],
            "questions": climate_questions,
            "start_timestamp": "05:30"
        })
    
    # Group 3: Check for quantum computing questions
    quantum_questions = [q for q in selected_questions if any(keyword in q["question"].lower() 
                         for keyword in ["quantum", "qubit", "entanglement", "superposition"])]
    if quantum_questions:
        topics.append({
            "title": "Quantum Computing Principles",
            "required": False,
            "learning_objectives": ["Understand quantum computing basics", "Explore quantum applications"],
            "questions": quantum_questions,
            "start_timestamp": "10:45"
        })
    
    # Group 4: Default group for remaining questions
    other_questions = [q for q in selected_questions if not any(q in topic["questions"] for topic in topics)]
    if other_questions:
        topics.append({
            "title": "General Knowledge and Concepts",
            "required": False,
            "learning_objectives": ["Demonstrate comprehensive understanding", "Apply critical thinking"],
            "questions": other_questions,
            "start_timestamp": "15:20"
        })
    
    return {"topics": topics}

# Function to save question bank
def save_question_bank(question_bank, filename="sample-data/topics_with_q.json"):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w') as f:
        json.dump(question_bank, f, indent=2)
    return filename

# Streamlit UI
def main():
    st.set_page_config(page_title="Question Bank Creator")
    
    st.title("Question Bank Creator")
    st.write("Create a question bank from a URL or PDF file")
    
    # Step 1: Input source
    st.header("Step 1: Select Content Source")
    source_type = st.radio("Choose content source:", ["URL", "PDF Upload"])
    
    extracted_text = ""
    if source_type == "URL":
        # url with default value "https://www.youtube.com/watch?v=nKW8Ndu7Mjw"
        url = st.text_input("Enter Youtube Video URL:", "https://www.youtube.com/watch?v=nKW8Ndu7Mjw")
        if st.button("Extract Content from URL"):
            with st.spinner("Extracting content..."):
                extracted_text = extract_text_from_url(url)
                st.session_state.extracted_text = extracted_text
                st.success("Content extracted successfully!")
    else:
        uploaded_file = st.file_uploader("Upload PDF file", type=["pdf"])
        if uploaded_file is not None and st.button("Extract Content from PDF"):
            with st.spinner("Extracting content..."):
                # In a real application, we would process the PDF here
                # For this mockup, we'll use our mock function
                extracted_text = extract_text_from_pdf(uploaded_file)
                st.session_state.extracted_text = extracted_text
                st.success("Content extracted successfully!")
    
    # Display extracted text if available
    if "extracted_text" in st.session_state:
        with st.expander("View Extracted Text"):
            st.text_area("Content", st.session_state.extracted_text, height=200)
    
    # Step 2: Generate questions
    st.header("Step 2: Generate Questions")
    if "extracted_text" in st.session_state and st.button("Generate Questions"):
        with st.spinner("Generating questions..."):
            questions = generate_questions(st.session_state.extracted_text)
            st.session_state.generated_questions = questions
            st.success(f"Generated {len(questions)} questions!")
    
    # Step 3: Select questions
    if "generated_questions" in st.session_state:
        st.header("Step 3: Select Questions")
        
        # Display questions with checkboxes
        selected_questions = []
        for i, q in enumerate(st.session_state.generated_questions):
            question_type = "Multiple Choice" if q.get("type") == "mcq" else "Open-ended"
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                selected = st.checkbox("", key=f"q_{i}", value=True)
            with col2:
                st.write(f"**Q{i+1} [{question_type}]:** {q['question']}")
                with st.expander("View Answer"):
                    if q.get("type") == "mcq":
                        st.write("Options:")
                        for opt in q.get("options", []):
                            st.write(f"- {opt}")
                        st.write(f"Correct answer: {q.get('answer')}")
                    else:
                        st.write(q.get("answer", "No answer provided"))
            
            if selected:
                selected_questions.append(q)
        
        st.session_state.selected_questions = selected_questions
        
        if st.button("Group Selected Questions into Topics"):
            with st.spinner("Grouping questions..."):
                # Group questions into topics
                question_bank = group_questions_into_topics(selected_questions)
                st.session_state.question_bank = question_bank
                st.success(f"Created {len(question_bank['topics'])} topic groups!")
    
    # Step 4: Preview question bank
    if "question_bank" in st.session_state:
        st.header("Step 4: Preview Question Bank")
        
        # Display topics and questions in a tabular format
        for i, topic in enumerate(st.session_state.question_bank["topics"]):
            st.subheader(f"Topic {i+1}: {topic['title']}")
            st.write(f"Required: {'Yes' if topic.get('required', False) else 'No'}")
            st.write("Learning Objectives:")
            for obj in topic.get("learning_objectives", []):
                st.write(f"- {obj}")
            
            # Create a dataframe for the questions
            questions_data = []
            for q in topic.get("questions", []):
                q_type = "Multiple Choice" if q.get("type") == "mcq" else "Open-ended"
                
                # Format the answer field based on question type
                if q.get("type") == "mcq":
                    answer = f"Correct: {q.get('answer')}\nOptions: {', '.join(q.get('options', []))}"
                else:
                    # Truncate long answers for display
                    answer = q.get('answer', '')
                    if len(answer) > 100:
                        answer = answer[:97] + "..."
                
                questions_data.append({
                    "Question": q.get("question", ""),
                    "Type": q_type,
                    "Points": q.get("point_value", 10),
                    "Answer/Rubric": answer
                })
            
            if questions_data:
                df = pd.DataFrame(questions_data)
                st.table(df)
            else:
                st.write("No questions in this topic.")
        
        # Save question bank
        if st.button("Save Question Bank"):
            filename = save_question_bank(st.session_state.question_bank)
            st.success(f"Question bank saved to {filename}")
            
            # Provide download button for the saved file
            with open(filename, "r") as f:
                st.download_button(
                    label="Download Question Bank",
                    data=f,
                    file_name="question_bank.json",
                    mime="application/json"
                )

if __name__ == "__main__":
    main()
