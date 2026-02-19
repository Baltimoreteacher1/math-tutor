import streamlit as st
import anthropic
import openai

st.set_page_config(page_title="Math Tutor", layout="wide", initial_sidebar_state="expanded")

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
</style>
""", unsafe_allow_html=True)

if "problems" not in st.session_state:
    st.session_state.problems = []
if "current_problem_index" not in st.session_state:
    st.session_state.current_problem_index = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "teacher_mode" not in st.session_state:
    st.session_state.teacher_mode = True
if "selected_ai" not in st.session_state:
    st.session_state.selected_ai = "Claude"

with st.sidebar:
    st.title("Math Tutor")
    
    st.subheader("API Configuration")
    
    ai_choice = st.radio(
        "Choose AI:",
        ["Claude (Anthropic)", "ChatGPT (OpenAI)"],
        key="ai_choice"
    )
    st.session_state.selected_ai = ai_choice
    
    if "Claude" in ai_choice:
        api_key = st.text_input("Anthropic API Key", type="password", key="api_key")
        if api_key:
            st.session_state.anthropic_api_key = api_key
        st.markdown("[Get Key](https://console.anthropic.com)")
    else:
        api_key = st.text_input("OpenAI API Key", type="password", key="api_key_openai")
        if api_key:
            st.session_state.openai_api_key = api_key
        st.markdown("[Get Key](https://platform.openai.com/api-keys)")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Teacher", use_container_width=True, 
                     type="primary" if st.session_state.teacher_mode else "secondary"):
            st.session_state.teacher_mode = True
    with col2:
        if st.button("Student", use_container_width=True,
                     type="primary" if not st.session_state.teacher_mode else "secondary"):
            st.session_state.teacher_mode = False
    
    st.markdown("---")
    
    if st.session_state.teacher_mode:
        st.subheader("Add Problems")
        new_problem = st.text_area("Word Problem:", height=100)
        
        if st.button("Add Problem", use_container_width=True, type="primary"):
            if new_problem.strip():
                st.session_state.problems.append(new_problem.strip())
                st.session_state.current_problem_index = 0
                st.session_state.messages = []
                st.rerun()
        
        st.markdown("---")
        st.subheader("Problems")
        
        if st.session_state.problems:
            for i, problem in enumerate(st.session_state.problems):
                col1, col2 = st.columns([0.85, 0.15])
                with col1:
                    if st.button(f"Problem {i+1}", use_container_width=True,
                                type="primary" if i == st.session_state.current_problem_index else "secondary", 
                                key=f"sel_{i}"):
                        st.session_state.current_problem_index = i
                        st.session_state.messages = []
                with col2:
                    if st.button("Delete", key=f"del_{i}", use_container_width=True):
                        st.session_state.problems.pop(i)
                        st.rerun()

if not st.session_state.teacher_mode:
    if st.session_state.current_problem_index is None or len(st.session_state.problems) == 0:
        st.info("No problem selected yet")
    else:
        current_problem = st.session_state.problems[st.session_state.current_problem_index]
        
        st.markdown(f"""
        <div class="problem-box">
            <h3>Problem {st.session_state.current_problem_index + 1}</h3>
            <p>{current_problem}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Let's solve this together!")
        
        if len(st.session_state.messages) == 0:
            st.markdown("Start by telling me: What do you understand about this problem?")
        
        for msg in st.session_state.messages:
            if msg["role"] == "student":
                st.markdown(f'<div class="student-message">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="tutor-message">{msg["content"]}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            user_input = st.text_input("Your response:", key="student_input", placeholder="Type here...")
        with col2:
            send_button = st.button("Send", use_container_width=True, type="primary")
        
        if send_button and user_input.strip():
            st.session_state.messages.append({"role": "student", "content": user_input})
            
            try:
                api_messages = []
                for msg in st.session_state.messages:
                    api_messages.append({
                        "role": "user" if msg["role"] == "student" else "assistant",
                        "content": msg["content"]
                    })
                
                system_prompt = f"""You are an adaptive math tutor helping students solve word problems.

Assess the student's language proficiency (beginner/intermediate/advanced) and math understanding from their response.

Scaffold their learning by:
- Praising effort and correct thinking
- Asking clarifying questions instead of giving answers
- Breaking down concepts into smaller steps
- Using simpler language for ESOL students
- Providing sentence starters when needed

Guide them through these steps in order:
1. Understanding - What is the problem asking?
2. Identifying - What information do we have and what are we solving for?
3. Planning - What operation will we use?
4. Solving - Work through the math
5. Checking - Does our answer make sense?

Adapt your language based on proficiency level. Keep responses short (2-3 sentences). Ask ONE question at a time.

Current problem: {current_problem}

Help the student based on where they are in their thinking."""
                
                if "Claude" in st.session_state.selected_ai:
                    if not hasattr(st.session_state, 'anthropic_api_key'):
                        st.error("Please set API key in sidebar")
                    else:
                        client = anthropic.Anthropic(api_key=st.session_state.anthropic_api_key)
                        response = client.messages.create(
                            model="claude-opus-4-20250805",
                            max_tokens=500,
                            system=system_prompt,
                            messages=api_messages
                        )
                        tutor_message = response.content[0].text
                        st.session_state.messages.append({"role": "tutor", "content": tutor_message})
                        st.rerun()
                else:
                    if not hasattr(st.session_state, 'openai_api_key'):
                        st.error("Please set API key in sidebar")
                    else:
                        openai.api_key = st.session_state.openai_api_key
                        response = openai.ChatCompletion.create(
                            model="gpt-4",
                            max_tokens=500,
                            system=system_prompt,
                            messages=api_messages
                        )
                        tutor_message = response.choices[0].message.content
                        st.session_state.messages.append({"role": "tutor", "content": tutor_message})
                        st.rerun()
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
else:
    st.title("Teacher Control Panel")
    
    if st.session_state.problems:
        st.success(f"You have {len(st.session_state.problems)} problem(s) ready")
    else:
        st.info("Add word problems using the sidebar")
```

## **requirements.txt** (same as before)
```
streamlit
anthropic
openai