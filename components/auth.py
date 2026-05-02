import bcrypt
import streamlit as st


def _check_password(username: str, password: str) -> bool:
    try:
        stored_username = st.secrets["auth"]["username"]
        stored_hash = st.secrets["auth"]["password_hash"].encode()
        return username == stored_username and bcrypt.checkpw(password.encode(), stored_hash)
    except Exception:
        return False


def render_login_form() -> None:
    st.markdown("""
    <div style="max-width: 400px; margin: 80px auto; text-align: center;">
        <h1 style="color: #9b59b6; font-size: 3em; margin-bottom: 0;">⚔️</h1>
        <h2 style="color: #e8e8e8;">Life Game</h2>
        <p style="color: #888;">Gamify your life. Achieve your goals.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("Enter the Game", use_container_width=True)

        if submit:
            if _check_password(username, password):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("Invalid username or password.")


def require_auth() -> str:
    """Call at the top of every page. Returns username or stops execution."""
    if not st.session_state.get("authenticated"):
        st.switch_page("app.py")
        st.stop()
    return st.session_state["username"]


def logout() -> None:
    st.session_state.clear()
    st.rerun()
