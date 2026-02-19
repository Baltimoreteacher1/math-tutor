import streamlit as st
import anthropic
import openai
from datetime import datetime

# Page config
st.set_page_config(page_title="Math Tutor", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for better styling
st.markdown("""
<style>
    .problem-box {
        background: linear-gradient(135deg, #3b82f6 0%, #4f46e5 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    .student-message {
        background-color: #3b82f6;
        color: white;
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        max-width: 70%;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    .tutor-message {
        background-color: #f3f4f6;
        color: #1f2937;
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        max-width: 70%;
        border-bottom-left-radius: 4px;
    }
    .problem-item {
        background-color: #f3f4f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #3b82f6;
    }
    .problem-item.active {
        background-color: #dbeafe;
        border-left-color: #0284c7;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "problems" not in st.session_state:
    st.session_state.problems = []
if "current_problem_index" not in st.session_state:
    st.session_state.current_problem_index = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "teacher_mode" not in st.session_state:
    st.session_state.teacher_mode = True
if "api_keys_set" not in st.session_state:
    st.session_state.api_keys_set = False
if "selected_ai" not in st.session_state:
    st.session_state.selected_ai = "Claude"

# Sidebar for teacher controls
with st.sidebar:
    st.title("📚 Math Tutor Control Panel")
    
    st.subheader("API Configuration")
    
    # AI Selection
    st.session_state.selected_ai = st.radio(
        "Choose AI Tutor:",
        ["Claude (Anthropic)", "ChatGPT (OpenAI)"],
        index=0 if st.session_state.selected_ai == "Claude" else 1,
        key="ai_selection"
    )
    
    # API Key inputs based on selection
    if "Claude" in st.session_state.selected_ai:
        anthropic_key = st.text_input("Enter your Anthropic API Key", type="password", key="anthropic_key_input")
        if anthropic_key:
            st.session_state.anthropic_api_key = anthropic_key
            st.session_state.api_keys_set = True
        st.markdown("[Get Anthropic API Key →](https://console.anthropic.com)")
    else:
        openai_key = st.text_input("Enter your OpenAI API Key", type="password", key="openai_key_input")
        if openai_key:
            st.session_state.openai_api_key = openai_key
            st.session_state.api_keys_set = True
        st.markdown("[Get OpenAI API Key →](https://platform.openai.com/api-keys)")
    
    st.markdown("---")
    
    # Mode toggle
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👨‍🏫 Teacher Mode", use_container_width=True, 
                     type="primary" if st.session_state.teacher_mode else "secondary"):
            st.session_state.teacher_mode = True
            st.rerun()
    with col2:
        if st.button("👨‍🎓 Student Mode", use_container_width=True,
                     type="primary" if not st.session_state.teacher_mode else "secondary"):
            st.session_state.teacher_mode = False
            st.rerun()
    
    st.markdown("---")
    
    # Teacher mode controls
    if st.session_state.teacher_mode:
        st.subheader("Add Word Problems")
        new_problem = st.text_area("Paste a word problem:", height=120, key="problem_input")
        
        if st.button("➕ Add Problem", use_container_width=True, type="primary"):
            if new_problem.strip():
                st.session_state.problems.append(new_problem.strip())
                st.session_state.problem_input = ""
                st.session_state.current_problem_index = 0
                st.session_state.messages = []
                st.success("Problem added!")
                st.rerun()
        
        st.markdown("---")
        st.subheader("Problems List")
        
        if st.session_state.problems:
            for i, problem in enumerate(st.session_state.problems):
                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    is_active = i == st.session_state.current_problem_index
                    if st.button(f"Problem {i+1}", use_container_width=True,
                                type="primary" if is_active else "secondary", key=f"select_{i}"):
                        st.session_state.current_problem_index = i
                        st.session_state.messages = []
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"delete_{i}", use_container_width=True):
                        st.session_state.problems.pop(i)
                        if st.session_state.current_problem_index == i:
                            st.session_state.current_problem_index = None
                            st.session_state.messages = []
                        st.rerun()
        else:
            st.info("No problems added yet")
    
    st.markdown("---")
    st.markdown("**Tips:**\n- Use Claude for best tutoring\n- Use ChatGPT as alternative\n- Both work great for ESOL students!")

# Main content area
if not st.session_state.teacher_mode:
    # Student mode
    if not st.session_state.api_keys_set:
        st.warning("⚠️ Teacher hasn't set up an API key yet. Please ask your teacher to configure it.")
    elif st.session_state.current_problem_index is None or len(st.session_state.problems) == 0:
        st.info("📚 No problem selected. Your teacher will add problems here.")
    else:
        # Display current problem
        current_problem = st.session_state.problems[st.session_state.current_problem_index]
        st.markdown(f"""
        <div class="problem-box">
            <h3>Problem {st.session_state.current_problem_index + 1}</h3>
            <p style="font-size: 1.2em; margin-top: 1rem;">{current_problem}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display chat messages
        st.markdown("### Let's solve this together!")
        
        if len(st.session_state.messages) == 0:
            st.markdown("**Start by telling me:** What do you understand about this problem?")
        
        # Message display area
        messages_container = st.container()
        with messages_container:
            for msg in st.session_state.messages:
                if msg["role"] == "student":
                    st.markdown(f'<div class="student-message">{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="tutor-message">{msg["content"]}</div>', unsafe_allow_html=True)
        
        # Input area
        st.markdown("---")
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            user_input = st.text_input("Your response:", key="student_input", placeholder="Type your answer or question...")
        with col2:
            send_button = st.button("Send", use_container_width=True, type="primary")
        
        # Process user input
        if send_button and user_input.strip():
            # Add user message
            st.session_state.messages.append({"role": "student", "content": user_input})
            
            try:
                # Build conversation history for API
                api_messages = []
                for msg in st.session_state.messages:
                    api_messages.append({
                        "role": "user" if msg["role"] == "student" else "assistant",
                        "content": msg["content"]
                    })
                
                # System prompt for tutoring
                tutoring_system_prompt = f"""You are an adaptive math tutor helping students (both ESOL and non-ESOL) solve word problems. Your role is to:

1. ASSESS their response by identifying:
   - Their language proficiency level (beginner/intermediate/advanced English)
   - Their mathematical understanding
   - What they understand vs. what's unclear

2. SCAFFOLD their learning by:
   - Praising effort and correct thinking
   - Asking clarifying questions rather than giving answers
   - Breaking down concepts into smaller steps
   - Using simpler language for ESOL students while maintaining math accuracy
   - Providing sentence starters for ESOL students: "The problem asks me to...", "I need to find...", "The operation I should use is..."

3. GUIDE them through these steps IN ORDER (don't skip ahead):
   - Understanding: What is the problem asking?
   - Identifying: What information do we have? What are we looking for?
   - Planning: What operation or steps will we use?
   - Solving: Working through the math
   - Checking: Does our answer make sense?

4. ADAPT your language:
   - For beginner ESOL: Use short sentences, simple words, visual descriptions when possible
   - For intermediate ESOL: Use complete sentences but simpler structures
   - For advanced/non-ESOL: Use more complex explanations and encourage deeper thinking

5. Keep responses concise (2-3 sentences typically) - ask ONE question or give ONE piece of guidance at a time.

Current word problem: "{current_problem}"

Help the student work through this problem step by step based on where they are in their thinking."""
                
                # Call appropriate API
                if "Claude" in st.session_state.selected_ai:
                    if not hasattr(st.session_state, 'anthropic_api_key'):
                        st.error("API key not set. Please provide it in the sidebar.")
                    else:
                        client = anthropic.Anthropic(api_key=st.session_state.anthropic_api_key)
                        response = client.messages.create(
                            model="claude-opus-4-20250805",
                            max_tokens=1000,
                            system=tutoring_system_prompt,
                            messages=api_messages
                        )
                        tutor_message = response.content[0].text
                        st.session_state.messages.append({"role": "tutor", "content": tutor_message})
                        st.rerun()
                else:  # ChatGPT
                    if not hasattr(st.session_state, 'openai_api_key'):
                        st.error("API key not set. Please provide it in the sidebar.")
                    else:
                        openai.api_key = st.session_state.openai_api_key
                        response = openai.ChatCompletion.create(
                            model="gpt-4",
                            max_tokens=1000,
                            system=tutoring_system_prompt,
                            messages=api_messages
                        )
                        tutor_message = response.choices[0].message.content
                        st.session_state.messages.append({"role": "tutor", "content": tutor_message})
                        st.rerun()
            
            except anthropic.APIError as e:
                st.error(f"Anthropic API Error: {str(e)}")
            except openai.error.OpenAIError as e:
                st.error(f"OpenAI API Error: {str(e)}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
else:
    # Teacher mode view
    st.title("👨‍🏫 Teacher Control Panel")
    st.markdown("Use the sidebar on the left to add and manage word problems.")
    
    if st.session_state.problems:
        st.success(f"✅ You have {len(st.session_state.problems)} problem(s) ready for students")
        st.info(f"**Tip:** Click 'Student Mode' to preview how students will see the problems.")
    else:
        st.info("📝 Add word problems using the sidebar to get started!")