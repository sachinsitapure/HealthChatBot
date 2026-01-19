import streamlit as st
from google import genai
import re

# Streamlit page config
st.set_page_config(
    page_title="Medical AI Chatbot",
    page_icon="🩺",
    layout="centered"
)

# Initialize Gemini client
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# ============================================
# GUARDRAILS CONFIGURATION
# ============================================

# Prohibited topics - High-risk medical queries
PROHIBITED_KEYWORDS = [
    # Self-harm and dangerous behaviors
    "suicide", "kill myself", "end my life", "self harm", "cut myself",
    "overdose", "od on", "lethal dose",
    
    # Prescription requests
    "prescribe", "prescription", "dosage for", "how much should i take",
    "give me medication", "what medicine should i take",
    
    # Dangerous substances
    "abortion pill", "misoprostol", "mifepristone",
    "opioid", "fentanyl", "controlled substance",
    
    # Emergency situations (should seek immediate help)
    "chest pain", "heart attack", "stroke", "seizure",
    "difficulty breathing", "can't breathe", "choking",
    "severe bleeding", "unconscious", "stopped breathing",
    "severe allergic reaction", "anaphylaxis",
    
    # Diagnosis requests
    "do i have", "diagnose me", "what disease do i have",
    "is it cancer", "do i have covid"
]

# Warning keywords - Trigger additional disclaimers
WARNING_KEYWORDS = [
    "pregnant", "pregnancy", "baby", "infant", "child", "pediatric",
    "medication", "drug", "pill", "treatment", "therapy",
    "pain", "fever", "infection", "rash", "wound"
]

# Emergency keywords - Direct to emergency services
EMERGENCY_KEYWORDS = [
    "chest pain", "heart attack", "stroke", "can't breathe",
    "severe bleeding", "unconscious", "seizure", "anaphylaxis",
    "severe allergic", "choking", "severe burn"
]

# System instructions
SYSTEM_PROMPT = """
You are a medical assistant chatbot for educational purposes only.

STRICT RULES YOU MUST FOLLOW:
1. NEVER diagnose any disease or condition
2. NEVER prescribe medications or recommend specific drugs
3. NEVER provide dosage information
4. NEVER encourage self-medication
5. NEVER provide information that could enable self-harm
6. ALWAYS recommend consulting a licensed healthcare provider
7. If asked about emergency symptoms, immediately direct to emergency services

Your role is to:
- Provide general health education
- Explain common symptoms in a general way
- Suggest basic, safe self-care measures (rest, hydration, etc.)
- Recognize warning signs that need professional care
- Be empathetic and supportive

You have access to the conversation history. Use it to provide consistent responses.

REMEMBER: You are NOT a doctor. You provide education, not medical advice.
"""

# ============================================
# GUARDRAIL FUNCTIONS
# ============================================

def check_prohibited_content(text):
    """Check if text contains prohibited keywords"""
    text_lower = text.lower()
    for keyword in PROHIBITED_KEYWORDS:
        if keyword in text_lower:
            return True, keyword
    return False, None

def check_emergency_content(text):
    """Check if text describes an emergency situation"""
    text_lower = text.lower()
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in text_lower:
            return True, keyword
    return False, None

def check_warning_content(text):
    """Check if text contains topics needing extra caution"""
    text_lower = text.lower()
    for keyword in WARNING_KEYWORDS:
        if keyword in text_lower:
            return True, keyword
    return False, None

def is_asking_for_diagnosis(text):
    """Detect diagnosis requests using patterns"""
    patterns = [
        r"do i have",
        r"is (it|this)",
        r"diagnose",
        r"what('s| is) (wrong|my condition)",
        r"am i (sick|ill)",
        r"could (it|this) be"
    ]
    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True
    return False

def is_asking_for_prescription(text):
    """Detect prescription/medication requests"""
    patterns = [
        r"what (medicine|medication|drug|pill)",
        r"should i take",
        r"can i take",
        r"prescribe",
        r"recommend.*medication",
        r"how much.*take"
    ]
    text_lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, text_lower):
            return True
    return False

def generate_emergency_response(keyword):
    """Generate response for emergency situations"""
    return f"""
🚨 **EMERGENCY ALERT** 🚨

Your message mentions **"{keyword}"** which could indicate a medical emergency.

**IMMEDIATE ACTION REQUIRED:**
- 🚑 Call emergency services (911 in US, 112 in EU, or your local emergency number)
- 🏥 Go to the nearest emergency room
- 📞 Contact your doctor immediately

**DO NOT WAIT** for online advice in emergency situations.

This chatbot CANNOT provide emergency medical care. Please seek immediate professional help.
"""

def generate_prohibited_response(keyword):
    """Generate response for prohibited topics"""
    return f"""
⚠️ **I Cannot Help With This Request**

I'm designed to provide general health education only. Your question about **"{keyword}"** falls outside my capabilities.

**Why I can't help:**
- I cannot diagnose conditions
- I cannot prescribe medications
- I cannot provide information that could be harmful
- I am not a substitute for a licensed healthcare provider

**What you should do:**
- 📞 **Contact a licensed doctor** or healthcare provider
- 🏥 **Visit a clinic** for professional evaluation
- 🆘 **Call a crisis helpline** if you're in distress:
  - National Suicide Prevention Lifeline: 988 (US)
  - Crisis Text Line: Text HOME to 741741

Your health and safety are important. Please seek professional help.
"""

