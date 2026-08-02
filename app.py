import streamlit as st
import pandas as pd
import os
import uuid
import time
import json

from AgentM.workflow import workflow
from AgentM.utils.utils import file_handler, metrics, load_csv_safely

# ─────────────────────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgentM · AI Data Cleaner",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# Custom CSS (Light Theme Optimized)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Import fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── Global ── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Hide default Streamlit clutter while keeping sidebar reopen button visible ── */
    #MainMenu, footer { visibility: hidden; }
    header, [data-testid="stHeader"] {
        background: transparent !important;
    }
    [data-testid="collapsedControl"], [data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        display: flex !important;
        z-index: 999999 !important;
    }

    /* ── Pipeline tracker ── */
    .pipeline-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0;
        margin: 1.5rem 0 2rem 0;
        flex-wrap: wrap;
    }
    .agent-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 110px;
        position: relative;
    }
    .agent-icon {
        width: 54px; height: 54px;
        border-radius: 16px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.4rem;
        transition: all 0.3s ease;
        position: relative;
        z-index: 2;
    }
    .agent-label {
        margin-top: 8px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.01em;
        text-align: center;
    }

    /* States */
    .step-pending .agent-icon {
        background: #F3F4F6;
        border: 2px solid #E5E7EB;
        color: #9CA3AF;
    }
    .step-pending .agent-label { color: #9CA3AF; }

    .step-active .agent-icon {
        background: linear-gradient(135deg, #4F46E5, #7C3AED);
        border: 2px solid #6366F1;
        color: #FFFFFF;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);
        animation: pulse-glow 2s ease-in-out infinite;
    }
    .step-active .agent-label { color: #4F46E5; font-weight: 700; }

    .step-done .agent-icon {
        background: #DCFCE7;
        border: 2px solid #86EFAC;
        color: #16A34A;
    }
    .step-done .agent-label { color: #16A34A; font-weight: 600; }

    .step-error .agent-icon {
        background: #FEE2E2;
        border: 2px solid #FCA5A5;
        color: #DC2626;
    }
    .step-error .agent-label { color: #DC2626; font-weight: 600; }

    .step-waiting .agent-icon {
        background: #FEF3C7;
        border: 2px solid #FDE68A;
        color: #D97706;
        animation: pulse-glow-amber 2s ease-in-out infinite;
    }
    .step-waiting .agent-label { color: #D97706; font-weight: 700; }

    /* Connector line */
    .connector {
        width: 36px; height: 3px;
        background: #E5E7EB;
        margin-bottom: 26px;
        border-radius: 2px;
    }
    .connector-done {
        background: #22C55E;
    }
    .connector-active {
        background: linear-gradient(90deg, #22C55E, #4F46E5);
    }

    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 12px rgba(79, 70, 229, 0.3); }
        50% { box-shadow: 0 0 22px rgba(79, 70, 229, 0.55); }
    }
    @keyframes pulse-glow-amber {
        0%, 100% { box-shadow: 0 0 10px rgba(217, 119, 6, 0.25); }
        50% { box-shadow: 0 0 20px rgba(217, 119, 6, 0.45); }
    }

    /* ── Metric cards ── */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #4F46E5;
        line-height: 1.2;
    }
    .metric-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 4px;
    }
    .metric-delta {
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 4px;
    }
    .delta-good { color: #16A34A; }
    .delta-neutral { color: #6B7280; }

    /* ── Section headers ── */
    .section-header {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #6B7280;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #E5E7EB;
    }

    /* ── Hero title ── */
    .hero-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E1B4B;
        margin-bottom: 0.25rem;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        text-align: center;
        font-size: 0.95rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }

    /* ── Review card ── */
    .review-card {
        background: #FFFBEB;
        border: 1px solid #FDE68A;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    /* ── Success banner ── */
    .success-banner {
        background: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-radius: 16px;
        padding: 1.5rem 2rem;
        text-align: center;
        margin: 1rem 0;
    }

    /* ── Failure banner ── */
    .failure-banner {
        background: #FEF2F2;
        border: 1px solid #FECACA;
        border-radius: 16px;
        padding: 1.5rem 2rem;
        text-align: center;
        margin: 1rem 0;
    }

    /* ── Button overrides ── */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        letter-spacing: 0.01em;
        transition: all 0.3s ease;
    }

    /* ── Active Config Summary ── */
    .active-config-card {
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 0.85rem 1.25rem;
        margin-bottom: 1.25rem;
        font-size: 0.9rem;
        color: #374151;
        display: flex;
        align-items: center;
        gap: 1.5rem;
        flex-wrap: wrap;
    }
    .config-tag {
        background: #EEF2FF;
        color: #4F46E5;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.82rem;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Pipeline Step Definitions
# ─────────────────────────────────────────────────────────────
PIPELINE_STEPS = [
    {"id": "upload",       "icon": "📤", "label": "Upload"},
    {"id": "profile",      "icon": "🔍", "label": "Profiler"},
    {"id": "coder",        "icon": "💻", "label": "Coder"},
    {"id": "ai_review",    "icon": "🛡️", "label": "Reviewer"},
    {"id": "human_review", "icon": "👤", "label": "Review"},
    {"id": "code_execute", "icon": "⚡", "label": "Executor"},
    {"id": "done",         "icon": "✅", "label": "Done"},
]


def render_pipeline_tracker(active_step_id, step_states=None):
    """Render the horizontal pipeline progress tracker.
    
    step_states: dict mapping step id -> 'pending' | 'active' | 'done' | 'error' | 'waiting'
    """
    if step_states is None:
        step_states = {}

    html_parts = ['<div class="pipeline-container">']

    for i, step in enumerate(PIPELINE_STEPS):
        state = step_states.get(step["id"], "pending")

        # Auto-compute states if not explicitly set
        if state == "pending" and active_step_id:
            step_idx = next((j for j, s in enumerate(PIPELINE_STEPS) if s["id"] == active_step_id), -1)
            curr_idx = i
            if curr_idx < step_idx:
                state = "done"
            elif curr_idx == step_idx:
                state = "active"

        html_parts.append(f'''
            <div class="agent-step step-{state}">
                <div class="agent-icon">{step["icon"]}</div>
                <div class="agent-label">{step["label"]}</div>
            </div>
        ''')

        # Connector between steps
        if i < len(PIPELINE_STEPS) - 1:
            step_idx = next((j for j, s in enumerate(PIPELINE_STEPS) if s["id"] == active_step_id), -1) if active_step_id else -1
            if i < step_idx - 1:
                conn_class = "connector connector-done"
            elif i == step_idx - 1:
                conn_class = "connector connector-active"
            else:
                conn_class = "connector"
            html_parts.append(f'<div class="{conn_class}"></div>')

    html_parts.append('</div>')
    st.markdown("".join(html_parts), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Session State Init
# ─────────────────────────────────────────────────────────────
# Session State Init
# ─────────────────────────────────────────────────────────────
DEFAULTS = {
    "pipeline_phase": "upload",     # upload | running | human_review | complete | failed
    "thread_id": None,
    "run_timestamp": None,
    "active_user_instruction": "",
    "dataset_path": None,
    "step_states": {},
    "active_step": "upload",
    "agent_logs": [],
    "generated_code": None,
    "review_result": None,
    "final_state": None,
    "retry_count": 0,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)


def save_run_log():
    """Save or update current run log file in logs/."""
    thread_id = st.session_state.get("thread_id")
    if not thread_id:
        return
    log_file = os.path.join(LOGS_DIR, f"run_{thread_id}.json")
    dataset_path = st.session_state.get("dataset_path", "")
    dataset_name = os.path.basename(dataset_path) if dataset_path else "Dataset"
    
    run_data = {
        "thread_id": thread_id,
        "timestamp": st.session_state.get("run_timestamp", time.strftime("%Y-%m-%d %H:%M:%S")),
        "dataset_name": dataset_name,
        "user_instruction": st.session_state.get("active_user_instruction", ""),
        "pipeline_phase": st.session_state.get("pipeline_phase", "upload"),
        "logs": st.session_state.get("agent_logs", []),
    }
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(run_data, f, indent=2)
    except Exception:
        pass


def load_all_run_logs():
    """Load metadata of all saved run logs sorted by timestamp descending."""
    runs = []
    if os.path.exists(LOGS_DIR):
        for fname in os.listdir(LOGS_DIR):
            if fname.startswith("run_") and fname.endswith(".json"):
                fpath = os.path.join(LOGS_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        runs.append(data)
                except Exception:
                    pass
    runs.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return runs


def log(icon, message):
    """Append a timestamped log entry and persist."""
    st.session_state.agent_logs.append({
        "time": time.strftime("%H:%M:%S"),
        "icon": icon,
        "message": message,
    })
    save_run_log()


def set_step(step_id, state="active"):
    """Update the pipeline tracker."""
    # Mark everything before this step as done
    found = False
    for s in PIPELINE_STEPS:
        if s["id"] == step_id:
            found = True
            st.session_state.step_states[s["id"]] = state
        elif not found:
            st.session_state.step_states[s["id"]] = "done"
    st.session_state.active_step = step_id


# ─────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">🧬 AgentM</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Multi-agent AI pipeline for automated dataset cleaning</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Main Middle Area: Upload Dataset & Cleaning Instructions
# ─────────────────────────────────────────────────────────────
start_btn = False

uploaded_file = st.session_state.get("main_uploaded_file")
user_instruction = st.session_state.get("main_user_instruction", "")

if st.session_state.pipeline_phase == "upload":
    st.markdown('<div class="section-header">📥 Dataset & Cleaning Setup</div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        col_up, col_inst = st.columns([1, 1], gap="medium")
        
        with col_up:
            st.markdown("##### 📂 Upload Dataset")
            main_file_val = st.file_uploader(
                "Upload a CSV file",
                type=["csv"],
                help="Drag & drop or click to browse",
                key="main_uploaded_file",
                label_visibility="collapsed",
            )
            if main_file_val is not None:
                uploaded_file = main_file_val

        with col_inst:
            st.markdown("##### 🎯 Cleaning Instructions")
            main_inst_val = st.text_area(
                "Cleaning Instructions",
                placeholder="e.g. Remove duplicates, fill missing ages with median, standardize column names...",
                height=110,
                key="main_user_instruction",
                label_visibility="collapsed",
            )
            if main_inst_val:
                user_instruction = main_inst_val

        st.markdown("")
        start_btn = st.button(
            "🚀 Start Cleaning",
            use_container_width=True,
            disabled=(uploaded_file is None or st.session_state.pipeline_phase == "running"),
            type="primary",
            key="main_start_btn",
        )

else:
    # Summary card when pipeline is running/review/complete
    dataset_name = os.path.basename(st.session_state.dataset_path) if st.session_state.dataset_path else "Dataset"
    active_inst = st.session_state.get("active_user_instruction", "") or user_instruction or "Standard Cleaning"
    st.markdown(f'''
    <div class="active-config-card">
        <div>📁 <b>Active Dataset:</b> <span class="config-tag">{dataset_name}</span></div>
        <div>🎯 <b>Instructions:</b> {active_inst}</div>
    </div>
    ''', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Pipeline Tracker (Below Upload & Cleaning Instructions)
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">⚙️ Pipeline Tracker</div>', unsafe_allow_html=True)
render_pipeline_tracker(st.session_state.active_step, st.session_state.step_states)


# ─────────────────────────────────────────────────────────────
# Sidebar — Log Viewer & Run History
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📋 Agent Logs & History")
    
    if st.session_state.pipeline_phase != "upload":
        if st.button("➕ Start New Cleaning Run", use_container_width=True, type="primary"):
            for k, v in DEFAULTS.items():
                st.session_state[k] = v if not isinstance(v, (list, dict)) else type(v)()
            st.rerun()
        st.divider()

    st.markdown("##### 📜 Select Pipeline Run Log")
    
    all_runs = load_all_run_logs()
    current_id = st.session_state.get("thread_id")
    
    options = []
    run_options_map = {}
    
    if current_id:
        curr_ds = os.path.basename(st.session_state.dataset_path) if st.session_state.dataset_path else "Current Dataset"
        curr_phase = st.session_state.pipeline_phase
        curr_label = f"⚡ Active Run — {curr_ds}"
        options.append(curr_label)
        run_options_map[curr_label] = {
            "is_active": True,
            "dataset_name": curr_ds,
            "user_instruction": st.session_state.get("active_user_instruction", ""),
            "pipeline_phase": curr_phase,
            "logs": st.session_state.agent_logs,
        }

    for run in all_runs:
        if current_id and run.get("thread_id") == current_id:
            continue
        ts = run.get("timestamp", "")
        ds = run.get("dataset_name", "Dataset")
        ph = run.get("pipeline_phase", "done")
        label = f"🗓️ {ts} — {ds} ({ph})"
        options.append(label)
        run_options_map[label] = run

    if not options:
        st.caption("No log history saved yet.")
    else:
        selected_option = st.selectbox(
            "Select Run",
            options=options,
            index=0,
            key="run_log_selector",
            label_visibility="collapsed",
        )
        
        selected_run = run_options_map.get(selected_option)
        if selected_run:
            st.markdown(f"**Dataset:** `{selected_run.get('dataset_name', 'N/A')}`")
            st.markdown(f"**Instructions:** {selected_run.get('user_instruction') or '*Standard cleaning*'}")
            st.markdown(f"**Status:** `{selected_run.get('pipeline_phase', 'unknown')}`")
            
            st.markdown("---")
            log_container = st.container(height=320)
            with log_container:
                logs_to_show = selected_run.get("logs", [])
                if not logs_to_show:
                    st.caption("No log entries recorded for this run.")
                else:
                    for entry in reversed(logs_to_show):
                        st.markdown(f"`{entry['time']}` {entry['icon']} {entry['message']}")


# ─────────────────────────────────────────────────────────────
# PHASE: Upload Preview
# ─────────────────────────────────────────────────────────────
if st.session_state.pipeline_phase == "upload":
    if uploaded_file and not start_btn:
        # Preview the uploaded file
        st.markdown('<div class="section-header">📊 Dataset Preview</div>', unsafe_allow_html=True)
        try:
            preview_df = load_csv_safely(uploaded_file)
            uploaded_file.seek(0)  # Reset for later use

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f'''<div class="metric-card">
                    <div class="metric-value">{preview_df.shape[0]:,}</div>
                    <div class="metric-label">Rows</div>
                </div>''', unsafe_allow_html=True)
            with col2:
                st.markdown(f'''<div class="metric-card">
                    <div class="metric-value">{preview_df.shape[1]}</div>
                    <div class="metric-label">Columns</div>
                </div>''', unsafe_allow_html=True)
            with col3:
                st.markdown(f'''<div class="metric-card">
                    <div class="metric-value">{int(preview_df.isnull().sum().sum()):,}</div>
                    <div class="metric-label">Null Values</div>
                </div>''', unsafe_allow_html=True)
            with col4:
                st.markdown(f'''<div class="metric-card">
                    <div class="metric-value">{int(preview_df.duplicated().sum()):,}</div>
                    <div class="metric-label">Duplicates</div>
                </div>''', unsafe_allow_html=True)

            st.markdown("")
            st.dataframe(preview_df.head(10), use_container_width=True, height=300)
        except Exception as e:
            st.error(f"Could not preview file: {e}")


# ─────────────────────────────────────────────────────────────
# PHASE: Start Pipeline
# ─────────────────────────────────────────────────────────────
if start_btn and uploaded_file:
    # Save uploaded file to disk
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    dataset_path = os.path.join(upload_dir, uploaded_file.name)
    with open(dataset_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.session_state.dataset_path = dataset_path
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.run_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.active_user_instruction = user_instruction or ""
    st.session_state.pipeline_phase = "running"
    st.session_state.agent_logs = []
    st.session_state.retry_count = 0

    config = {
        "configurable": {"thread_id": st.session_state.thread_id},
        "run_name": "AgentM Data Cleaning Pipeline",
        "tags": ["AgentM", "Streamlit", "DataCleaner"],
        "metadata": {
            "thread_id": st.session_state.thread_id,
            "dataset_name": uploaded_file.name,
        },
    }

    initial_state = {
        "dataset_path": dataset_path,
        "user_instruction": user_instruction or "",
        "python_code": "",
        "clean_plan": "",
        "errors": [],
        "retry_count": 0,
        "is_cleaned": False,
        "clean_path": "",
        "review_safe": True,
        "human_approved": False,
    }

    log("📤", f"Uploaded **{uploaded_file.name}**")
    set_step("upload", "done")

    # ── Run the graph until it hits interrupt_before ──
    agent_names = {
        "profile":      ("🔍", "Profiler — Analyzing dataset"),
        "coder":        ("💻", "Coder — Generating cleaning code"),
        "ai_review":    ("🛡️", "Reviewer — Reviewing code safety"),
        "human_review": ("👤", "Human Review — Awaiting your approval"),
        "code_execute": ("⚡", "Executor — Running transformation"),
    }

    status_placeholder = st.empty()

    with status_placeholder.status("🧬 Running AgentM pipeline…", expanded=True) as status:
        try:
            for event in workflow.stream(initial_state, config, stream_mode="updates"):
                for node_name, node_output in event.items():
                    if node_name in agent_names:
                        icon, desc = agent_names[node_name]
                        st.write(f"{icon}  {desc}")
                        log(icon, desc.split(" — ")[1] if " — " in desc else desc)
                        set_step(node_name, "done")

                        # Capture specific outputs
                        if node_name == "coder":
                            st.session_state.generated_code = node_output.get("python_code", "")

                        if node_name == "ai_review":
                            safe = node_output.get("review_safe", True)
                            errs = node_output.get("errors", [])
                            if not safe:
                                log("🚨", f"Security VETO: {errs[-1] if errs else 'Unknown'}")
                                set_step("ai_review", "error")

            # If we get here, the graph is paused (interrupt_before human_review)
            set_step("human_review", "waiting")
            log("⏸️", "Pipeline paused — waiting for your review")
            status.update(label="⏸️ Awaiting human review", state="complete")
            st.session_state.pipeline_phase = "human_review"

        except Exception as e:
            status.update(label="❌ Pipeline error", state="error")
            log("❌", f"Error: {str(e)}")
            st.session_state.pipeline_phase = "failed"
            st.session_state.step_states[st.session_state.active_step] = "error"

    st.rerun()


# ─────────────────────────────────────────────────────────────
# PHASE: Human Review
# ─────────────────────────────────────────────────────────────
if st.session_state.pipeline_phase == "human_review":
    st.markdown('<div class="section-header">👤 Human Review Gate</div>', unsafe_allow_html=True)

    st.markdown('''
    <div class="review-card">
        <span style="font-size:1.2rem;">⏸️</span>
        <span style="font-weight:700; color:#B45309;"> Pipeline paused</span>
        <span style="color:#4B5563;"> — Review the generated code before execution</span>
    </div>
    ''', unsafe_allow_html=True)

    # Show the generated code
    if st.session_state.generated_code:
        with st.expander("🔍 View Generated Code", expanded=True):
            st.code(st.session_state.generated_code, language="python", line_numbers=True)

    col1, col2 = st.columns(2)

    with col1:
        approve_btn = st.button("✅ Approve & Execute", use_container_width=True, type="primary")
    with col2:
        reject_btn = st.button("❌ Reject & Regenerate", use_container_width=True)

    if approve_btn or reject_btn:
        config = {"configurable": {"thread_id": st.session_state.thread_id}}

        if approve_btn:
            log("✅", "Code **approved** — resuming execution")
            # Update state with human_approved = True, then resume
            workflow.update_state(config, {"human_approved": True}, as_node="human_review")
        else:
            log("❌", "Code **rejected** — sending back to Coder")
            workflow.update_state(config, {"human_approved": False}, as_node="human_review")

        st.session_state.pipeline_phase = "running_post_review"
        st.rerun()


# ─────────────────────────────────────────────────────────────
# PHASE: Post-Review Execution
# ─────────────────────────────────────────────────────────────
if st.session_state.pipeline_phase == "running_post_review":
    config = {
        "configurable": {"thread_id": st.session_state.thread_id},
        "run_name": "AgentM Post-Review Execution",
        "tags": ["AgentM", "Streamlit", "DataCleaner", "PostReview"],
        "metadata": {
            "thread_id": st.session_state.thread_id,
        },
    }

    agent_names = {
        "profile":      ("🔍", "Profiler — Re-analyzing dataset"),
        "coder":        ("💻", "Coder — Regenerating cleaning code"),
        "ai_review":    ("🛡️", "Reviewer — Re-reviewing code"),
        "human_review": ("👤", "Human Review — Awaiting your approval"),
        "code_execute": ("⚡", "Executor — Running transformation"),
    }

    status_placeholder = st.empty()
    hit_interrupt = False

    with status_placeholder.status("🧬 Resuming pipeline…", expanded=True) as status:
        try:
            for event in workflow.stream(None, config, stream_mode="updates"):
                for node_name, node_output in event.items():
                    if node_name in agent_names:
                        icon, desc = agent_names[node_name]
                        st.write(f"{icon}  {desc}")
                        log(icon, desc.split(" — ")[1] if " — " in desc else desc)
                        set_step(node_name, "done")

                        if node_name == "coder":
                            st.session_state.generated_code = node_output.get("python_code", "")

                        if node_name == "ai_review":
                            safe = node_output.get("review_safe", True)
                            if not safe:
                                log("🚨", "Security flagged the code again")
                                set_step("ai_review", "error")

                        if node_name == "code_execute":
                            cleaned = node_output.get("is_cleaned", False)
                            retry = node_output.get("retry_count", 0)
                            st.session_state.retry_count = retry
                            if cleaned:
                                log("🎉", "Cleaning **successful**!")
                            else:
                                errs = node_output.get("errors", [])
                                err_short = errs[-1].splitlines()[-1] if errs else "Unknown error"
                                log("⚠️", f"Execution failed (retry {retry}/3): {err_short}")

            # Check if we hit another interrupt (looped back through coder → review → human_review)
            snapshot = workflow.get_state(config)
            if snapshot.next and "human_review" in snapshot.next:
                hit_interrupt = True
                set_step("human_review", "waiting")
                log("⏸️", "Pipeline paused again — new code needs review")
                status.update(label="⏸️ Awaiting human review", state="complete")
                st.session_state.pipeline_phase = "human_review"
            else:
                # Pipeline finished
                final_state = snapshot.values
                st.session_state.final_state = final_state

                if final_state.get("is_cleaned"):
                    set_step("done", "done")
                    status.update(label="✅ Cleaning complete!", state="complete")
                    st.session_state.pipeline_phase = "complete"
                    log("✅", "Pipeline finished — dataset cleaned successfully")
                else:
                    retry = final_state.get("retry_count", 0)
                    if retry >= 3:
                        set_step("code_execute", "error")
                        status.update(label="🛑 Circuit breaker triggered", state="error")
                        st.session_state.pipeline_phase = "failed"
                        log("🛑", f"Circuit breaker — failed after {retry} retries")
                    else:
                        set_step("done", "done")
                        status.update(label="⚠️ Pipeline ended", state="complete")
                        st.session_state.pipeline_phase = "complete"

        except Exception as e:
            status.update(label="❌ Pipeline error", state="error")
            log("❌", f"Error: {str(e)}")
            st.session_state.pipeline_phase = "failed"

    st.rerun()


# ─────────────────────────────────────────────────────────────
# PHASE: Complete — Show Results
# ─────────────────────────────────────────────────────────────
if st.session_state.pipeline_phase == "complete":
    st.markdown('''
    <div class="success-banner">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">🎉</div>
        <div style="font-size:1.3rem; font-weight:700; color:#15803D;">Dataset Cleaned Successfully</div>
        <div style="color:#4B5563; margin-top:0.25rem;">Your data has been processed by the AgentM pipeline</div>
    </div>
    ''', unsafe_allow_html=True)

    dataset_path = st.session_state.dataset_path or ""
    orig_filename = os.path.basename(dataset_path) if dataset_path else "data.csv"
    download_filename = f"cleaned_{orig_filename}"

    cleaned_path = st.session_state.final_state.get("clean_path") if st.session_state.final_state else None
    if not cleaned_path or not os.path.exists(cleaned_path):
        cleaned_path = os.path.join("outputs", download_filename).replace("\\", "/")

    # ── Before / After Metrics ──
    if dataset_path and os.path.exists(cleaned_path):
        m = metrics(st.session_state.dataset_path, cleaned_path)

        if m:
            st.markdown('<div class="section-header">📊 Before → After Comparison</div>', unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                delta = m["delta"]["rows_removed"]
                delta_class = "delta-good" if delta > 0 else "delta-neutral"
                st.markdown(f'''<div class="metric-card">
                    <div class="metric-value">{m["cleaned"]["rows"]:,}</div>
                    <div class="metric-label">Rows</div>
                    <div class="metric-delta {delta_class}">{"−" if delta > 0 else ""}{abs(delta):,} removed</div>
                </div>''', unsafe_allow_html=True)

            with col2:
                delta = m["delta"]["columns_added"]
                st.markdown(f'''<div class="metric-card">
                    <div class="metric-value">{m["cleaned"]["cols"]}</div>
                    <div class="metric-label">Columns</div>
                    <div class="metric-delta delta-neutral">{"+" if delta > 0 else ""}{delta} changed</div>
                </div>''', unsafe_allow_html=True)

            with col3:
                delta = m["delta"]["nulls_fixed"]
                delta_class = "delta-good" if delta > 0 else "delta-neutral"
                st.markdown(f'''<div class="metric-card">
                    <div class="metric-value">{m["cleaned"]["nulls"]:,}</div>
                    <div class="metric-label">Nulls Remaining</div>
                    <div class="metric-delta {delta_class}">{delta:,} fixed</div>
                </div>''', unsafe_allow_html=True)

            with col4:
                delta = m["delta"]["duplicates_removed"]
                delta_class = "delta-good" if delta > 0 else "delta-neutral"
                st.markdown(f'''<div class="metric-card">
                    <div class="metric-value">{m["cleaned"]["duplicates"]:,}</div>
                    <div class="metric-label">Duplicates</div>
                    <div class="metric-delta {delta_class}">{delta:,} removed</div>
                </div>''', unsafe_allow_html=True)

        # ── Cleaned Data Preview ──
        st.markdown("")
        st.markdown('<div class="section-header">🔎 Cleaned Dataset Preview</div>', unsafe_allow_html=True)

        cleaned_df = load_csv_safely(cleaned_path)
        st.dataframe(cleaned_df.head(20), use_container_width=True, height=350)

        # ── Download ──
        st.markdown("")
        with open(cleaned_path, "rb") as f:
            st.download_button(
                label="📥 Download Cleaned Dataset",
                data=f,
                file_name=download_filename,
                mime="text/csv",
                use_container_width=True,
                type="primary",
            )

    # ── Show final code ──
    if st.session_state.generated_code:
        with st.expander("🔍 Final Cleaning Code"):
            st.code(st.session_state.generated_code, language="python", line_numbers=True)


# ─────────────────────────────────────────────────────────────
# PHASE: Failed
# ─────────────────────────────────────────────────────────────
if st.session_state.pipeline_phase == "failed":
    retry_count = st.session_state.retry_count

    st.markdown(f'''
    <div class="failure-banner">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">🛑</div>
        <div style="font-size:1.3rem; font-weight:700; color:#B91C1C;">Pipeline Failed</div>
        <div style="color:#4B5563; margin-top:0.25rem;">
            {"Circuit breaker triggered after 3 failed attempts" if retry_count >= 3 else "An error occurred during processing"}
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Show error log
    error_logs = [l for l in st.session_state.agent_logs if "❌" in l["icon"] or "🛑" in l["icon"] or "⚠️" in l["icon"]]
    if error_logs:
        st.markdown('<div class="section-header">🔴 Error Details</div>', unsafe_allow_html=True)
        for entry in error_logs:
            st.markdown(f"`{entry['time']}` {entry['icon']} {entry['message']}")

    if st.session_state.generated_code:
        with st.expander("🔍 Last Generated Code"):
            st.code(st.session_state.generated_code, language="python", line_numbers=True)
