import streamlit as st 
def show_dashboard_header(title: str):
    """Displays a themed header across pages."""
    st.markdown(
        f"""
        <div style="
            background-color: #1D3557; /* Use your PRIMARY_COLOR */
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 25px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        ">
            <h2 style="color: #F1FAEE; margin: 0;">{title}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )