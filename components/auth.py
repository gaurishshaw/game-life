import io
import bcrypt
import pyotp
import qrcode
import streamlit as st


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_totp() -> pyotp.TOTP:
    secret = st.secrets["auth"]["totp_secret"]
    return pyotp.TOTP(secret)


def _check_password(username: str, password: str) -> bool:
    try:
        stored_username = st.secrets["auth"]["username"]
        stored_hash = st.secrets["auth"]["password_hash"].encode()
        return username == stored_username and bcrypt.checkpw(password.encode(), stored_hash)
    except Exception:
        return False


def _check_totp(code: str) -> bool:
    try:
        return _get_totp().verify(code.strip(), valid_window=1)
    except Exception:
        return False


def _totp_provisioning_uri() -> str:
    username = st.secrets["auth"].get("username", "user")
    return _get_totp().provisioning_uri(name=username, issuer_name="Life Game")


def _qr_code_bytes() -> bytes:
    uri = _totp_provisioning_uri()
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── Public API ────────────────────────────────────────────────────────────────

def render_login_form() -> None:
    st.markdown("""
    <div style="max-width:420px;margin:60px auto;text-align:center;">
        <h1 style="color:#9b59b6;font-size:3em;margin-bottom:0;">⚔️</h1>
        <h2 style="color:#e8e8e8;">Life Game</h2>
        <p style="color:#888;">Gamify your life. Achieve your goals.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            totp_code = st.text_input(
                "Authenticator Code",
                placeholder="6-digit code from your phone",
                max_chars=6,
                help="Open your Authenticator app (or Apple Passwords) and enter the current 6-digit code for Life Game.",
            )
            submit = st.form_submit_button("Enter the Game", use_container_width=True)

        if submit:
            if not _check_password(username, password):
                st.error("Invalid username or password.")
            elif not _check_totp(totp_code):
                st.error("Invalid or expired authenticator code. Check your app and try again.")
            else:
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.rerun()

        # ── First-time setup expander ────────────────────────────────────────
        st.markdown("")
        with st.expander("📱 First-time setup — scan QR code", expanded=False):
            st.markdown("""
            **Set up two-factor authentication on your phone:**

            1. Open **Apple Passwords** (Settings → Passwords) — or install **Google Authenticator** / **Authy**
            2. Add a new account and scan the QR code below
            3. Your phone will show a 6-digit code that refreshes every 30 seconds
            4. On iPhone, **Face ID** protects the code inside Apple Passwords

            > After scanning, enter your username + password + the 6-digit code above to log in.
            """)
            try:
                qr_bytes = _qr_code_bytes()
                st.image(qr_bytes, width=220, caption="Scan with Apple Passwords or Google Authenticator")
                uri = _totp_provisioning_uri()
                st.code(uri, language=None)
                st.caption("Or copy the URI above and paste it manually into your authenticator app.")
            except Exception as e:
                st.error(f"Could not generate QR code: {e}")


def require_auth() -> str:
    """Call at the top of every page. Returns username or redirects to login."""
    if not st.session_state.get("authenticated"):
        st.switch_page("app.py")
        st.stop()
    return st.session_state["username"]


def logout() -> None:
    st.session_state.clear()
    st.rerun()
