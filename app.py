import streamlit as st

from config.settings import settings
from services.supabase_client import get_client

from pages import main_page, upload_page, results_page, config_page

st.set_page_config(page_title="[PROJECT NAME] Demo", layout="centered")

SUPABASE = get_client()

PAGES = {
    "Main": main_page.render,
    "Upload / Input": upload_page.render,
    "Results": results_page.render,
    "Config": config_page.render,
}


def main():
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))
    page = PAGES[selection]
    page(supabase=SUPABASE, settings=settings)


if __name__ == "__main__":
    main()
