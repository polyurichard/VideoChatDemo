import streamlit as st
import pandas as pd
import json
import os
import re
from io import StringIO
import tempfile
import uuid
import random

# Set page config
st.set_page_config(page_title="Question Bank Creator", layout="wide")

# Mock function to replace API calls for transcript/text extraction
def extract_text_from_url(url):
    """Mock function to extract text from URL"""
    if "youtube" in url.lower():
        return """This is a mock transcript from a YouTube video about machine learning.
        The 7 steps of machine learning include gathering data, preparing data, choosing a model, training, evaluation, hyperparameter tuning, and prediction.
        Data gathering involves collecting relevant information like features and labels.
        Data preparation includes cleaning, normalizing, and splitting data into training and evaluation sets.
        Model selection depends on the type of data and problem you're solving.
        Training adjusts the model's parameters to make accurate predictions.
        Evaluation tests the model on unseen data to ensure it generalizes well.
        Hyperparameter tuning optimizes the model's performance by adjusting learning rate and other settings.
        Prediction is the final step where the trained model is used to answer questions with new data."""
    else:
        return """This is mock text from a webpage about climate change impacts.
        Global temperatures are rising at an alarming rate due to greenhouse gas emissions.
        Polar ice caps are melting, causing sea levels to rise and threatening coastal communities.
        Extreme weather events like hurricanes and droughts are becoming more frequent and intense.
        Carbon dioxide emissions continue to increase globally, primarily from burning fossil fuels.
        Renewable energy adoption is growing but not fast enough to prevent significant warming.
        Conservation efforts are crucial for ecosystem preservation and biodiversity protection.
        International cooperation through agreements like the Paris Climate Accord is essential.
        Individual actions such as reducing consumption and energy use can collectively make a difference."""

def extract_text_from_pdf(pdf_file):
    """Mock function to extract text from PDF"""
    return """This is mock text extracted from a PDF file about quantum computing.
    Quantum computing uses quantum bits or qubits that can exist in multiple states simultaneously.
    Quantum superposition allows qubits to represent many possible combinations of states at once.
    Quantum entanglement creates correlation between qubits that can be exploited for computation.
    Quantum algorithms like Shor's algorithm can solve certain problems exponentially faster than classical algorithms.
    Quantum error correction is necessary because qubits are highly susceptible to environmental interference.
    Quantum decoherence occurs when qubits lose their quantum properties through interaction with the environment.
    Quantum supremacy is achieved when quantum computers solve problems beyond classical computing capabilities.
    Major tech companies and research institutions are investing heavily in quantum computing development.
    Practical applications include cryptography, drug discovery, optimization problems, and materials science."""

