import streamlit as st

st.set_page_config(
    page_title="Life Game",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from db.models import initialize_database
from components.auth import render_login_form
from components.ui_helpers import inject_custom_css

initialize_database()
inject_custom_css()

if st.session_state.get("authenticated"):
    username = st.session_state["username"]
    from db.queries import ensure_user_exists
    from game.cron import maybe_run_cron

    ensure_user_exists(username)

    if "cron_checked" not in st.session_state:
        cron_results = maybe_run_cron(username)
        st.session_state["cron_results"] = cron_results
        st.session_state["cron_checked"] = True

    st.switch_page("pages/1_Dashboard.py")
else:
    render_login_form()
