import streamlit as st


def render(supabase=None, settings=None):
    st.header("Config / Status")
    st.subheader("Environment")
    st.write({
        "SUPABASE_URL": bool(settings.SUPABASE_URL),
        "SUPABASE_KEY": bool(settings.SUPABASE_KEY),
    })

    st.subheader("Supabase client status")
    st.write("Client available" if supabase is not None else "Client not configured")

    if supabase is not None:
        if st.button("Test fetch from `inputs` table"):
            try:
                res = supabase.table("inputs").select("*").limit(5).execute()
                st.write(res.data if hasattr(res, "data") else res)
            except Exception as e:
                st.error(f"Test failed: {e}")