# Mock function to generate questions from text with classification
def generate_questions(text, num_questions=10):
    """Generate questions from text with classifications based on Bloom's taxonomy and other categories"""
    questions = []
    
    # Define the categories
    bloom_categories = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
    knowledge_categories = ["factual", "conceptual", "procedural", "metacognitive"]
    
    if "machine learning" in text.lower():
        # Create questions related to machine learning
        questions = [
            {
                "question": "What are the seven steps of the machine learning process mentioned in the video?",
                "answer": "The seven steps are: gathering data, preparing data, choosing a model, training, evaluation, hyperparameter tuning, and prediction/inference.",
                "type": "remember",
                "category": "bloom"
            },
            {
                "question": "Explain how the training process in machine learning is similar to a person learning to drive a car.",
                "answer": "Just as a new driver initially doesn't know how to operate the car's controls but improves through practice and correction, a machine learning model starts with random parameters and gradually improves by adjusting these parameters based on feedback from training data.",
                "type": "understand",
                "category": "bloom"
            },
            {
                "question": "If you were building a machine learning model to predict housing prices, what features would you collect and how would you prepare this data?",
                "answer": "Features might include square footage, number of bedrooms/bathrooms, location, age of house, etc. Data preparation would involve normalizing numerical values, encoding categorical variables, handling missing values, and splitting into training and validation sets.",
                "type": "apply",
                "category": "bloom"
            },
            {
                "question": "Compare and contrast the data preparation and evaluation steps in the machine learning process. How do they relate to each other?",
                "answer": "Data preparation involves cleaning, normalizing, and splitting data into training and evaluation sets. Evaluation uses the reserved data to test model performance on unseen examples. The relationship is that proper data preparation, especially the training/evaluation split, directly impacts the validity of the evaluation and the model's real-world performance.",
                "type": "analyze",
                "category": "bloom"
            },
            {
                "question": "Assess the importance of hyperparameter tuning in the machine learning process. When might intensive tuning be beneficial versus excessive?",
                "answer": "Hyperparameter tuning is important for optimizing model performance by finding the best settings for parameters like learning rate or batch size. Intensive tuning is beneficial when small improvements have significant real-world impact or when working with complex models. However, it can become excessive when it leads to overfitting or when the time/resources spent don't justify marginal improvements. A balance should be struck based on the specific application needs and constraints.",
                "type": "evaluate",
                "category": "bloom"
            },
            {
                "question": "Design a machine learning system to help medical professionals diagnose a specific disease. Outline the seven steps you would follow and any ethical considerations unique to this application.",
                "answer": "The answer should include a comprehensive design covering data gathering (medical records, symptoms, test results), data preparation (anonymization, normalization), model selection appropriate for medical diagnosis, training approach, evaluation metrics (prioritizing recall/sensitivity), hyperparameter tuning, and deployment considerations. Ethical considerations should address patient privacy, algorithmic bias, explainability for medical professionals, regulatory compliance, and the appropriate level of human oversight.",
                "type": "create",
                "category": "bloom"
            },
            {
                "question": "According to the video, what fraction of data is typically reserved for evaluation rather than training?",
                "answer": "According to the video, a good rule of thumb is to use a training/evaluation split of 80/20 or 70/30, meaning 20-30% of the data is reserved for evaluation.",
                "type": "factual",
                "category": "knowledge"
            },
            {
                "question": "How does the concept of hyperparameters differ from the regular parameters (weights and biases) in a machine learning model?",
                "answer": "Regular parameters (weights and biases) are values that the model learns during training through optimization algorithms. Hyperparameters, in contrast, are settings that govern the training process itself and are set before training begins. Examples include learning rate, number of training iterations, and initial conditions. While regular parameters are optimized automatically during training, hyperparameters require manual tuning or specialized optimization techniques.",
                "type": "conceptual",
                "category": "knowledge"
            },
            {
                "question": "Describe the step-by-step process you would follow to evaluate whether your machine learning model is overfitting to the training data.",
                "answer": "1) Train the model on the training data set. 2) Record the model's performance metrics on the training data. 3) Apply the trained model to the evaluation/validation data set. 4) Compare performance metrics between training and validation sets. 5) If there's a significant gap with much better performance on training data, overfitting is likely occurring. 6) Implement regularization techniques or gather more training data as appropriate. 7) Retrain and reevaluate until the performance gap narrows sufficiently.",
                "type": "procedural",
                "category": "knowledge"
            },
            {
                "question": "Reflect on your own learning process when acquiring a new skill. How is it similar to or different from the machine learning training process described in the video?",
                "answer": "The answer should include thoughtful reflection on human learning versus machine learning, identifying similarities (iterative improvement through feedback, requiring examples, practice leading to better performance) and differences (humans can generalize from fewer examples, learn through various methods beyond direct feedback, apply creativity and intuition). The reflection should demonstrate metacognitive awareness of one's own learning processes compared to the algorithmic approach of machine learning.",
                "type": "metacognitive",
                "category": "knowledge"
            },
            {
                "question": "Machine learning has enabled computers to defeat world champions in complex games like chess and Go. How might these same techniques be applied to solve critical real-world problems that interest you personally?",
                "answer": "The answer could discuss applications in healthcare, climate science, education, or other domains, showing how the machine learning process described could be applied to a problem the student cares about. A good answer would connect the technical concepts from the video to a meaningful real-world application with personal relevance.",
                "type": "interest",
                "category": "motivation"
            }
        ]
    elif "climate change" in text.lower():
        questions = [
            {
                "question": "What are three major effects of climate change mentioned in the text?",
                "answer": "Rising global temperatures, melting polar ice caps leading to sea level rise, and increased frequency of extreme weather events.",
                "type": "remember",
                "category": "bloom"
            },
            {
                "question": "Explain how greenhouse gas emissions contribute to the process of global warming.",
                "answer": "Greenhouse gases like carbon dioxide trap heat in the atmosphere that would otherwise escape into space. As these gases increase from burning fossil fuels and other human activities, more heat is trapped, causing global temperatures to rise progressively.",
                "type": "understand",
                "category": "bloom"
            },
            {
                "question": "Based on the information about rising sea levels, how would you modify urban planning for a coastal city to adapt to climate change effects over the next 50 years?",
                "answer": "Adaptations might include: building sea walls or surge barriers; implementing zoning restrictions for low-lying areas; designing elevated or floating infrastructure; creating natural buffer zones like restored wetlands; developing evacuation plans and early warning systems; gradually relocating critical infrastructure to higher ground; and implementing water-resistant building codes.",
                "type": "apply",
                "category": "bloom"
            },
            {
                "question": "Analyze the relationship between international cooperation and individual actions in addressing climate change. What are the strengths and limitations of each approach?",
                "answer": "International cooperation provides coordinated action across borders, establishes global standards, and can mobilize significant resources, but faces challenges of enforcement, political disagreement, and slow implementation. Individual actions can drive market changes, demonstrate demand for sustainable options, and have cumulative effects, but may be limited in scale without systemic support. The most effective approach combines both: international frameworks that enable and incentivize individual and national actions.",
                "type": "analyze",
                "category": "bloom"
            },
            {
                "question": "Evaluate the claim that 'renewable energy adoption is growing but not fast enough to prevent significant warming.' What criteria would you use to assess whether the pace is adequate?",
                "answer": "Evaluation criteria should include: comparison of renewable energy growth rates against emissions reduction targets from scientific bodies like the IPCC; analysis of whether deployment is consistent with limiting warming to 1.5-2°C; consideration of technology adoption S-curves and whether renewables are approaching inflection points; examination of investment levels compared to what's needed; assessment of policy support and barriers; and consideration of concurrent fossil fuel development. A strong answer would weigh these factors to reach a reasoned conclusion.",
                "type": "evaluate",
                "category": "bloom"
            },
            {
                "question": "Design a comprehensive climate action plan for your community that addresses both mitigation and adaptation strategies, incorporating renewable energy, conservation efforts, and community engagement.",
                "answer": "The plan should include: 1) Emissions inventory and reduction targets; 2) Renewable energy initiatives (community solar, wind projects, microgrids); 3) Energy efficiency programs for buildings; 4) Transportation solutions (public transit, EV infrastructure, bike paths); 5) Adaptation measures based on local climate risks; 6) Natural resource protection and ecosystem services; 7) Waste reduction and circular economy initiatives; 8) Climate-resilient infrastructure; 9) Community education and engagement strategies; 10) Funding mechanisms, metrics for success, and implementation timeline.",
                "type": "create",
                "category": "bloom"
            },
            {
                "question": "What is the primary source of increasing carbon dioxide emissions globally according to the text?",
                "answer": "According to the text, the primary source of increasing carbon dioxide emissions globally is burning fossil fuels.",
                "type": "factual",
                "category": "knowledge"
            },
            {
                "question": "Explain the concept of how melting ice caps contribute to sea level rise rather than melting ice cubes in a glass of water.",
                "answer": "When ice that is already floating in water melts (like ice cubes in a drink), it doesn't raise the water level because the ice already displaced its weight in water. However, polar ice caps rest largely on land. When this land-based ice melts and flows into the ocean, it adds water that wasn't previously part of the ocean system, causing sea levels to rise. Additionally, as ocean waters warm, they expand in volume due to thermal expansion, further contributing to sea level rise.",
                "type": "conceptual",
                "category": "knowledge"
            },
            {
                "question": "Outline a step-by-step process for an individual to calculate their carbon footprint and identify the most effective actions to reduce it.",
                "answer": "1) Gather data about your energy usage (electricity/gas bills), transportation (vehicle mileage, flights taken), food consumption habits, and purchasing patterns. 2) Use a carbon footprint calculator from a reputable organization. 3) Input your data to generate your total emissions and see how they compare to averages. 4) Review the breakdown to identify your largest emission sources. 5) Research the most impactful reduction strategies for your biggest categories. 6) Create a prioritized action plan focusing on high-impact changes first. 7) Implement changes and track your progress. 8) Reassess periodically and adjust strategies as needed.",
                "type": "procedural",
                "category": "knowledge"
            },
            {
                "question": "Reflect on how your personal beliefs and values influence your perception of climate change information and your willingness to take action. What cognitive biases might affect your thinking on this topic?",
                "answer": "The answer should include thoughtful self-reflection on how one's values (political, economic, social) shape their climate change perspectives, examination of cognitive biases like confirmation bias (seeking information that confirms existing beliefs), temporal discounting (valuing present concerns over future ones), or optimism bias (believing negative outcomes won't affect oneself). It should demonstrate awareness of how one processes climate information and makes decisions about personal actions.",
                "type": "metacognitive",
                "category": "knowledge"
            },
            {
                "question": "If you could develop a breakthrough technology to address one aspect of climate change, what would it be and how might it transform our response to the climate crisis?",
                "answer": "The answer should describe an innovative technology addressing a climate challenge (energy storage, carbon capture, alternative materials, etc.), explaining its potential impact and why it interests the student personally. It should connect technical possibilities with meaningful outcomes for people and the planet.",
                "type": "interest",
                "category": "motivation"
            }
        ]
    elif "quantum computing" in text.lower():
        questions = [
            {
                "question": "What are qubits and what unique property allows them to differ from classical bits?",
                "answer": "Qubits are quantum bits, the fundamental units of quantum information. Unlike classical bits that can only be in states 0 or 1, qubits can exist in multiple states simultaneously through the property of quantum superposition.",
                "type": "remember",
                "category": "bloom"
            },
            {
                "question": "Explain how quantum entanglement contributes to the power of quantum computing.",
                "answer": "Quantum entanglement creates correlations between qubits where the state of one qubit is dependent on the state of another, regardless of distance. This allows quantum computers to process multiple possibilities simultaneously and perform certain calculations exponentially faster than classical computers because changes to one qubit can instantly affect its entangled partners, enabling complex operations to be performed in parallel.",
                "type": "understand",
                "category": "bloom"
            },
            {
                "question": "How could Shor's algorithm be applied to impact current encryption methods, and what steps would organizations need to take to prepare for this?",
                "answer": "Shor's algorithm could efficiently factor large numbers, breaking RSA encryption which relies on the difficulty of this task. Organizations would need to: 1) Inventory systems using vulnerable encryption, 2) Develop migration plans to quantum-resistant algorithms, 3) Implement crypto-agility to quickly update encryption methods, 4) Consider hybrid approaches during transition, 5) Monitor quantum computing developments to time the transitions appropriately, and 6) Participate in standardization efforts for post-quantum cryptography.",
                "type": "apply",
                "category": "bloom"
            },
            {
                "question": "Compare and contrast the challenges of scaling classical computing versus quantum computing. What fundamental differences affect their development trajectories?",
                "answer": "Classical computing scaling faces challenges of physical limits to transistor miniaturization, heat dissipation, and power consumption, but benefits from decades of manufacturing optimization. Quantum computing faces fundamentally different challenges: maintaining quantum coherence (preventing information loss), scaling up qubit counts while preserving fidelity, developing error correction that doesn't consume too many physical qubits, creating specialized materials and cooling systems, and building a new software stack from the ground up. While classical computing improvements are largely incremental now, quantum computing may experience more dramatic breakthroughs but also significant technical setbacks as it develops.",
                "type": "analyze",
                "category": "bloom"
            },
            {
                "question": "Evaluate the claim that 'quantum supremacy has been achieved.' What criteria should be used to assess this claim, and how meaningful is this milestone for practical quantum computing applications?",
                "answer": "Evaluation should consider: whether the quantum computer solved a problem beyond classical capabilities (even if contrived); verification of results; reproducibility; scalability of the approach; error rates; and practical relevance of the demonstrated task. While quantum supremacy represents an important technical milestone showing quantum computers can outperform classical ones on specific tasks, it's only an early step toward practical applications. The gap between demonstrating supremacy on carefully chosen problems and developing error-corrected quantum computers that solve real-world problems remains substantial. A balanced evaluation would recognize the achievement while acknowledging its limitations and the significant work still needed.",
                "type": "evaluate",
                "category": "bloom"
            },
            {
                "question": "Design a novel application of quantum computing that could address a currently unsolved problem in healthcare or medicine. Explain your approach and how it leverages unique quantum properties.",
                "answer": "The design should propose an innovative application like drug discovery optimization, protein folding simulation, personalized medicine algorithms, or medical imaging enhancement. It should explain: 1) The specific healthcare problem addressed; 2) Why classical computing approaches are insufficient; 3) How quantum algorithms (e.g., quantum machine learning, quantum annealing, quantum simulation) would be applied; 4) Which quantum properties (superposition, entanglement, interference) enable the solution; 5) The technical approach and resource requirements; 6) Expected benefits and potential implementation challenges; and 7) A roadmap for development as quantum hardware matures.",
                "type": "create",
                "category": "bloom"
            },
            {
                "question": "How many states can a quantum bit (qubit) represent simultaneously due to superposition?",
                "answer": "A single qubit can exist in a superposition of two basic states (0 and 1) simultaneously, representing a continuous spectrum of states that are combinations of both. A system of n qubits can represent 2^n states simultaneously, exponentially more than classical bits.",
                "type": "factual",
                "category": "knowledge"
            },
            {
                "question": "Explain the conceptual relationship between quantum decoherence and the challenges of building practical quantum computers.",
                "answer": "Quantum decoherence occurs when quantum systems interact with their environment, causing them to lose their quantum properties and behave more like classical systems. This relationship is central to quantum computing challenges because qubits must maintain coherence to perform quantum calculations, yet they're extremely sensitive to environmental disturbances (temperature, electromagnetic radiation, vibration). As more qubits are added to a system, maintaining coherence becomes exponentially harder. This creates a fundamental tension: quantum computers need isolation from the environment for coherence, yet must also interact with control systems and measurement devices. This conceptual challenge drives the need for error correction, specialized materials, extreme cooling, and other complex engineering solutions in quantum computer design.",
                "type": "conceptual",
                "category": "knowledge"
            },
            {
                "question": "Describe the procedure for implementing Grover's quantum search algorithm to find an element in an unsorted database, including the key steps and how they provide a quadratic speedup over classical methods.",
                "answer": "1) Initialize all qubits in superposition to represent all possible database indices simultaneously. 2) Apply an oracle function that marks the target element by inverting its amplitude. 3) Apply amplitude amplification through a diffusion operator that increases the amplitude of the marked state and decreases others (specifically: reflect amplitudes about the average). 4) Repeat steps 2-3 approximately √N times, where N is the database size. 5) Measure the system to obtain the index of the target element with high probability. This provides quadratic speedup because classical algorithms require O(N) operations to search an unsorted database, while Grover's algorithm requires only O(√N) operations, due to quantum parallelism and the interference effects that amplify the correct answer's probability.",
                "type": "procedural",
                "category": "knowledge"
            },
            {
                "question": "As you learn about quantum computing concepts, reflect on which aspects you find most challenging to understand and why. How does your background in classical computing affect your ability to grasp quantum principles?",
                "answer": "The answer should include thoughtful self-reflection on cognitive challenges in understanding quantum concepts that defy classical intuition. It might discuss difficulties with visualizing superposition and entanglement, mathematical formalism barriers, or conceptual leaps required. The reflection should examine how prior knowledge of classical computing might both help (providing technical context) and hinder (creating conceptual barriers) understanding. A strong answer demonstrates awareness of one's learning process and mental models when approaching quantum computing concepts.",
                "type": "metacognitive",
                "category": "knowledge"
            },
            {
                "question": "Quantum computers have been described as potentially revolutionary for scientific discovery. Which scientific mystery or technological challenge are you most excited to see quantum computers help solve, and why?",
                "answer": "The answer should identify a specific scientific problem (materials discovery, climate modeling, biochemical simulation, etc.) that quantum computing might help solve, explaining its importance and why it interests the student personally. It should connect quantum computing capabilities to meaningful scientific or technological advancement that inspires curiosity.",
                "type": "interest",
                "category": "motivation"
            }
        ]
    else:
        # Generic questions if no specific topic is detected
        questions = [
            {
                "question": "What are the main concepts or ideas presented in the text?",
                "answer": "The answer should identify and list key concepts from the document with supporting details.",
                "type": "remember",
                "category": "bloom"
            },
            {
                "question": "Explain how the main concepts in this text relate to each other.",
                "answer": "The answer should demonstrate understanding by explaining relationships between key concepts and how they form a coherent framework or argument.",
                "type": "understand",
                "category": "bloom"
            },
            {
                "question": "How would you apply the concepts from this text to solve a real-world problem in your field?",
                "answer": "The answer should demonstrate practical application of the concepts to a specific problem, showing how the information could be used in a real situation.",
                "type": "apply",
                "category": "bloom"
            },
            {
                "question": "Analyze the strengths and weaknesses of the approach or arguments presented in this text.",
                "answer": "The answer should break down the approach into components, examining assumptions, evidence, logic, and potential flaws or gaps in the argument.",
                "type": "analyze",
                "category": "bloom"
            },
            {
                "question": "Evaluate the significance of these ideas in relation to current developments in this field.",
                "answer": "The answer should assess the value, importance, or quality of the ideas presented, using relevant criteria and contextualizing within the broader field.",
                "type": "evaluate",
                "category": "bloom"
            },
            {
                "question": "Design a new approach or solution that builds upon and extends the ideas presented in this text.",
                "answer": "The answer should demonstrate creativity by proposing something new that incorporates and goes beyond the original concepts.",
                "type": "create",
                "category": "bloom"
            },
            {
                "question": "What specific data or evidence does the text provide to support its main claims?",
                "answer": "The answer should identify concrete facts, statistics, examples, or other evidence presented in the text.",
                "type": "factual",
                "category": "knowledge"
            },
            {
                "question": "Explain the fundamental principles or theories that underlie the information presented in this text.",
                "answer": "The answer should identify and explain theoretical frameworks, models, or principles that give meaning to the specific facts in the text.",
                "type": "conceptual",
                "category": "knowledge"
            },
            {
                "question": "Outline a step-by-step process for implementing or applying the main ideas from this text.",
                "answer": "The answer should provide a clear sequence of actions or methods for putting the concepts into practice.",
                "type": "procedural",
                "category": "knowledge"
            },
            {
                "question": "Reflect on how your understanding of this topic has evolved after reading this text, and what questions remain for your further exploration.",
                "answer": "The answer should demonstrate self-awareness about one's learning process, how new information connects to prior knowledge, and identification of knowledge gaps.",
                "type": "metacognitive",
                "category": "knowledge"
            },
            {
                "question": "How might the concepts in this text change or impact future developments in ways that could affect your personal or professional interests?",
                "answer": "The answer should connect the content to personal relevance, demonstrating engagement with potential applications or implications that spark curiosity.",
                "type": "interest",
                "category": "motivation"
            }
        ]
    
    # Add unique IDs to each question
    for i, q in enumerate(questions):
        q["id"] = str(uuid.uuid4())
        q["point_value"] = 10  # Default point value
    
    return questions

