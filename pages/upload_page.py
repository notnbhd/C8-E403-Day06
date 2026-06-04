import streamlit as st
from helpers.utils import read_csv_bytes
from services.supabase_client import insert_row


def render(supabase=None, settings=None):
    st.header("Upload / Input")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded is not None:
        df = read_csv_bytes(uploaded)
        if df is None:
            st.error("Could not read CSV file. Ensure it's a valid CSV.")
            return
        st.success("File loaded — preview below")
        st.dataframe(df.head())

        if st.button("Save sample row to Supabase"):
            if supabase is None:
                st.warning("Supabase client not configured. Skipping save.")
            else:
                # For demo: save first row as a JSON object to `inputs` table
                row = df.iloc[0].to_dict()
                res = insert_row(supabase, "inputs", row)
                st.write(res)