def add_extra_disclaimer(message, keyword):
    """Add extra disclaimer for warning topics"""
    disclaimers = {
        "pregnant": "\n\n⚠️ **Pregnancy Notice:** Always consult your OB-GYN before taking any action. Pregnancy requires specialized medical care.",
        "baby": "\n\n⚠️ **Pediatric Notice:** Children require specialized care. Always consult a pediatrician for infant/child health concerns.",
        "medication": "\n\n⚠️ **Medication Notice:** Never take medications without consulting a healthcare provider. Drug interactions can be dangerous.",
        "pain": "\n\n⚠️ **Pain Notice:** Persistent or severe pain requires professional evaluation. Don't ignore warning signs."
    }
    
    for key, disclaimer in disclaimers.items():
        if key in keyword.lower():
            return message + disclaimer
    
    return message + "\n\n⚠️ **Important:** This is general information only. Consult a healthcare provider for personalized advice."

# ============================================
# UI COMPONENTS
# ============================================

st.title("🩺 Medical AI Chatbot")
st.caption("Powered by AI | Educational use only")

# Prominent disclaimer at the top
st.error("""
⚠️ **MEDICAL DISCLAIMER**
- This chatbot is for **educational purposes only**
- It does **NOT** replace professional medical advice
- It **CANNOT** diagnose diseases or prescribe medications
- **Always consult a licensed healthcare provider** for medical concerns
""")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "blocked_count" not in st.session_state:
    st.blocked_count = 0

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Describe your health question (general education only)...")

if user_input:
    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # ============================================
    # APPLY GUARDRAILS
    # ============================================
    
    # Check for emergency content
    is_emergency, emergency_keyword = check_emergency_content(user_input)
    if is_emergency:
        emergency_response = generate_emergency_response(emergency_keyword)
        st.session_state.messages.append({"role": "assistant", "content": emergency_response})
        with st.chat_message("assistant"):
            st.markdown(emergency_response)
        st.stop()
    
    # Check for prohibited content
    is_prohibited, prohibited_keyword = check_prohibited_content(user_input)
    if is_prohibited:
        prohibited_response = generate_prohibited_response(prohibited_keyword)
        st.session_state.messages.append({"role": "assistant", "content": prohibited_response})
        with st.chat_message("assistant"):
            st.markdown(prohibited_response)
        st.session_state.blocked_count += 1
        st.stop()
    
    # Check for diagnosis requests
    if is_asking_for_diagnosis(user_input):
        diagnosis_response = """
I understand you're looking for answers about your health, but I cannot diagnose medical conditions.

**Why diagnosis requires a doctor:**
- Physical examination is necessary
- Medical tests may be needed
- Individual medical history matters
- Accurate diagnosis requires professional training

**What I can do:**
- Provide general information about symptoms
- Explain when to seek medical care
- Suggest questions to ask your doctor

**Please consult a healthcare provider** for an accurate diagnosis.
"""
        st.session_state.messages.append({"role": "assistant", "content": diagnosis_response})
        with st.chat_message("assistant"):
            st.markdown(diagnosis_response)
        st.stop()
    
    # Check for prescription requests
    if is_asking_for_prescription(user_input):
        prescription_response = """
I cannot recommend or prescribe medications.

**Why medication requires a doctor:**
- Proper dosing depends on individual factors
- Drug interactions can be dangerous
- Side effects need to be monitored
- Some conditions mimic others

**What you should do:**
- Consult a licensed healthcare provider
- Discuss your symptoms and concerns
- Get proper examination and tests
- Follow prescribed treatment plans

**Never self-medicate** based on online information.
"""
        st.session_state.messages.append({"role": "assistant", "content": prescription_response})
        with st.chat_message("assistant"):
            st.markdown(prescription_response)
        st.stop()
    
    # ============================================
    # GENERATE AI RESPONSE (if guardrails passed)
    # ============================================
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Build conversation history
            conversation = SYSTEM_PROMPT + "\n\n"
            
            for msg in st.session_state.messages:
                role = msg["role"]
                content = msg["content"]
                conversation += f"{role.capitalize()}: {content}\n"
            
            # Call Gemini API
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=conversation
                )
                
                reply = response.text
                
                # Check if response needs additional warnings
                has_warning, warning_keyword = check_warning_content(user_input)
                if has_warning:
                    reply = add_extra_disclaimer(reply, warning_keyword)
                
                # Add standard disclaimer to every response
                reply += "\n\n---\n💡 **Remember:** This is educational information. Always consult a healthcare professional for medical advice."
                
                # Display and save response
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                
            except Exception as e:
                error_msg = f"⚠️ Error generating response: {str(e)}\n\nPlease try again or contact support if the issue persists."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Trim conversation history
    MAX_MESSAGES = 20
    if len(st.session_state.messages) > MAX_MESSAGES:
        st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]

# ============================================
# SIDEBAR WITH INFORMATION
# ============================================

with st.sidebar:
    st.header("ℹ️ About This Chatbot")
    
    st.markdown("""
    **What this chatbot CAN do:**
    ✅ Provide general health education
    ✅ Explain common symptoms
    ✅ Suggest when to see a doctor
    ✅ Offer basic wellness tips
    
    **What this chatbot CANNOT do:**
    ❌ Diagnose diseases
    ❌ Prescribe medications
    ❌ Replace a doctor's visit
    ❌ Handle emergencies
    """)
    
    st.divider()
    
    st.header("🆘 Emergency Resources")
    st.markdown("""
    **Emergency:** 911 (US)
    **Suicide Prevention:** 988
    **Crisis Text Line:** Text HOME to 741741
    **Poison Control:** 1-800-222-1222
    """)
    
    st.divider()
    
    st.header("📊 Session Stats")
    st.metric("Messages", len(st.session_state.messages))
    if hasattr(st.session_state, 'blocked_count'):
        st.metric("Blocked Queries", st.session_state.blocked_count)
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.blocked_count = 0
        st.rerun()