# Mock function to group questions into topics
def group_questions_into_topics(selected_questions):
    """Mock function to group questions into topics"""
    topics = []
    
    # Group by Bloom's taxonomy levels
    bloom_questions = [q for q in selected_questions if q.get("category") == "bloom"]
    if bloom_questions:
        topics.append({
            "title": "Bloom's Taxonomy Questions",
            "required": True,
            "learning_objectives": ["Develop critical thinking skills at various cognitive levels", 
                                  "Apply different types of thinking from basic recall to creative synthesis"],
            "questions": bloom_questions,
            "start_timestamp": "00:00"
        })
    
    # Group by knowledge categories
    knowledge_questions = [q for q in selected_questions if q.get("category") == "knowledge"]
    if knowledge_questions:
        topics.append({
            "title": "Knowledge Dimension Questions",
            "required": True,
            "learning_objectives": ["Explore different types of knowledge", 
                                  "Develop factual, conceptual, procedural, and metacognitive understanding"],
            "questions": knowledge_questions,
            "start_timestamp": "05:30"
        })
    
    # Group motivational questions
    motivational_questions = [q for q in selected_questions if q.get("category") == "motivation"]
    if motivational_questions:
        topics.append({
            "title": "Engagement Questions",
            "required": False,
            "learning_objectives": ["Connect content to personal interests", 
                                  "Explore real-world applications and relevance"],
            "questions": motivational_questions,
            "start_timestamp": "10:45"
        })
    
    # If there are any questions not yet categorized, add them to a general topic
    other_questions = [q for q in selected_questions if not any(q in topic["questions"] for topic in topics)]
    if other_questions:
        topics.append({
            "title": "Additional Questions",
            "required": False,
            "learning_objectives": ["Reinforce key concepts", "Provide additional practice opportunities"],
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
    st.title("Question Bank Creator")
    st.write("Create a question bank from a URL or PDF file")
    
    # Step 1: Input source
    st.header("Step 1: Select Content Source")
    source_type = st.radio("Choose content source:", ["URL", "PDF Upload"])
    
    extracted_text = ""
    if source_type == "URL":
        url = st.text_input("Enter URL (YouTube or webpage):")
        if url and st.button("Extract Content from URL"):
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
        
        # Create tabs for different question categories
        bloom_questions = [q for q in st.session_state.generated_questions if q.get("category") == "bloom"]
        knowledge_questions = [q for q in st.session_state.generated_questions if q.get("category") == "knowledge"]
        motivation_questions = [q for q in st.session_state.generated_questions if q.get("category") == "motivation"]
        
        tabs = st.tabs(["Bloom's Taxonomy", "Knowledge Dimensions", "Engagement Questions"])
        
        selected_questions = []
        
        with tabs[0]:
            st.subheader("Bloom's Taxonomy Questions")
            for i, q in enumerate(bloom_questions):
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    selected = st.checkbox("", key=f"bloom_q_{i}", value=True)
                with col2:
                    st.write(f"**Q{i+1} [{q['type'].capitalize()}]:** {q['question']}")
                    with st.expander("View Answer"):
                        st.write(q.get("answer", "No answer provided"))
                
                if selected:
                    selected_questions.append(q)
        
        with tabs[1]:
            st.subheader("Knowledge Dimension Questions")
            for i, q in enumerate(knowledge_questions):
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    selected = st.checkbox("", key=f"know_q_{i}", value=True)
                with col2:
                    st.write(f"**Q{i+1} [{q['type'].capitalize()}]:** {q['question']}")
                    with st.expander("View Answer"):
                        st.write(q.get("answer", "No answer provided"))
                
                if selected:
                    selected_questions.append(q)
        
        with tabs[2]:
            st.subheader("Engagement Questions")
            for i, q in enumerate(motivation_questions):
                col1, col2 = st.columns([0.1, 0.9])
                with col1:
                    selected = st.checkbox("", key=f"motiv_q_{i}", value=True)
                with col2:
                    st.write(f"**Q{i+1} [{q['type'].capitalize()}]:** {q['question']}")
                    with st.expander("View Answer"):
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
                # Format the answer field
                answer = q.get('answer', '')
                if len(answer) > 100:
                    answer = answer[:97] + "..."
                
                questions_data.append({
                    "Question": q.get("question", ""),
                    "Type": q.get("type", "").capitalize(),
                    "Category": q.get("category", "").capitalize(),
                    "Points": q.get("point_value", 10),
                    "Answer/Rubric": answer
                })
            
            if questions_data:
                df = pd.DataFrame(questions_data)
                st.dataframe(df)
            else:
                st.write("No questions in this topic.")
        
        # Save question bank
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Question Bank"):
                filename = save_question_bank(st.session_state.question_bank)
                st.success(f"Question bank saved to {filename}")
                
                # Store the filename for download
                st.session_state.saved_filename = filename
        
        # Provide download button if file has been saved
        if "saved_filename" in st.session_state:
            with col2:
                with open(st.session_state.saved_filename, "r") as f:
                    st.download_button(
                        label="Download Question Bank",
                        data=f,
                        file_name="question_bank.json",
                        mime="application/json"
                    )

if __name__ == "__main__":
    main()
