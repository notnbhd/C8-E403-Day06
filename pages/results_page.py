import streamlit as st
from services.supabase_client import fetch_table
import pandas as pd


def render(supabase=None, settings=None):
    st.header("Results")
    st.write("This page lists recent rows from the `results` table in Supabase.")
    if supabase is None:
        st.warning("Supabase client not configured. Configure credentials in .env.")
        return

    rows = fetch_table(supabase, "results", limit=200)
    if not rows:
        st.info("No rows found (or client unavailable).")
        return

    df = pd.DataFrame(rows)
    st.dataframe(df)
