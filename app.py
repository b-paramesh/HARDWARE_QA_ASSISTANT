import streamlit as st
from core.assistant import HardwareAssistant

st.set_page_config(page_title="Hardware Q&A Assistant", page_icon="💻", layout="wide")
st.title("💻 Hardware Q&A Assistant")
st.caption("A local hardware assistant for Windows and Linux. It inspects your system through validated, read-only tools.")

@st.cache_resource
def create_assistant():
    return HardwareAssistant()

assistant = create_assistant()

with st.sidebar:
    st.subheader("Assistant")
    st.write("NLP:", "Ollama local model" if assistant.ollama_available() else "Built-in fallback")
    st.write("Model:", assistant.model if assistant.ollama_available() else "Not connected")
    if st.button("Refresh all hardware", use_container_width=True):
        assistant.refresh_all()
        st.success("Hardware snapshot refreshed.")
    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.subheader("Inspection tools")
    for tool, available in assistant.get_tool_status().items():
        st.write(f"{'✅' if available else '⚠️'} {tool}")

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hello! Ask me about your CPU, RAM, RAM upgrade options, storage or GPU. I will inspect system data before answering."
    }]

for item in st.session_state.messages:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

question = st.chat_input("Ask a question about this computer...")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    history = st.session_state.messages[-11:-1]
    with st.chat_message("assistant"):
        with st.spinner("Understanding your question and inspecting hardware..."):
            answer = assistant.answer(question, history)
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})

with st.expander("View last collected hardware snapshot"):
    st.json(assistant.get_all_info())
