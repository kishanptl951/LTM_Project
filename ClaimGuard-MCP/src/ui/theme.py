import streamlit as st


def inject_custom_css() -> None:
    """Inject modern gradient light-theme CSS with glassmorphism on white."""
    custom_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ═══════════════════════════════════════════════════════
       GLOBAL RESET & TYPOGRAPHY
       ═══════════════════════════════════════════════════════ */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    /* ═══════════════════════════════════════════════════════
       MAIN BACKGROUND — soft warm gradient mesh
       ═══════════════════════════════════════════════════════ */
    .stApp {
        background:
            radial-gradient(ellipse at 0% 0%, rgba(124, 58, 237, 0.06) 0%, transparent 50%),
            radial-gradient(ellipse at 100% 0%, rgba(59, 130, 246, 0.06) 0%, transparent 50%),
            radial-gradient(ellipse at 60% 100%, rgba(236, 72, 153, 0.05) 0%, transparent 50%),
            linear-gradient(180deg, #F8FAFF 0%, #F1F5FE 35%, #EEF2FF 70%, #F5F3FF 100%) !important;
        color: #1E293B !important;
        min-height: 100vh;
    }

    /* ═══════════════════════════════════════════════════════
       TOP HEADER BAR
       ═══════════════════════════════════════════════════════ */
    header[data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0.72) !important;
        backdrop-filter: blur(20px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
        border-bottom: 1px solid rgba(99, 102, 241, 0.08) !important;
    }

    /* ═══════════════════════════════════════════════════════
       SIDEBAR — frosted glass on white
       ═══════════════════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8F9FF 50%, #F3F0FF 100%) !important;
        border-right: 1px solid rgba(99, 102, 241, 0.10) !important;
        box-shadow: 4px 0 24px rgba(99, 102, 241, 0.04) !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: #6366F1 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.10em !important;
        font-weight: 700 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* Sidebar radio group pills */
    [data-testid="stSidebar"] div[role="radiogroup"] {
        background: rgba(238, 242, 255, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.10);
        border-radius: 14px;
        padding: 6px;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label {
        color: #475569 !important;
        font-weight: 500 !important;
    }

    [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"],
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        color: #4F46E5 !important;
        font-weight: 700 !important;
    }

    /* ═══════════════════════════════════════════════════════
       GLASS CARDS — frosted white
       ═══════════════════════════════════════════════════════ */
    .glass-card {
        background: rgba(255, 255, 255, 0.72) !important;
        backdrop-filter: blur(20px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
        border: 1px solid rgba(99, 102, 241, 0.10) !important;
        border-radius: 20px !important;
        padding: 28px !important;
        margin-bottom: 24px !important;
        box-shadow:
            0 4px 6px -1px rgba(0, 0, 0, 0.03),
            0 10px 30px -5px rgba(99, 102, 241, 0.06),
            inset 0 1px 0 rgba(255, 255, 255, 0.8) !important;
        transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    .glass-card:hover {
        border-color: rgba(99, 102, 241, 0.22) !important;
        box-shadow:
            0 8px 20px -5px rgba(99, 102, 241, 0.10),
            0 20px 40px -10px rgba(99, 102, 241, 0.06),
            inset 0 1px 0 rgba(255, 255, 255, 0.9) !important;
        transform: translateY(-2px);
    }

    /* ═══════════════════════════════════════════════════════
       METRIC CARDS — elevated white
       ═══════════════════════════════════════════════════════ */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.85) !important;
        border: 1px solid rgba(99, 102, 241, 0.08) !important;
        border-radius: 16px !important;
        padding: 18px 22px !important;
        box-shadow:
            0 2px 8px rgba(99, 102, 241, 0.05),
            0 4px 16px rgba(0, 0, 0, 0.03) !important;
        transition: all 0.25s ease;
    }

    div[data-testid="stMetric"]:hover {
        border-color: rgba(99, 102, 241, 0.25) !important;
        transform: translateY(-3px);
        box-shadow:
            0 8px 24px rgba(99, 102, 241, 0.10),
            0 4px 16px rgba(0, 0, 0, 0.04) !important;
    }

    div[data-testid="stMetric"] label {
        color: #64748B !important;
        font-size: 0.80rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }

    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #1E293B !important;
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    /* ═══════════════════════════════════════════════════════
       PRIMARY BUTTONS — vivid gradient
       ═══════════════════════════════════════════════════════ */
    .stButton > button {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #A855F7 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 13px 28px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.02em !important;
        box-shadow:
            0 4px 14px rgba(99, 102, 241, 0.35),
            0 2px 6px rgba(139, 92, 246, 0.20) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative;
        overflow: hidden;
    }

    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0; left: -100%; right: 0; bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s ease;
    }

    .stButton > button:hover {
        box-shadow:
            0 8px 25px rgba(99, 102, 241, 0.45),
            0 4px 12px rgba(139, 92, 246, 0.30) !important;
        transform: translateY(-2px) scale(1.01) !important;
    }

    .stButton > button:hover::before {
        left: 100%;
    }

    .stButton > button:active {
        transform: translateY(0px) scale(0.99) !important;
    }

    /* Secondary / Download buttons */
    .stDownloadButton > button {
        background: rgba(255, 255, 255, 0.8) !important;
        border: 1px solid rgba(99, 102, 241, 0.18) !important;
        color: #4F46E5 !important;
        border-radius: 14px !important;
        padding: 11px 22px !important;
        font-weight: 600 !important;
        transition: all 0.25s ease !important;
        backdrop-filter: blur(8px) !important;
    }

    .stDownloadButton > button:hover {
        background: rgba(238, 242, 255, 0.9) !important;
        border-color: #6366F1 !important;
        color: #4338CA !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.15) !important;
        transform: translateY(-1px);
    }

    /* ═══════════════════════════════════════════════════════
       INPUTS — soft bordered
       ═══════════════════════════════════════════════════════ */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1.5px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 12px !important;
        color: #1E293B !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12) !important;
        background: #FFFFFF !important;
    }

    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {
        color: #94A3B8 !important;
    }

    /* Label colors */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stFileUploader label {
        color: #475569 !important;
        font-weight: 600 !important;
    }

    /* ═══════════════════════════════════════════════════════
       FILE UPLOADER — gradient dashed border
       ═══════════════════════════════════════════════════════ */
    div[data-testid="stFileUploader"] {
        background: rgba(238, 242, 255, 0.5) !important;
        border: 2px dashed rgba(99, 102, 241, 0.25) !important;
        border-radius: 18px !important;
        padding: 28px !important;
        transition: all 0.3s ease !important;
    }

    div[data-testid="stFileUploader"]:hover {
        border-color: #8B5CF6 !important;
        background: rgba(238, 242, 255, 0.7) !important;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.08) !important;
    }

    div[data-testid="stFileUploader"] small {
        color: #64748B !important;
    }

    /* ═══════════════════════════════════════════════════════
       TABS — modern pill style
       ═══════════════════════════════════════════════════════ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(255, 255, 255, 0.6);
        border-radius: 14px;
        padding: 4px;
        border: 1px solid rgba(99, 102, 241, 0.08);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        padding: 10px 18px !important;
        font-weight: 600 !important;
        color: #64748B !important;
        transition: all 0.2s ease !important;
        border: none !important;
        background: transparent !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(99, 102, 241, 0.06) !important;
        color: #4F46E5 !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25) !important;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    .stTabs [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* ═══════════════════════════════════════════════════════
       EXPANDERS — clean glass
       ═══════════════════════════════════════════════════════ */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.7) !important;
        border: 1px solid rgba(99, 102, 241, 0.10) !important;
        border-radius: 14px !important;
        color: #334155 !important;
        font-weight: 600 !important;
        padding: 14px 20px !important;
    }

    .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.5) !important;
        border: 1px solid rgba(99, 102, 241, 0.06) !important;
        border-top: none !important;
        border-bottom-left-radius: 14px !important;
        border-bottom-right-radius: 14px !important;
        padding: 18px !important;
    }

    /* ═══════════════════════════════════════════════════════
       DATAFRAMES
       ═══════════════════════════════════════════════════════ */
    div[data-testid="stDataFrame"] {
        border-radius: 14px !important;
        overflow: hidden;
        border: 1px solid rgba(99, 102, 241, 0.10) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03) !important;
    }

    /* ═══════════════════════════════════════════════════════
       SELECT BOXES
       ═══════════════════════════════════════════════════════ */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1.5px solid rgba(99, 102, 241, 0.15) !important;
        border-radius: 12px !important;
        color: #1E293B !important;
    }

    /* ═══════════════════════════════════════════════════════
       DIVIDERS
       ═══════════════════════════════════════════════════════ */
    hr {
        border-color: rgba(99, 102, 241, 0.08) !important;
    }

    /* ═══════════════════════════════════════════════════════
       BADGES & TAGS — vibrant modern pills
       ═══════════════════════════════════════════════════════ */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 14px;
        border-radius: 9999px;
        font-size: 0.73rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        transition: all 0.2s ease;
    }

    .badge-cyan {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.12) 0%, rgba(59, 130, 246, 0.10) 100%);
        color: #0891B2;
        border: 1px solid rgba(6, 182, 212, 0.25);
    }

    .badge-indigo {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(139, 92, 246, 0.10) 100%);
        color: #4F46E5;
        border: 1px solid rgba(99, 102, 241, 0.25);
    }

    .badge-emerald {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(5, 150, 105, 0.10) 100%);
        color: #059669;
        border: 1px solid rgba(16, 185, 129, 0.25);
    }

    .badge-amber {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, rgba(217, 119, 6, 0.10) 100%);
        color: #B45309;
        border: 1px solid rgba(245, 158, 11, 0.25);
    }

    .badge-rose {
        background: linear-gradient(135deg, rgba(244, 63, 94, 0.12) 0%, rgba(225, 29, 72, 0.08) 100%);
        color: #BE123C;
        border: 1px solid rgba(244, 63, 94, 0.25);
    }

    /* ═══════════════════════════════════════════════════════
       VERDICT BANNERS — light glassmorphism
       ═══════════════════════════════════════════════════════ */
    .verdict-banner-pass {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.10) 0%, rgba(52, 211, 153, 0.06) 100%);
        border: 1.5px solid rgba(16, 185, 129, 0.30);
        border-radius: 22px;
        padding: 28px;
        margin-bottom: 28px;
        box-shadow:
            0 4px 16px rgba(16, 185, 129, 0.10),
            0 8px 30px -5px rgba(16, 185, 129, 0.06);
        backdrop-filter: blur(12px);
        position: relative;
        overflow: hidden;
    }

    .verdict-banner-pass::before {
        content: '';
        position: absolute;
        top: -50%; right: -20%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(16, 185, 129, 0.08) 0%, transparent 70%);
        pointer-events: none;
    }

    .verdict-banner-review {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.10) 0%, rgba(251, 191, 36, 0.06) 100%);
        border: 1.5px solid rgba(245, 158, 11, 0.30);
        border-radius: 22px;
        padding: 28px;
        margin-bottom: 28px;
        box-shadow:
            0 4px 16px rgba(245, 158, 11, 0.10),
            0 8px 30px -5px rgba(245, 158, 11, 0.06);
        backdrop-filter: blur(12px);
        position: relative;
        overflow: hidden;
    }

    .verdict-banner-review::before {
        content: '';
        position: absolute;
        top: -50%; right: -20%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(245, 158, 11, 0.08) 0%, transparent 70%);
        pointer-events: none;
    }

    .verdict-banner-fail {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.10) 0%, rgba(244, 63, 94, 0.06) 100%);
        border: 1.5px solid rgba(239, 68, 68, 0.30);
        border-radius: 22px;
        padding: 28px;
        margin-bottom: 28px;
        box-shadow:
            0 4px 16px rgba(239, 68, 68, 0.10),
            0 8px 30px -5px rgba(239, 68, 68, 0.06);
        backdrop-filter: blur(12px);
        position: relative;
        overflow: hidden;
    }

    .verdict-banner-fail::before {
        content: '';
        position: absolute;
        top: -50%; right: -20%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(239, 68, 68, 0.08) 0%, transparent 70%);
        pointer-events: none;
    }

    /* ═══════════════════════════════════════════════════════
       CHECK ITEM RESULTS — soft colored rows
       ═══════════════════════════════════════════════════════ */
    .check-item {
        display: flex;
        align-items: flex-start;
        gap: 14px;
        padding: 14px 18px;
        border-radius: 14px;
        margin-bottom: 10px;
        font-size: 0.9rem;
        transition: all 0.2s ease;
        backdrop-filter: blur(8px);
    }

    .check-item:hover {
        transform: translateX(4px);
    }

    .check-item-pass {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(52, 211, 153, 0.04) 100%);
        border-left: 4px solid #10B981;
        color: #065F46;
    }

    .check-item-fail {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(248, 113, 113, 0.04) 100%);
        border-left: 4px solid #EF4444;
        color: #991B1B;
    }

    .check-item-review {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(251, 191, 36, 0.04) 100%);
        border-left: 4px solid #F59E0B;
        color: #92400E;
    }

    /* ═══════════════════════════════════════════════════════
       ALERTS — st.success, st.error, st.warning, st.info
       ═══════════════════════════════════════════════════════ */
    div[data-testid="stAlert"] {
        border-radius: 14px !important;
        font-weight: 500 !important;
    }

    /* ═══════════════════════════════════════════════════════
       SPINNER
       ═══════════════════════════════════════════════════════ */
    .stSpinner > div {
        color: #6366F1 !important;
    }

    /* ═══════════════════════════════════════════════════════
       SCROLLBAR — sleek thin
       ═══════════════════════════════════════════════════════ */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(241, 245, 249, 0.5);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #A5B4FC, #C4B5FD);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #818CF8, #A78BFA);
    }

    /* ═══════════════════════════════════════════════════════
       ANIMATIONS
       ═══════════════════════════════════════════════════════ */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(16px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }

    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 6px rgba(16, 185, 129, 0.4); }
        50% { box-shadow: 0 0 14px rgba(16, 185, 129, 0.7); }
    }

    .status-dot-online {
        animation: pulse-glow 2s ease-in-out infinite;
    }

    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def render_brand_header() -> None:
    """Render a vibrant modern gradient header banner."""
    header_html = """
    <div style="
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 28px; padding: 24px 28px;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.06) 0%, rgba(139, 92, 246, 0.04) 50%, rgba(236, 72, 153, 0.04) 100%);
        border: 1px solid rgba(99, 102, 241, 0.10);
        border-radius: 22px;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.06);
        animation: fadeInUp 0.5s ease-out;
    ">
        <div>
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px; flex-wrap: wrap;">
                <span class="badge-pill badge-cyan">🛡️ Enterprise Fraud Arbiter</span>
                <span class="badge-pill badge-indigo">⚡ Model Context Protocol (MCP)</span>
                <span class="badge-pill badge-emerald">👁️ Qwen2-VL Multimodal</span>
            </div>
            <h1 style="
                font-size: 2.5rem; font-weight: 900; margin: 0;
                background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 40%, #EC4899 80%, #F43F5E 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                letter-spacing: -0.03em;
                line-height: 1.1;
            ">
                ClaimGuard-MCP
            </h1>
            <p style="margin: 8px 0 0 0; color: #64748B; font-size: 1.05rem; font-weight: 400; line-height: 1.4;">
                Multimodal Insurance Claim Consistency & Fraud Arbitration Intelligence
            </p>
        </div>
        <div style="text-align: right; display: flex; flex-direction: column; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 8px; justify-content: flex-end;">
                <span class="status-dot-online" style="
                    height: 9px; width: 9px; background: #10B981; border-radius: 50%;
                    display: inline-block;
                "></span>
                <span style="font-size: 0.82rem; font-weight: 600; color: #334155;">DuckDB Engine Active</span>
            </div>
            <div style="
                font-family: 'JetBrains Mono', monospace; font-size: 0.73rem; color: #94A3B8;
                background: rgba(99, 102, 241, 0.06); padding: 4px 12px; border-radius: 8px;
            ">
                Audit Lake v1.5 • Pipeline v2.0
            </div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)


def render_verdict_card(assessment) -> None:
    """Render an eye-catching verdict hero banner with gradient accents."""
    is_pass = assessment.overall_result == "PASS"

    if is_pass:
        card_html = f"""
        <div class="verdict-banner-pass" style="animation: fadeInUp 0.4s ease-out;">
            <div style="display: flex; align-items: center; justify-content: space-between; position: relative; z-index: 1;">
                <div style="display: flex; align-items: center; gap: 18px;">
                    <div style="
                        font-size: 2.5rem;
                        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(52, 211, 153, 0.10) 100%);
                        height: 68px; width: 68px;
                        display: flex; align-items: center; justify-content: center;
                        border-radius: 18px;
                        border: 1.5px solid rgba(16, 185, 129, 0.30);
                        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.10);
                    ">
                        ✅
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                            <span class="badge-pill badge-emerald">VERDICT: PASS</span>
                            <span style="font-size: 0.85rem; color: #059669; font-family: 'JetBrains Mono', monospace; font-weight: 600;">ID: {assessment.claim_id}</span>
                        </div>
                        <h2 style="font-size: 1.55rem; font-weight: 800; color: #064E3B; margin: 0;">Claim Validated & Approved for Processing</h2>
                        <p style="margin: 6px 0 0 0; color: #047857; font-size: 0.92rem; line-height: 1.5;">
                            All cross-document consistency checks, policy period tests, expense arithmetic, and damage photos verified with zero anomalies.
                        </p>
                    </div>
                </div>
                <div style="
                    text-align: right;
                    background: linear-gradient(135deg, rgba(16, 185, 129, 0.10) 0%, rgba(52, 211, 153, 0.06) 100%);
                    padding: 14px 22px; border-radius: 16px;
                    border: 1px solid rgba(16, 185, 129, 0.20);
                ">
                    <div style="font-size: 0.72rem; text-transform: uppercase; color: #059669; font-weight: 700; letter-spacing: 0.06em;">Arbitration Status</div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #065F46; font-family: 'JetBrains Mono', monospace;">READY TO SETTLE</div>
                </div>
            </div>
        </div>
        """
    elif assessment.overall_result == "FAIL":
        reasons_count = len(assessment.reasons)
        card_html = f"""
        <div class="verdict-banner-fail" style="animation: fadeInUp 0.4s ease-out;">
            <div style="display: flex; align-items: center; justify-content: space-between; position: relative; z-index: 1;">
                <div style="display: flex; align-items: center; gap: 18px;">
                    <div style="
                        font-size: 2.5rem;
                        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(244, 63, 94, 0.10) 100%);
                        height: 68px; width: 68px;
                        display: flex; align-items: center; justify-content: center;
                        border-radius: 18px;
                        border: 1.5px solid rgba(239, 68, 68, 0.30);
                        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.10);
                    ">
                        🚫
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                            <span class="badge-pill badge-rose">VERDICT: CLAIM REJECTED</span>
                            <span style="font-size: 0.85rem; color: #DC2626; font-family: 'JetBrains Mono', monospace; font-weight: 600;">ID: {assessment.claim_id}</span>
                        </div>
                        <h2 style="font-size: 1.55rem; font-weight: 800; color: #991B1B; margin: 0;">Disqualifying Violations Detected — Auto-Rejected</h2>
                        <p style="margin: 6px 0 0 0; color: #B91C1C; font-size: 0.92rem; line-height: 1.5;">
                            Identified <strong>{reasons_count} fatal contradiction(s)</strong> or policy breaches requiring claim denial.
                        </p>
                    </div>
                </div>
                <div style="
                    text-align: right;
                    background: linear-gradient(135deg, rgba(239, 68, 68, 0.10) 0%, rgba(244, 63, 94, 0.06) 100%);
                    padding: 14px 22px; border-radius: 16px;
                    border: 1px solid rgba(239, 68, 68, 0.20);
                ">
                    <div style="font-size: 0.72rem; text-transform: uppercase; color: #DC2626; font-weight: 700; letter-spacing: 0.06em;">Arbitration Status</div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #991B1B; font-family: 'JetBrains Mono', monospace;">REJECTED</div>
                </div>
            </div>
        </div>
        """
    else:
        reasons_count = len(assessment.reasons)
        card_html = f"""
        <div class="verdict-banner-review" style="animation: fadeInUp 0.4s ease-out;">
            <div style="display: flex; align-items: center; justify-content: space-between; position: relative; z-index: 1;">
                <div style="display: flex; align-items: center; gap: 18px;">
                    <div style="
                        font-size: 2.5rem;
                        background: linear-gradient(135deg, rgba(245, 158, 11, 0.15) 0%, rgba(251, 191, 36, 0.10) 100%);
                        height: 68px; width: 68px;
                        display: flex; align-items: center; justify-content: center;
                        border-radius: 18px;
                        border: 1.5px solid rgba(245, 158, 11, 0.30);
                        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.10);
                    ">
                        ⚠️
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                            <span class="badge-pill badge-amber">VERDICT: REVIEW REQUIRED</span>
                            <span style="font-size: 0.85rem; color: #B45309; font-family: 'JetBrains Mono', monospace; font-weight: 600;">ID: {assessment.claim_id}</span>
                        </div>
                        <h2 style="font-size: 1.55rem; font-weight: 800; color: #78350F; margin: 0;">Discrepancies Detected — Needs Human Adjuster</h2>
                        <p style="margin: 6px 0 0 0; color: #92400E; font-size: 0.92rem; line-height: 1.5;">
                            Identified <strong>{reasons_count} attention point(s)</strong> across policy validity, document consistency, damage correlation, or required files.
                        </p>
                    </div>
                </div>
                <div style="
                    text-align: right;
                    background: linear-gradient(135deg, rgba(245, 158, 11, 0.10) 0%, rgba(251, 191, 36, 0.06) 100%);
                    padding: 14px 22px; border-radius: 16px;
                    border: 1px solid rgba(245, 158, 11, 0.20);
                ">
                    <div style="font-size: 0.72rem; text-transform: uppercase; color: #B45309; font-weight: 700; letter-spacing: 0.06em;">Attention Flags</div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #78350F; font-family: 'JetBrains Mono', monospace;">{reasons_count} FLAGGED</div>
                </div>
            </div>
        </div>
        """
    st.markdown(card_html, unsafe_allow_html=True)


def render_check_item(rule_id: str, explanation: str, result: str) -> None:
    """Render a styled item for evaluation and invariant lists."""
    status_class = (
        "check-item-pass"
        if result == "PASS"
        else ("check-item-fail" if result == "FAIL" else "check-item-review")
    )
    icon = "✅" if result == "PASS" else ("❌" if result == "FAIL" else "⚠️")
    badge_class = (
        "badge-emerald"
        if result == "PASS"
        else ("badge-rose" if result == "FAIL" else "badge-amber")
    )

    html = f"""
    <div class="check-item {status_class}">
        <div style="font-size: 1.15rem; line-height: 1.2;">{icon}</div>
        <div style="flex-grow: 1;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-weight: 700; color: #1E293B; font-size: 0.93rem; font-family: 'JetBrains Mono', monospace;">{rule_id}</span>
                <span class="badge-pill {badge_class}">{result}</span>
            </div>
            <div style="color: #475569; font-size: 0.88rem; line-height: 1.5;">{explanation}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_financial_dossier(fin) -> None:
    """Render a comprehensive financial breakdown card with gradient accents."""
    if not fin:
        return

    repair_cost = getattr(fin, "repair_cost", None)
    cov_limit = getattr(fin, "coverage_limit", None)
    deductible = getattr(fin, "deductible", None)
    payable = getattr(fin, "estimated_payable", None)

    if repair_cost is None and cov_limit is None:
        return

    if repair_cost is not None and cov_limit is not None and cov_limit > 0:
        cov_pct = min(100.0, max(0.0, (repair_cost / cov_limit * 100)))
        badge_text = f"Coverage Consumed: {cov_pct:.1f}%"
    else:
        cov_pct = 0.0
        badge_text = "Coverage Consumed: N/A"

    repair_str = f"₹{repair_cost:,.2f}" if repair_cost is not None else "Not Specified"
    limit_str = f"₹{cov_limit:,.2f}" if cov_limit is not None else "Not Specified"
    deduct_str = f"- ₹{deductible:,.2f}" if deductible is not None else "₹0.00"
    payable_str = f"₹{payable:,.2f}" if payable is not None else "Pending"

    html = f"""
    <div class="glass-card" style="margin-top: 18px; animation: fadeInUp 0.5s ease-out;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.3rem;">💳</span>
                <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #1E293B;">Settlement & Coverage Breakdown</h3>
            </div>
            <span class="badge-pill badge-indigo">{badge_text}</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;">
            <div style="
                background: linear-gradient(135deg, rgba(59, 130, 246, 0.06) 0%, rgba(99, 102, 241, 0.04) 100%);
                padding: 16px; border-radius: 14px;
                border: 1px solid rgba(59, 130, 246, 0.12);
            ">
                <div style="color: #64748B; font-size: 0.76rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">Declared Repair Cost</div>
                <div style="font-size: 1.3rem; font-weight: 800; color: #2563EB; font-family: 'JetBrains Mono', monospace; margin-top: 6px;">{repair_str}</div>
            </div>
            <div style="
                background: linear-gradient(135deg, rgba(99, 102, 241, 0.06) 0%, rgba(139, 92, 246, 0.04) 100%);
                padding: 16px; border-radius: 14px;
                border: 1px solid rgba(99, 102, 241, 0.12);
            ">
                <div style="color: #64748B; font-size: 0.76rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">Policy Limit</div>
                <div style="font-size: 1.3rem; font-weight: 800; color: #6366F1; font-family: 'JetBrains Mono', monospace; margin-top: 6px;">{limit_str}</div>
            </div>
            <div style="
                background: linear-gradient(135deg, rgba(245, 158, 11, 0.06) 0%, rgba(251, 191, 36, 0.04) 100%);
                padding: 16px; border-radius: 14px;
                border: 1px solid rgba(245, 158, 11, 0.12);
            ">
                <div style="color: #64748B; font-size: 0.76rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">Deductible (Excess)</div>
                <div style="font-size: 1.3rem; font-weight: 800; color: #D97706; font-family: 'JetBrains Mono', monospace; margin-top: 6px;">{deduct_str}</div>
            </div>
            <div style="
                background: linear-gradient(135deg, rgba(16, 185, 129, 0.10) 0%, rgba(52, 211, 153, 0.06) 100%);
                padding: 16px; border-radius: 14px;
                border: 1.5px solid rgba(16, 185, 129, 0.25);
                box-shadow: 0 2px 8px rgba(16, 185, 129, 0.06);
            ">
                <div style="color: #059669; font-size: 0.76rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">Net Payable to Insured</div>
                <div style="font-size: 1.3rem; font-weight: 800; color: #059669; font-family: 'JetBrains Mono', monospace; margin-top: 6px;">{payable_str}</div>
            </div>
        </div>
        <div style="margin-top: 18px; background: rgba(241, 245, 249, 0.7); border-radius: 9999px; height: 10px; overflow: hidden; border: 1px solid rgba(99, 102, 241, 0.08);">
            <div style="
                background: linear-gradient(90deg, #6366F1, #8B5CF6, #A855F7);
                width: {cov_pct}%; height: 100%;
                border-radius: 9999px;
                transition: width 1s ease;
                box-shadow: 0 0 8px rgba(99, 102, 241, 0.3);
            "></div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_sidebar_status() -> None:
    """Render system health badges in the sidebar."""
    html = """
    <div style="
        background: linear-gradient(135deg, rgba(238, 242, 255, 0.7) 0%, rgba(243, 240, 255, 0.5) 100%);
        border: 1px solid rgba(99, 102, 241, 0.10);
        border-radius: 14px;
        padding: 16px;
        margin-top: 18px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
    ">
        <div style="font-size: 0.70rem; font-weight: 700; color: #6366F1; text-transform: uppercase; letter-spacing: 0.10em; margin-bottom: 10px;">
            Service Health Status
        </div>
        <div style="display: flex; flex-direction: column; gap: 8px; font-size: 0.82rem;">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="color: #334155; font-weight: 500;">DuckDB Lake</span>
                <span class="badge-pill badge-emerald" style="padding: 2px 10px; font-size: 0.66rem;">Online</span>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="color: #334155; font-weight: 500;">MCP Servers</span>
                <span class="badge-pill badge-indigo" style="padding: 2px 10px; font-size: 0.66rem;">4 Tools</span>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="color: #334155; font-weight: 500;">Vision Model</span>
                <span class="badge-pill badge-cyan" style="padding: 2px 10px; font-size: 0.66rem;">Qwen2-VL</span>
            </div>
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="color: #334155; font-weight: 500;">OCR Engine</span>
                <span class="badge-pill badge-emerald" style="padding: 2px 10px; font-size: 0.66rem;">Active</span>
            </div>
        </div>
    </div>
    """
    st.sidebar.markdown(html, unsafe_allow_html=True)
