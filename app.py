# app.py
import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000"

def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        text = resp.text if hasattr(resp, "text") else None
        return {"detail": text} if text else {}

def _parse_jwt_no_verify(token: str):
    import base64, json
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {}
        payload_b64 = parts[1]
        rem = len(payload_b64) % 4
        if rem:
            payload_b64 += '=' * (4 - rem)
        decoded = base64.urlsafe_b64decode(payload_b64)
        return json.loads(decoded)
    except Exception:
        return {}

st.set_page_config(
    page_title="Ethara Task Manager",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- GLOBAL LIGHT THEME & SAAS STYLING ---
global_css = """
<style>
    /* Hide Default Streamlit UI */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Global Background and Typography */
    .stApp {
        background-color: #f8fafc !important; 
        font-family: 'Inter', 'Segoe UI', sans-serif !important;
    }
    
    h1, h2, h3, h4 {
        color: #1e293b !important; 
    }
    
    label {
        color: #64748b !important; 
    }

    /* Global Button Styling */
    button[kind="primary"] {
        background-color: #a855f7 !important;
        border-radius: 8px !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }
    
    /* THE ULTIMATE TEXT FIX: Explicitly target Streamlit's nested <p> and <div> tags inside buttons */
    button[kind="primary"] p, 
    button[kind="primary"] div, 
    button[kind="primary"] span {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    button[kind="primary"]:hover {
        background-color: #9333ea !important;
        box-shadow: 0 4px 12px rgba(168, 85, 247, 0.3) !important;
        transform: translateY(-1px);
    }
    
    button[kind="secondary"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
    }
    
    button[kind="secondary"] p,
    button[kind="secondary"] div {
        color: #64748b !important;
        font-weight: 500 !important;
    }
    
    button[kind="secondary"]:hover {
        border-color: #a855f7 !important;
    }

    /* Dashboard Forms & Containers (Acting as our uniform boxes) */
    div[data-testid="metric-container"], 
    .uniform-box,
    [data-testid="stForm"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
    }
    
    /* Global Input Styling */
    input, textarea, div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        color: #1e293b !important;
    }
    input:focus, textarea:focus, div[data-baseweb="select"] > div:focus-within {
        border-color: #a855f7 !important;
        box-shadow: 0 0 0 2px rgba(168, 85, 247, 0.1) !important;
    }
</style>
"""
st.markdown(global_css, unsafe_allow_html=True)

# --- SESSION STATE ---
if "token" not in st.session_state:
    st.session_state.token = None
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = None

# --- VIEWS ---

def login_view():
    st.markdown("""
    <style>
        .block-container {
            max-width: 1000px !important;
            padding-top: 8vh !important;
        }
        
        [data-testid="stHorizontalBlock"] {
            gap: 0rem;
            background-color: #ffffff !important; 
            border-radius: 24px;
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.1);
            border: 1px solid #f1f5f9;
        }
        
        /* LEFT PANE: White Form */
        [data-testid="column"]:nth-of-type(1) {
            background-color: #ffffff !important;
            padding: 4rem 3.5rem !important;
        }
        
        /* OVERRIDE: Remove the box styling from the forms just for the login page */
        [data-testid="column"]:nth-of-type(1) [data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
            box-shadow: none !important;
            background-color: transparent !important;
        }
        
        [data-testid="column"]:nth-of-type(1) p {
            color: #64748b !important;
        }
        
        [data-testid="column"]:nth-of-type(1) button[kind="primary"] p,
        [data-testid="column"]:nth-of-type(1) button[kind="primary"] div {
            color: #ffffff !important;
        }
        
        /* RIGHT PANE: Purple banner */
        [data-testid="column"]:nth-of-type(2) {
            background: linear-gradient(135deg, #a855f7 0%, #7c3aed 100%) !important;
            padding: 4rem 3rem !important;
            display: flex;
            flex-direction: column;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }
        
        [data-testid="column"]:nth-of-type(2) h1,
        [data-testid="column"]:nth-of-type(2) p,
        [data-testid="column"]:nth-of-type(2) span,
        [data-testid="column"]:nth-of-type(2) div {
            color: #ffffff !important;
        }
        
        /* Transparent inputs for the left pane */
        [data-testid="column"]:nth-of-type(1) div[data-baseweb="input"],
        [data-testid="column"]:nth-of-type(1) div[data-baseweb="base-input"],
        [data-testid="column"]:nth-of-type(1) input,
        [data-testid="column"]:nth-of-type(1) div[data-baseweb="select"] > div {
            background-color: transparent !important;
            border: none !important;
            border-bottom: 2px solid #e2e8f0 !important;
            border-radius: 0 !important;
            color: #1e293b !important;
            box-shadow: none !important;
            padding-left: 0 !important;
        }

        [data-testid="column"]:nth-of-type(1) input:focus,
        [data-testid="column"]:nth-of-type(1) div[data-baseweb="select"] > div:focus-within {
            border-bottom: 2px solid #a855f7 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    if "show_signup" not in st.session_state:
        st.session_state.show_signup = False

    col1, col2 = st.columns([1.2, 1])

    with col1:
        if not st.session_state.show_signup:
            st.markdown("<h1 style='margin-bottom: 0px;'>Login</h1>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 14px; margin-bottom: 2.5rem;'>Enter your account details</p>", unsafe_allow_html=True)
            
            with st.form("login_form", clear_on_submit=True):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                st.markdown("<p style='font-size: 12px; text-align: left; cursor: pointer; margin-top: 10px; color: #a855f7 !important;'>Forgot Password? (not set up yet)</p>", unsafe_allow_html=True)
                
                if st.form_submit_button("Login", use_container_width=True, type="primary"):
                    if not username or not password:
                        st.error("Please enter both username and password")
                    else:
                        with st.spinner("Authenticating..."):
                            response = requests.post(f"{API_URL}/auth/login", data={"username": username, "password": password}, timeout=5)
                            if response.status_code == 200:
                                data = safe_json(response)
                                st.session_state.token = data.get("access_token")
                                payload = _parse_jwt_no_verify(data.get("access_token", ""))
                                st.session_state.role = payload.get("role")
                                st.session_state.username = payload.get("sub")
                                st.rerun()
                            else:
                                st.error("Invalid credentials: " + safe_json(response).get("detail", "Please try again"))
            
            st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
            if st.button("Don't have an account? Sign up", use_container_width=True):
                st.session_state.show_signup = True
                st.rerun()
                    
        else:
            st.markdown("<h1 style='margin-bottom: 0px;'>Sign Up</h1>", unsafe_allow_html=True)
            st.markdown("<p style='font-size: 14px; margin-bottom: 2.5rem;'>Create your workspace account</p>", unsafe_allow_html=True)
            
            with st.form("register_form", clear_on_submit=True):
                new_user = st.text_input("Username")
                new_pass = st.text_input("Password", type="password")
                role = st.selectbox("Account Type", ["Member", "Admin"])
                
                if st.form_submit_button("Create Account", use_container_width=True, type="primary"):
                    if not new_user or not new_pass:
                        st.error("Please fill in all fields")
                    else:
                        with st.spinner("Creating account..."):
                            response = requests.post(f"{API_URL}/auth/signup", json={"username": new_user, "password": new_pass, "role": role}, timeout=5)
                            if response.status_code in (200, 201):
                                st.success("Account created! Redirecting to login...")
                                time.sleep(1.5)
                                st.session_state.show_signup = False
                                st.rerun()
                            else:
                                st.error("Registration failed: " + safe_json(response).get("detail", "Please try again"))
            
            st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
            if st.button("Already have an account? Log in", use_container_width=True):
                st.session_state.show_signup = False
                st.rerun()

    with col2:
        st.markdown(
"""<div style="position: relative; height: 100%; z-index: 2; text-align: left;">
<h1 style="font-size: 3rem; line-height: 1.1; margin-bottom: 1rem; margin-top: 0;">Welcome to<br>Ethara portal</h1>
<p style="font-size: 1rem; font-weight: 300;">Login to access your account</p>
<div style="position: absolute; width: 350px; height: 350px; background: rgba(255,255,255,0.1); border-radius: 40% 60% 70% 30% / 40% 50% 60% 50%; top: -150px; right: -100px; z-index: -1;"></div>
<div style="position: absolute; width: 250px; height: 250px; background: rgba(255,255,255,0.08); border-radius: 50%; bottom: -50px; left: -80px; z-index: -1;"></div>
<div style="margin-top: 5rem; text-align: center;">
<svg width="280" height="220" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="opacity: 0.95;">
<rect x="3" y="3" width="18" height="18" rx="2" fill="rgba(255,255,255,0.1)" stroke="white" stroke-width="1"/>
<path d="M7 8h10M7 12h10M7 16h6" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
<circle cx="17" cy="16" r="2.5" fill="#ffffff" stroke="white" stroke-width="1"/>
<path d="M18.5 17.5l1.5 1.5" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
<rect x="-2" y="10" width="8" height="6" rx="1" fill="#7c3aed" stroke="white" stroke-width="1"/>
<circle cx="2" cy="13" r="1" fill="#ffffff"/>
</svg>
</div>
</div>""",
            unsafe_allow_html=True
        )

def dashboard_view():
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    try:
        projects_res = requests.get(f"{API_URL}/projects/", headers=headers, timeout=5)
        projects = safe_json(projects_res) if projects_res.status_code == 200 else []
    except:
        projects = []
    
    # --- HEADER ---
    st.markdown("<div style='padding-top: 1rem;'></div>", unsafe_allow_html=True)
    col_header1, col_header2, col_header3 = st.columns([3, 1, 1])
    
    with col_header1:
        st.markdown(
            f"""
            <h1 style='margin: 0; font-size: 2.2rem;'>
                Welcome, <span style='color: #a855f7 !important;'>{st.session_state.username}</span>
            </h1>
            <p style='margin: 0.2rem 0 0 0; font-size: 1rem; font-weight: 500; color: #64748b !important;'>
                {st.session_state.role} Portal • {datetime.now().strftime('%B %d, %Y')}
            </p>
            """,
            unsafe_allow_html=True
        )
    
    with col_header3:
        st.write("") 
        if st.button("Sign Out", use_container_width=True):
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.role = None
            st.rerun()
    
    st.markdown("<hr style='border: none; height: 1px; background-color: #e2e8f0; margin: 1.5rem 0;'>", unsafe_allow_html=True)
    
    # --- METRICS ---
    if projects:
        total_tasks = sum(len(p.get("tasks", [])) for p in projects)
        completed = sum(1 for p in projects for t in p.get("tasks", []) if t["status"] == "Completed")
        in_progress = sum(1 for p in projects for t in p.get("tasks", []) if t["status"] == "In Progress")
        pending = total_tasks - completed - in_progress
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Tasks", f"{total_tasks}")
        m2.metric("Pending", f"{pending}")
        m3.metric("In Progress", f"{in_progress}")
        m4.metric("Completed", f"{completed}")
        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
    
    # --- ADMIN PANEL ---
    if st.session_state.role == "Admin":
        st.markdown("<h3>Admin Controls</h3>", unsafe_allow_html=True)
        admin_col1, admin_col2 = st.columns(2)
        
        with admin_col1:
            # FIX: Moved the header inside the form so it is contained within the box
            with st.form("new_project_form"):
                st.markdown("<h4 style='margin-top:0;'>Create Project</h4>", unsafe_allow_html=True)
                p_name = st.text_input("Project Name")
                p_desc = st.text_area("Description", height=68)
                start_date = st.date_input("Start date", value=datetime.now().date())
                end_date = st.date_input("End date", value=datetime.now().date())
                if st.form_submit_button("Deploy Project", use_container_width=True, type="primary"):
                    if not p_name:
                        st.error("Project name required")
                    elif end_date < start_date:
                        st.error("End date must be the same or after start date")
                    else:
                        payload = {
                            "name": p_name,
                            "description": p_desc,
                            # send full ISO datetimes (midnight) so backend parses cleanly
                            "start_date": f"{start_date.isoformat()}T00:00:00",
                            "end_date": f"{end_date.isoformat()}T00:00:00",
                        }
                        try:
                            resp = requests.post(f"{API_URL}/projects/", json=payload, headers=headers, timeout=8)
                        except Exception as e:
                            st.error(f"Request failed: {e}")
                        else:
                            if resp.status_code in (200, 201):
                                st.success("Project created successfully")
                                st.experimental_rerun()
                            else:
                                err = safe_json(resp)
                                st.error(f"Failed to create project: {err.get('detail', resp.text)}")
            
        with admin_col2:
            # FIX: Moved the header inside the form so it is contained within the box
            if projects:
                # Fetch users for assignee dropdown
                try:
                    users_res = requests.get(f"{API_URL}/users/", headers=headers, timeout=5)
                    users = safe_json(users_res) if users_res.status_code == 200 else []
                except Exception:
                    users = []

                user_map = {u.get("username"): u.get("id") for u in users}

                with st.form("new_task_form"):
                    st.markdown("<h4 style='margin-top:0;'>Dispatch Task</h4>", unsafe_allow_html=True)
                    proj_dict = {p["name"]: p["id"] for p in projects}
                    selected_proj = st.selectbox("Select Target Project", list(proj_dict.keys()))
                    t_title = st.text_input("Task Directive")
                    if users:
                        assignee_username = st.selectbox("Assignee", list(user_map.keys()))
                        t_assignee = user_map.get(assignee_username)
                    else:
                        st.info("No users available to assign. Create users first.")
                        t_assignee = None

                    if st.form_submit_button("Dispatch to Member", use_container_width=True, type="primary"):
                        if not t_title:
                            st.error("Task directive required")
                        elif not t_assignee:
                            st.error("Select a valid assignee")
                        else:
                            proj_id = proj_dict[selected_proj]
                            payload = {"title": t_title, "assigned_to": t_assignee}
                            try:
                                resp = requests.post(f"{API_URL}/projects/{proj_id}/tasks/", json=payload, headers=headers, timeout=8)
                            except Exception as e:
                                st.error(f"Request failed: {e}")
                            else:
                                if resp.status_code in (200, 201):
                                    st.success("Task dispatched")
                                    st.experimental_rerun()
                                else:
                                    err = safe_json(resp)
                                    st.error(f"Failed to dispatch task: {err.get('detail', resp.text)}")
            else:
                with st.container():
                    st.markdown("<div class='uniform-box'><h4 style='margin-top:0;'>Dispatch Task</h4><p style='color:#64748b;'>Initialize a project first.</p></div>", unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    
    # --- WORKSPACE ---
    st.markdown("<h3>Active Workspace</h3>", unsafe_allow_html=True)
    
    if not projects:
        st.markdown("<div class='uniform-box'><p style='color:#64748b;'>Your queue is currently empty.</p></div>", unsafe_allow_html=True)
    else:
        for proj in projects:
            # Format start/end dates if available
            sd_raw = proj.get("start_date")
            ed_raw = proj.get("end_date")
            try:
                sd_text = sd_raw[:10] if sd_raw else ""
            except Exception:
                sd_text = str(sd_raw) if sd_raw else ""
            try:
                ed_text = ed_raw[:10] if ed_raw else ""
            except Exception:
                ed_text = str(ed_raw) if ed_raw else ""

            date_line = ""
            if sd_text or ed_text:
                date_line = f"<p style='margin:0.25rem 0 0 0; font-size:0.9rem; color:#475569 !important;'>Duration: {sd_text} — {ed_text}</p>"

            st.markdown(f"<div class='uniform-box' style='margin-bottom: 1rem;'><h3 style='margin:0; color:#a855f7 !important;'>{proj['name']}</h3><p style='margin:0; color:#64748b !important;'>{proj.get('description', '')}</p>{date_line}</div>", unsafe_allow_html=True)
            
            tasks = proj.get("tasks", [])
            if not tasks:
                st.info("No active directives in this project.")
                continue
            
            df = pd.DataFrame(tasks)
            df_display = pd.DataFrame({
                "ID": df["id"],
                "Directive": df["title"],
                "Status": df["status"],
                "Assignee ID": df["assigned_to"]
            })
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            st.markdown("<p style='font-weight: 600; margin-top: 1rem; color: #1e293b !important;'>Update Directive Status</p>", unsafe_allow_html=True)
            u1, u2, u3 = st.columns([1, 1.5, 1])
            with u1:
                task_id = st.number_input("Task ID", min_value=1, step=1, key=f"tid_{proj['id']}")
            with u2:
                new_status = st.selectbox("Set Status", ["Pending", "In Progress", "Completed"], key=f"stat_{proj['id']}")
            with u3:
                st.write("") 
                st.write("") 
                if st.button("Commit Status", use_container_width=True, key=f"btn_{proj['id']}", type="primary"):
                    try:
                        update_res = requests.patch(f"{API_URL}/tasks/{task_id}/status?status={new_status}", headers=headers, timeout=8)
                    except Exception as e:
                        st.error(f"Request failed: {e}")
                    else:
                        if update_res.status_code == 200:
                            st.success("Status updated")
                            st.experimental_rerun()
                        else:
                            err = safe_json(update_res)
                            st.error(f"Failed to update status: {err.get('detail', update_res.text)}")
            st.markdown("<hr style='border: none; height: 1px; background-color: #e2e8f0; margin: 2rem 0;'>", unsafe_allow_html=True)

# --- APP ROUTING ---
if st.session_state.token is None:
    login_view()
else:
    dashboard_view()