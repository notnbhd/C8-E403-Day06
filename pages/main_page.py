import streamlit as st


def render(**kwargs):
    st.title("[PROJECT NAME] — Demo")
    st.markdown("""
    This is a lightweight demo scaffold using Streamlit + Supabase.
    Use the sidebar to navigate to Upload / Results / Config pages.
    """)
