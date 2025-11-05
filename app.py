import streamlit as st
from PIL import Image
from io import BytesIO
import base64
import re
import io


# --- Import price fetcher ---
try:
    from price_fetcher import get_price
except ImportError as e:
    st.error(f"⚠️ Missing or invalid price_fetcher.py: {e}")
    st.stop()

# --- Import database module ---
try:
    from database import (
    init_db,
    create_usertable,
    add_userdata,
    login_user,
    get_user_data,
    update_user_data,
    make_hash,
    check_hash,
    reset_password,
    get_user_history,
    delete_history_item,
    clear_user_history,
    add_to_history
)

except ImportError as e:
    st.error(f"❌ Missing database.py file or import error: {e}")
    st.stop()

# --- Initialize database ---
try:
    init_db()
except Exception as e:
    st.error(f"⚠️ Database initialization failed: {e}")
    st.stop()

# --- Import image processing module ---
try:
    from image_processing import ProductIdentifier
except ImportError:
    st.warning("🧠 Missing image_processing.py — AI functionality will be simulated.")
    class ProductIdentifier:
        def identify_product(self, uploaded_file):
            return "Wired Headphones", 92  # Simulated fallback

# --- Initialize session state variables ---
if 'price_results' not in st.session_state:
    st.session_state.price_results = []

if 'username' not in st.session_state:
    st.session_state.username = None

if 'uploaded_img' not in st.session_state:
    st.session_state.uploaded_img = None

if 'identified_product' not in st.session_state:
    st.session_state.identified_product = None

if 'confidence' not in st.session_state:
    st.session_state.confidence = 0

# --- Example: Save product to history when results exist ---
if st.session_state.price_results and st.session_state.username:
    try:
        image_buffer = io.BytesIO()
        st.session_state.uploaded_img.save(image_buffer, format="PNG")
        add_to_history(
            st.session_state.username,
            st.session_state.identified_product,
            st.session_state.confidence,
            image_buffer.getvalue(),
            st.session_state.price_results
        )
    except Exception as e:
        st.error(f"⚠️ Failed to save to history: {e}")

# ===========================
# CONFIG
# ===========================
st.set_page_config(page_title="Compario", page_icon="🛒", layout="wide")

# --- GLOBAL COLOR PALETTE ---
PRIMARY_COLOR = "#1D3557"   # Deep Navy Blue
ACCENT_COLOR = "#457B9D"    # Muted Teal Blue
ALERT_COLOR = "#E63946"     # Vibrant Salmon
BACKGROUND_COLOR = "#F1FAEE" # Very Light Creamy Blue

# Load logo (Using a placeholder logic since the file 'logo.png' is not available here)
try:
    LOGO_IMAGE = Image.open("C:\INFOSYS_INTERNSHIP\compario_logo.jpg")
except Exception:
    # Creating a simple placeholder image in memory if logo.png is not found
    from PIL import Image, ImageDraw, ImageFont
    LOGO_IMAGE = Image.new('RGB', (300, 70), color = PRIMARY_COLOR)
    d = ImageDraw.Draw(LOGO_IMAGE)
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()
    d.text((10,15), "Compario Logo", fill=BACKGROUND_COLOR, font=font)


# Ensure DB table exists
try:
    create_usertable()
except Exception as e:
    # st.warning(f"Database table creation issue: {e}") # Suppressed in final app
    pass

# ===========================
# HELPERS
# ===========================
def image_to_base64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def show_centered_logo(width=300):
    if LOGO_IMAGE:
        st.markdown(
            f"<div style='text-align:center; margin-top:20px; margin-bottom:20px;'>"
            f"<img src='data:image/png;base64,{image_to_base64(LOGO_IMAGE)}' width='{width}'></div>",
            unsafe_allow_html=True
        )

def show_topbar():
    logo_html = ""
    if LOGO_IMAGE:
        logo_html = f"<img src='data:image/png;base64,{image_to_base64(LOGO_IMAGE)}' style='height:50px; vertical-align:middle; margin-right:12px; border-radius:8px;'>"

    st.markdown(f"""
    <style>
    /* Global Background */
    body {{
        background-color: {BACKGROUND_COLOR};
        background-attachment: fixed;
        font-family: 'Inter', sans-serif;
    }}
    .stApp {{
        background-color: {BACKGROUND_COLOR};
    }}

    /* Top Bar Styling */
    .topbar {{
        background: #ffffff;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 40px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        position: sticky;
        top: 0;
        z-index: 100;
        border-bottom: 3px solid {ACCENT_COLOR};
    }}
    .app-name {{
        font-size: 32px;
        font-weight: 900;
        color: {PRIMARY_COLOR};
        display: flex;
        align-items: center;
    }}
    
    /* Buttons (including Home/Logout/Login) */
    .stButton>button {{
        background: linear-gradient(90deg, {PRIMARY_COLOR}, {ACCENT_COLOR});
        color: white !important;
        border: none;
        padding: 12px 20px;
        border-radius: 12px;
        font-size: 16px;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight:bold;
        margin-left:10px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    }}
    .stButton>button:hover {{
        background: linear-gradient(90deg, {ACCENT_COLOR}, {PRIMARY_COLOR});
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.3);
    }}

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {{  
        gap: 10px;
        justify-content: center;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {BACKGROUND_COLOR};
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
        font-weight: bold;
        font-size: 18px;
        color: {PRIMARY_COLOR};
        border-bottom: 4px solid transparent;
        transition: all 0.3s ease;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: #ffffff;
        color: {ACCENT_COLOR};
    }}
    .stTabs [aria-selected="true"] {{
        color: {ALERT_COLOR};
        border-bottom: 4px solid {ALERT_COLOR};
        background-color: #ffffff;
    }}

    /* Card Styles */
    .section-title {{
        color:{ALERT_COLOR};
        font-size:40px;
        font-weight:900;
        margin-top:50px;
        text-align:center;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }}
    .adv-card, .platform-card, .about-card, .feature-card {{
        padding:25px;
        border-radius:15px;
        box-shadow:0 6px 20px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        margin:15px;
        border: 1px solid #ddd;
    }}
    .adv-card {{
        background: #ffffff;
        text-align:center;
        height:220px;
        display:flex;
        flex-direction:column;
        justify-content:center;
    }}
    .adv-card:hover {{
        background: {ACCENT_COLOR};
        color:white;
        transform: translateY(-5px);
        box-shadow:0 10px 25px rgba(0,0,0,0.2);
    }}
    .adv-card-title {{
        font-size:24px;
        font-weight:900;
        margin-bottom:10px;
        color: {PRIMARY_COLOR};
    }}
    .adv-card:hover .adv-card-title {{
        color: white;
    }}

    .feature-card {{
        background: linear-gradient(to bottom right, #ffffff, {BACKGROUND_COLOR});
        text-align:center;
        max-width:700px;
        font-weight:bold;
        font-size:20px;
        border-left: 5px solid {ACCENT_COLOR};
    }}
    .feature-card:hover {{
        background: linear-gradient(to bottom right, {ACCENT_COLOR}, {PRIMARY_COLOR});
        color:white;
        transform: scale(1.02);
        box-shadow:0 10px 30px rgba(0,0,0,0.3);
    }}

    .platform-card {{
        background: #ffffff;
        text-align:center;
        font-size:22px;
        font-weight:800;
        height:150px;
        display:flex;
        align-items:center;
        justify-content:center;
    }}
    .platform-card:hover {{
        background: {ALERT_COLOR};
        color:white;
        transform: translateY(-5px);
        box-shadow:0 10px 25px rgba(0,0,0,0.3);
    }}

    .about-card {{
        background: #ffffff;
        padding:30px;
        border-radius:15px;
        box-shadow:0 6px 25px rgba(0,0,0,0.15);
        max-width:900px;
        margin:30px auto;
        font-size:18px;
        line-height:1.6em;
        text-align:center;
        border-left: 8px solid {PRIMARY_COLOR};
    }}

    .offer-banner {{
        background:linear-gradient(90deg, {ALERT_COLOR}, #F07167);
        color:white;
        padding:25px;
        border-radius:14px;
        text-align:center;
        font-weight:900;
        font-size:24px;
        margin-bottom:30px;
        animation: pulse 1.5s infinite alternate;
        box-shadow:0 6px 20px rgba(0,0,0,0.3);
    }}
    @keyframes pulse {{
        from {{ transform: scale(1); }}
        to {{ transform: scale(1.015); }}
    }}
    .footer {{
        text-align:center;
        padding:30px;
        background:#e0e0e0;
        color:{PRIMARY_COLOR};
        margin-top:60px;
        font-weight:bold;
        line-height:1.6em;
        border-top: 2px solid {ACCENT_COLOR};
    }}
    
    /* Price Result Card Styling */
    .result-card {{
        background: #ffffff;
        padding: 20px;
        margin: 10px 0;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
    }}
    .result-price {{
        font-size: 28px;
        font-weight: 900;
        color: {ALERT_COLOR}; /* Use Alert color for attention-grabbing price */
        margin-left: 15px;
        white-space: nowrap;
    }}
    .result-title {{
        font-size: 18px;
        font-weight: 600;
        color: {PRIMARY_COLOR};
        margin-bottom: 5px;
    }}
    .result-website {{
        font-size: 14px;
        color: {ACCENT_COLOR};
        font-weight: 700;
    }}

    </style>
    """, unsafe_allow_html=True)

    # Streamlit layout for Top Bar
    col1, col2, col3 = st.columns([6, 1, 2])
    with col1:
        # App Name Title
        st.markdown(f"<div class='app-name'>{logo_html} Compario</div>", unsafe_allow_html=True)
    with col2:
        # Home Button
        if st.button("🏠 Home", key="home_btn"):
            st.session_state.page = "home"
            st.rerun()
    with col3:
        # Login/Logout Button
        if st.session_state.logged_in:
            if st.button("🚪 Logout"):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.session_state.name = None
                st.session_state.page = "home"
                st.rerun()
        else:
            if st.button("Login / Signup", key="login_btn"):
                st.session_state.page = "login"
                st.rerun()

def validate_password(password):
    if len(password) < 8: return "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password): return "Password must include at least one uppercase letter."
    if not re.search(r"[a-z]", password): return "Password must include at least one lowercase letter."
    if not re.search(r"[0-9]", password): return "Password must include at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): return "Password must include at least one special character."
    return None


# ===========================
# SIDEBAR AND AUTHENTICATED HEADER
# ===========================

def show_dashboard_header(page_title):
    """Shows the header with logo on the left and removes Home/Logout from the right."""
    # Custom CSS for Sidebar Look (integrated into the general CSS section below)

    # Use markdown to place the logo (Top Left) and the title (Center)
    col_logo, col_title = st.columns([1, 6])

    with col_logo:
        # Logo on the top-left, adjusted to fit the sidebar space or main page corner
        st.markdown(f"<div style='margin-top:20px; text-align:left;'>{LOGO_IMAGE.resize((150, 40))}</div>", unsafe_allow_html=True)

    # Page Title (centered visually)
    st.markdown(f"<h1 style='text-align:center; color:{PRIMARY_COLOR}; margin-top:-70px; margin-bottom: 40px;'>{page_title}</h1>", unsafe_allow_html=True)


# ===========================
# SIDEBAR AND AUTHENTICATED HEADER (MODIFIED)
# ===========================

# ===========================
# SIDEBAR AND AUTHENTICATED HEADER (MODIFIED TO CONTAIN ALL CSS)
# ===========================

# ===========================
# SIDEBAR (REFINED STYLING)
# ===========================

# ===========================
# SIDEBAR (CLEAN, LIGHTER STYLING)
# ===========================

# ===========================
# SIDEBAR (FINAL DEVIAS MENU STYLE)
# ===========================

# ===========================
# SIDEBAR (FINAL: RADIO BUTTONS REMOVED)
# ===========================

# ===========================
# SIDEBAR (FINAL: DARK BACKGROUND, CLEAN MENU)
# ===========================

# ===========================
# SIDEBAR (FINAL: DEVIAS COLOR MATCH)
# ===========================

# ===========================
# SIDEBAR (FINAL: DEVIAS COLOR MATCH & GUARANTEED VISIBILITY)
# ===========================

# ===========================
# SIDEBAR (FINAL: DEVIAS COLOR, GUARANTEED VISIBILITY, CIRCULAR LOGO)
# ===========================

def show_sidebar():
    """Sets up the sidebar navigation for authenticated users, with a circular logo at the top."""
    
    # Define colors
    MEDIUM_DARK_SIDEBAR_BG = "#1C2536" # Rich Dark Blue-Grey for sidebar background (Devias)
    PRIMARY_COLOR = "#FFFFFF"      # White (GUARANTEED: for all inactive text)
    
    # Active/Hover Colors (Kept from last successful Devias color match)
    ACCENT_COLOR = "#2C3A57"       # Deep Blue-Violet for active item background
    HOVER_COLOR = "#273245"        # Medium Blue-Grey for hover background
    ACTIVE_TEXT_COLOR = "#FFFFFF"  # White for active item text

    # 1. Prepare Logo HTML using base64 for embedding and circular styling
    # Resize the logo for the circle container (adjust size as needed, e.g., 80x80)
    logo_b64 = image_to_base64(LOGO_IMAGE.resize((80, 80))) 
    
    # HTML for a circular logo
    logo_html = f"""
    <div style="
        width: 100px; /* Outer container for centering */
        height: 100px; /* Match width for perfect circle */
        border-radius: 50%; /* Makes it circular */
        overflow: hidden; /* Hides parts of image outside the circle */
        margin: 20px auto 20px auto; /* Center horizontally, add vertical spacing */
        border: 2px solid {ACCENT_COLOR}; /* Optional: a border matching accent color */
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: {PRIMARY_COLOR}; /* Background if image is transparent or smaller */
    ">
        <img src='data:image/png;base64,{logo_b64}' alt='Compario Logo' style='
            max-width: 100%; 
            max-height: 100%;
            object-fit: cover; /* Ensures the image covers the circle area */
        '>
    </div>
    """

    with st.sidebar:
        # --- LOCAL CSS INJECTION: AGGRESSIVE RADIO BUTTON REMOVAL & DEVIAS THEME ---
        st.markdown(f"""
            <style>
            /* TARGET THE MAIN SIDEBAR CONTAINER FOR BACKGROUND COLOR */
            .stSidebar > div:first-child, .css-r6v9h1 {{
                background-color: {MEDIUM_DARK_SIDEBAR_BG} !important;
                color: {PRIMARY_COLOR} !important; 
            }}
            /* Adjust the Streamlit default content color */
            .stSidebar div[data-testid="stSidebarContent"] {{
                color: {PRIMARY_COLOR} !important;
            }}

            /* STYLE THE WELCOME MESSAGE */
            .stSidebar h3 {{
                color: {PRIMARY_COLOR} !important; 
                text-align: left; /* Changed to left-aligned from center for Devias feel */
                padding: 20px 0 10px 15px; /* Added left padding */
                font-weight: 700;
            }}
            
            /* --- MENU LINK STYLING --- */

            /* Style the overall label container */
            .stSidebar .stRadio div[role="radiogroup"] label {{
                font-size: 16px;
                padding: 10px 15px;
                margin: 5px 0;
                border-radius: 8px;
                transition: all 0.2s ease;
                font-weight: 500;
                display: flex;
                align-items: center;
            }}
            
            /* GUARANTEED INACTIVE TEXT/ICON COLOR FIX */
            .stSidebar .stRadio div[role="radiogroup"] label:not([data-baseweb="radio"]:has(input:checked)) * {{
                 color: {PRIMARY_COLOR} !important; 
            }}
            
            /* AGGRESSIVE RADIO BUTTON REMOVAL */
            .stSidebar .stRadio div[data-testid="stDecoration"] {{
                display: none !important;
            }}
            .stSidebar .stRadio input[type="radio"] {{
                display: none !important;
            }}
            
            /* Ensure the text is pushed to the left */
            .stSidebar .stRadio div[data-testid="stCheckableElementLabel"] {{
                margin-left: -5px; 
            }}

            /* HOVER EFFECT */
            .stSidebar .stRadio div[role="radiogroup"] label:hover {{
                background-color: {HOVER_COLOR};
            }}

            /* STYLE FOR THE SELECTED ITEM (ACTIVE PAGE) */
            .stSidebar .stRadio div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {{
                background-color: {ACCENT_COLOR}; 
                font-weight: bold;
            }}
            /* Ensure all elements within the active item stay white/bold */
            .stSidebar .stRadio div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) * {{
                color: {ACTIVE_TEXT_COLOR} !important;
            }}

            /* Ensure the menu title is visible and left-aligned */
            .stSidebar .stRadio label[data-testid="stWidgetLabel"] {{
                color: {PRIMARY_COLOR} !important;
                font-weight: bold;
                padding-left: 15px;
            }}
            </style>
        """, unsafe_allow_html=True)
        # --- END LOCAL CSS INJECTION ---
        
        # --- LOGO DISPLAY ---
        st.markdown(logo_html, unsafe_allow_html=True)
        
        # User Welcome Message
        st.markdown(f"<h3>Welcome, {st.session_state.name}!</h3>", unsafe_allow_html=True)
        
        # --- Sidebar Menu ---
        display_pages = {
            "📊 Dashboard": 'dashboard',
            "👤 My Profile": 'profile',
            # "🛒 My Saved Products": 'saved_products',
            "⏱️ My History": 'history',
            "🚪 Logout": 'logout'
        }
        
        # Find the current index to maintain state
        current_page_key = [k for k, v in display_pages.items() if v == st.session_state.get('page', 'dashboard')]
        current_index = list(display_pages.keys()).index(current_page_key[0]) if current_page_key else 0

        # Create radio buttons for navigation (now invisible and acting as links)
        selected_page_name = st.radio(
            "Menu",
            list(display_pages.keys()),
            index=current_index, 
            key='sidebar_nav'
        )
        
        # Update the session state page based on the sidebar selection
        st.session_state.page = display_pages[selected_page_name]


# ===========================
# FEATURES SECTION HELPER (NEW)
# ===========================
def init_card_state():
    # Initialize a state variable for each card to track its 'flipped' status
    if 'card_flip_0' not in st.session_state:
        st.session_state.card_flip_0 = False  # False means 'Front' side is showing
    if 'card_flip_1' not in st.session_state:
        st.session_state.card_flip_1 = False
    if 'card_flip_2' not in st.session_state:
        st.session_state.card_flip_2 = False

# Function to handle the flip action for a specific card index
def toggle_card(index):
    # This flips the state (True <-> False)
    st.session_state[f'card_flip_{index}'] = not st.session_state[f'card_flip_{index}']

# --- MAIN FEATURE RENDERING FUNCTION ---

def show_core_features():
    # Initialize state before any Streamlit widget is rendered
    init_card_state()
    
    # Fetching colors from global config for local use in markdown
    PRIMARY_COLOR = "#1D3557"   # Deep Navy Blue
    ACCENT_COLOR = "#457B9D"    # Muted Teal Blue
    ALERT_COLOR = "#E63946"     # Vibrant Salmon
    BACKGROUND_COLOR = "#F1FAEE" # Very Light Creamy Blue

    # Custom CSS for the feature cards, including the fixed height fix
    st.markdown(f"""
    <style>
    .features-container {{
        margin-top: 60px;
        margin-bottom: 60px;
    }}
    .features-header-title {{
        font-size: 36px;
        font-weight: 800;
        color: {PRIMARY_COLOR};
        margin-bottom: 5px;
        text-align: left;
    }}
    .features-header-subtitle {{
        font-size: 18px;
        color: #4a4a4a;
        margin-bottom: 40px;
        text-align: left;
    }}
    .start-saving-button {{
        border: 2px solid {ALERT_COLOR};
        color: {ALERT_COLOR};
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 700;
        transition: all 0.2s ease-in-out;
        white-space: nowrap;
    }}
    .start-saving-button:hover {{
        background-color: {ALERT_COLOR};
        color: white;
    }}

    /* Card Styling */
    .feature-box {{
        background: #ffffff;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        height: 350px; /* FIXED HEIGHT to prevent layout jumping on flip */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        border-top: 5px solid {ACCENT_COLOR};
        margin-bottom: 20px;
    }}
    .feature-box:hover {{
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }}
    .feature-icon-container {{
        width: 60px;
        height: 60px;
        margin: 0 auto 20px auto;
        border-radius: 50%;
        background-color: {BACKGROUND_COLOR};
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #e0e0e0;
    }}
    .feature-icon {{
        color: {ACCENT_COLOR};
        font-size: 30px;
    }}
    .feature-box-title {{
        font-size: 30px;
        font-weight: 700;
        color: {PRIMARY_COLOR};
        margin-bottom: 10px;
    }}
    .feature-box-desc {{
        font-size: 20px;
        color: #555;
        line-height: 1.5;
        flex-grow: 1; /* Allows the description area to take up available space */
    }}
    /* Styling for the Back/Detailed content */
    .feature-back-content {{
        font-size: 18px;
        color: #333;
        text-align: left;
        line-height: 1.6;
        flex-grow: 1; /* Allows the back content to take up available space */
    }}
    .stButton>button {{
        width: 100%; /* Make the button full width to look like a separate element */
        background-color: {ACCENT_COLOR};
        color: white;
        border: none;
        padding: 10px;
        border-radius: 8px;
        font-weight: 600;
    }}
    .stButton>button:hover {{
        background-color: {PRIMARY_COLOR};
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Header Row
    col_header, col_button = st.columns([8, 2])
    
    with col_header:
        st.markdown(f"<div class='features-container'><h2 class='features-header-title'>Core Features & Services</h2>", unsafe_allow_html=True)
        st.markdown("<p class='features-header-subtitle'>Beyond simply comparing numbers, our commitment lies in delivering unparalleled smart shopping tools tailored to your needs.</p></div>", unsafe_allow_html=True)

    with col_button:
        # Aligning the button to the bottom of the column to match the image layout
        st.markdown(f"""
        <div style='margin-top: 70px; text-align: right;'>
            <a href='#' class='start-saving-button'>Start Saving Now</a>
        </div>
        """, unsafe_allow_html=True)

    # Features Row (3 Cards)
    col1, col2, col3 = st.columns(3)

    features_data = [
        {
            "icon": "🤖",
            "title": "AI Product Identification",
            "desc_front": "Accurate Product ID, Swift Results: Our AI identifies products from any image for precise search.",
            "desc_back": "Leveraging advanced Convolutional Neural Networks (CNNs), the application can process uploaded images to accurately recognize and categorize products, enabling precise comparison searches across multiple e-commerce platforms. This uses the Image Upload, Preprocessing, and Recognition module.",
        },
        {
            "icon": "📈",
            "title": "Price Trend Analysis",
            "desc_front": "Our thorough assessments and expert evaluations help you stay proactive about fluctuating market prices.",
            "desc_back": "Historical pricing data is scraped or collected via APIs from e-commerce platforms (Amazon, Flipkart, Snapdeal) to generate detailed trend charts. This data also feeds into the comparison algorithm to find the absolute lowest price.",
        },
        {
            "icon": "💰",
            "title": "Maximized Savings Alerts",
            "desc_front": "Experience comprehensive deal spotting. Trust us to keep your budget healthy and your wallet fat.",
            "desc_back": "The application ensures prices from various stores are constantly updated. By developing a comparison algorithm, it reliably identifies the lowest price, saving the user significant cost and time.",
        },
    ]

    for index, (col, data) in enumerate(zip([col1, col2, col3], features_data)):
        is_flipped = st.session_state[f'card_flip_{index}']
        button_key = f'learn_more_btn_{index}'

        with col:
            # --- CARD CONTENT ---
            html = f"""
            <div class="feature-box">
                <div class="feature-icon-container">
                    <span class="feature-icon">{data['icon']}</span>
                </div>
                <div class="feature-box-title">{data['title']}</div>
                <div class="{ 'feature-box-desc' if not is_flipped else 'feature-back-content' }">
                    {data['desc_front'] if not is_flipped else data['desc_back']}
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)

            # --- BUTTON INSIDE CARD ---
            button_label = "Show Less" if is_flipped else "Learn More"
            button_html = f"""
            <div style="margin-top:-20px;">
                <form>
                    <button class="stButton" style="
                        width:100%;
                        background-color:{ACCENT_COLOR};
                        color:white;
                        border:none;
                        padding:10px;
                        border-radius:8px;
                        font-weight:600;
                        cursor:pointer;
                    ">{button_label}</button>
                </form>
            </div>
            """
            # Render the Streamlit button below HTML for interactivity
            st.button(button_label, key=button_key, on_click=toggle_card, args=(index,), use_container_width=True)

            
            st.markdown("</div>", unsafe_allow_html=True) # End the feature-box div

# To run this, you would call the function:
# show_core_features()


# ===========================
# TESTIMONIALS SECTION HELPER (NEW)
# ===========================
def show_testimonials():
    # Fetching colors from global config
    PRIMARY_COLOR = "#1D3557"   # Deep Navy Blue
    ACCENT_COLOR = "#457B9D"    # Muted Teal Blue
    BACKGROUND_COLOR = "#F1FAEE" # Very Light Creamy Blue

    # Custom CSS for Testimonial Cards
    st.markdown(f"""
    <style>
    /* Testimonial Header Alignment */
    .testimonial-header-title {{
        font-size: 36px;
        font-weight: 800;
        color: {PRIMARY_COLOR};
        margin-bottom: 5px;
        text-align: left;
    }}
    .testimonial-header-subtitle {{
        font-size: 16px;
        color: #666;
        margin-bottom: 40px;
        text-align: left;
    }}
    
    /* Card Styling */
    .testimonial-card {{
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        height: 100%;
        margin: 10px;
        transition: transform 0.3s ease;
        overflow: hidden; /* Ensures the image doesn't overflow the card */
    }}
    .testimonial-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    }}
    
    /* Image and Text Container */
    .testimonial-image-area {{
        height: 250px; /* Fixed height for image area */
        background-color: {BACKGROUND_COLOR}; /* Use light background for image area */
        overflow: hidden;
    }}
    .testimonial-image-area img {{
        object-fit: cover;
        width: 100%;
        height: 100%;
        display: block;
    }}
    
    /* Text Content */
    .testimonial-text-content {{
        padding: 20px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    .testimonial-name {{
        font-size: 18px;
        font-weight: 700;
        color: {PRIMARY_COLOR};
        margin-top: 5px;
    }}
    .testimonial-title {{
        font-size: 14px;
        color: {ACCENT_COLOR};
        font-weight: 500;
        margin-bottom: 15px;
    }}
    .testimonial-quote {{
        font-style: italic;
        font-size: 14px;
        color: #555;
        line-height: 1.5;
        min-height: 80px; /* Ensures consistent quote box height */
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Header Section
    col_head, col_nav = st.columns([10, 2])
    with col_head:
        st.markdown(f"<h2 class='testimonial-header-title'>What Our Users Say</h2>", unsafe_allow_html=True)
        st.markdown("<p class='testimonial-header-subtitle'>Read testimonials from savvy shoppers who trust Compario to maximize their savings.</p>", unsafe_allow_html=True)
    with col_nav:
        # Placeholder for navigation arrows (styled to match)
        # In a real app, these would control a carousel/slider.
        st.markdown(f"""
        <div style='margin-top: 30px; text-align: right;'>
            <span style='color: {ACCENT_COLOR}; font-size: 24px; margin-right: 15px;'>←</span>
            <span style='color: {ACCENT_COLOR}; font-size: 24px;'>→</span>
        </div>
        """, unsafe_allow_html=True)


    # Testimonial Content (3 Columns)
    col1, col2, col3 = st.columns(3)

    testimonials_data = [
        {
            "image": "C:\INFOSYS_INTERNSHIP\Top-Marketing-Experts-Mark-Brenner.jpeg",
            "name": "Michael Brenner",
            "title": "Marketing Analyst",
            "quote": "Compario is a game-changer! This is really amazing. Thanks to the real-time comparison. Just go for it."
        },
        {
            "image": "C:\INFOSYS_INTERNSHIP\Ann-Handley-Top-Marketing-Experts.jpeg",
            "name": "Ann Handley",
            "title": "Chief Content Officer, MarketingProfs",
            "quote": "The AI product identification is flawless. It cut my purchasing time in half for inventory."
        },
        {
            "image": "C:\INFOSYS_INTERNSHIP\Tom-Shapiro-Top-Marketing-Influencers.jpeg",
            "name": "Tom Shapiro",
            "title": "CEO at Stratabeat",
            "quote": "Simple to use and so effective. I check compario before every online purchase now!"
        },
    ]

    for col, data in zip([col1, col2, col3], testimonials_data):
        with col:
            # Load the image locally
            try:
                # Use PIL to load and resize the image for a square look
                img = Image.open(data['image'])
                
                # Resize the image to match the fixed height set in CSS (250px)
                # This prevents the raw image size from distorting the layout
                img_resized = img.resize((350, 250)) 
                
                # Convert the image to base64 for embedding in HTML, allowing the CSS to style it properly
                img_b64 = image_to_base64(img_resized)

                image_html = f"<div class='testimonial-image-area'><img src='data:image/jpeg;base64,{img_b64}'></div>"
                
            except FileNotFoundError:
                st.warning(f"Image not found: {data['image']}")
                image_html = f"<div class='testimonial-image-area' style='background-color: #ccc;'>Image Placeholder</div>"
            except Exception as e:
                st.error(f"Error processing image {data['image']}: {e}")
                image_html = f"<div class='testimonial-image-area' style='background-color: {ALERT_COLOR};'>Error Loading Image</div>"

            # Render the final card structure
            st.markdown(f"""
            <div class='testimonial-card'>
                {image_html}
                <div class='testimonial-text-content'>
                    <div>
                        <div class='testimonial-name'>{data['name']}</div>
                        <div class='testimonial-title'>{data['title']}</div>
                    </div>
                    <div class='testimonial-quote'>"{data['quote']}"</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            # Add a small vertical space to ensure card separation
            st.markdown("<br>", unsafe_allow_html=True)






# ===========================
# FOOTER SECTION HELPER (FINAL & FULL-WIDTH)
# ===========================
def show_custom_footer():
    # Fetching colors from global config
    PRIMARY_COLOR = "#1D3557"   # Deep Navy Blue
    ACCENT_COLOR = "#457B9D"    # Muted Teal Blue
    
    # NEW CUSTOM COLOR FOR THE FOOTER CONTENT AREA
    FOOTER_BG_COLOR = "#E8F5F5" # A Light Grayish Blue

    # Custom CSS for the footer elements
    st.markdown(f"""
    <style>
    /* Global App Background Color from config for contrast */
    .stApp {{
        background-color: #F1FAEE; /* Ensure this is set to your global BACKGROUND_COLOR */
    }}
    
    /* Custom Footer Styling */
    .custom-footer-wrapper {{
        /* Use negative margins to span the entire width of the page */
        margin-left: -80px; 
        margin-right: -80px;
        background-color: {FOOTER_BG_COLOR}; /* Apply the light blue to the wrapper */
        padding-top: 50px; /* Padding for the space above content */
    }}

    .custom-footer-area {{
        /* This is now just a padding container, background is handled by the wrapper */
        padding: 0 80px 50px 80px; 
        color: {PRIMARY_COLOR};
    }}
    .footer-section-title {{
        font-size: 20px;
        font-weight: 900;
        color: {ACCENT_COLOR}; 
        margin-bottom: 20px;
    }}
    .footer-link-list {{
        list-style: none;
        padding: 0;
    }}
    .footer-link-list li {{
        margin-bottom: 8px;
        font-size: 15px;
    }}
    .footer-link-list a {{
        color: {PRIMARY_COLOR};
        text-decoration: none;
        transition: color 0.2s;
    }}
    .footer-link-list a:hover {{
        color: {ACCENT_COLOR};
    }}
    .footer-contact-item {{
        display: flex;
        align-items: flex-start;
        margin-bottom: 12px;
        font-size: 15px;
    }}
    .footer-contact-icon {{
        margin-right: 10px;
        color: {ACCENT_COLOR};
        font-size: 18px;
        line-height: 1.5;
    }}
    .footer-logo-title {{
        font-size: 28px;
        font-weight: 900;
        color: {ACCENT_COLOR};
        margin-bottom: 15px;
    }}
    .footer-mission-text {{
        font-size: 15px;
        line-height: 1.6;
        color: #555;
    }}
    .footer-bottom-bar {{
        background-color: {ACCENT_COLOR}; 
        color: white;
        padding: 15px 80px;
        text-align: left;
        font-size: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .social-icons a {{
        color: white;
        margin-left: 15px;
        font-size: 18px;
        text-decoration: none;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # 1. Create the full-width wrapper with the new background color
    st.markdown(f"<div class='custom-footer-wrapper'>", unsafe_allow_html=True)
    
    # 2. Start the main content area (which contains the columns)
    st.markdown(f"<div class='custom-footer-area'>", unsafe_allow_html=True)
    
    # Use Streamlit columns for SIDE-BY-SIDE layout
    col1, col2, col3, col4 = st.columns([3, 2, 2, 3]) 

    with col1:
        st.markdown(f"""
            <div class="footer-logo-title">Compario</div>
            <p class='footer-mission-text'>
                We are honored to be a part of your smart shopping journey, committed to delivering unbiased, accurate, and top-notch price information every step of the way.
            </p>
            <p class='footer-mission-text'>
                Trust us with your budget, and let us work together to achieve the best possible outcomes for your wallet and your loved ones.
            </p>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="footer-section-title">Company</div>
            <ul class="footer-link-list">
                <li><a href="#">Home</a></li>
                <li><a href="#">About Us</a></li>
                <li><a href="#">Work With Us</a></li>
                <li><a href="#">Our Blog</a></li>
                <li><a href="#">Terms & Conditions</a></li>
            </ul>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="footer-section-title">Tools</div>
            <ul class="footer-link-list">
                <li><a href="#">Search by Image</a></li>
                <li><a href="#">Advanced Search</a></li>
                <li><a href="#">Privacy Policy</a></li>
                <li><a href="#">Retailers</a></li>
                <li><a href="#">Pricing Alerts</a></li>
            </ul>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class="footer-section-title">Contact Us</div>
            <div class="footer-contact-item">
                <span class="footer-contact-icon">📍</span> <span>Plot No. IIIG/2, New Town- Action area- III, Kolkata Leather Complex, Beonta II, Dist- South 24 parganas, Kolkata- 700135 (Near Hatishala)</span>
            </div>
            <div class="footer-contact-item">
                <span class="footer-contact-icon">📧</span> <span><a href="mailto:support@Compario.com" style="color:{PRIMARY_COLOR};">support@Compario.com</a></span>
            </div>
            <div class="footer-contact-item">
                <span class="footer-contact-icon">📞</span> <span>(+123) 549 7652</span>
            </div>
        """, unsafe_allow_html=True)

    # 3. Close the main content area
    st.markdown("</div>", unsafe_allow_html=True) 

    # 4. Bottom Bar (placed immediately after the main area)
    st.markdown(f"""
        <div class='footer-bottom-bar'>
            <span>Copyright © 2025 Compario. All rights reserved.</span>
            <span class='social-icons'>
                <a href="#">📷</a> 
                <a href="#">📘</a> 
                <a href="#">🐦</a> 
                <a href="#">🌐</a> 
            </span>
        </div>
    """, unsafe_allow_html=True)
    
    # 5. Close the full-width wrapper
    st.markdown("</div>", unsafe_allow_html=True)

# ===========================
# HOME PAGE
# ===========================
def home_page():
    show_topbar()
    
    # Using the Primary Color for the main heading
    st.markdown(f"<h1 style='text-align:center; color:{PRIMARY_COLOR};'>🛒 AI-Powered Product Price Comparison</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:18px; color:gray;'>Upload a product image and instantly find the lowest prices across multiple e-commerce platforms.</p>", unsafe_allow_html=True)

    st.markdown("<div class='offer-banner'>🔥 New User Exclusive: Get 10% Extra Cashback on Your First Purchase!</div>", unsafe_allow_html=True)

    st.markdown("<h2 class='section-title'>Advantages of Using compario</h2>", unsafe_allow_html=True)
    cols = st.columns(3)
    advantages = [
        ("⚡ Lightning Fast Search", "Find the best deals within seconds, saving precious time."),
        ("🤖 Precision AI Identification", "Upload any product image and the AI identifies it automatically with high accuracy."),
        ("💰 Maximize Savings", "Compare prices across all major e-commerce platforms effortlessly.")
    ]

    show_core_features()


    for col, (title, desc) in zip(cols, advantages):
        col.markdown(f"<div class='adv-card'><div class='adv-card-title'>{title}</div>{desc}</div>", unsafe_allow_html=True)

    # --- Key Features Section with Image (MODIFIED) ---

    # --- Key Features Section with Image (FINAL WORKING CORRECTION) ---

    # --- Key Features Section with FINAL SMALL IMAGE FIX ---

    # --- Key Features Section with FINAL ALIGNMENT FIX ---

    st.markdown("<h2 class='section-title'>Key Features</h2>", unsafe_allow_html=True)
    
    # Custom CSS for the tiny image container to vertically center the icon
    st.markdown("""
    <style>
    .aligned-image-container {
        /* Set height based on the total height of the features column */
        height: 100%; 
        display: flex;
        flex-direction: column;
        justify-content: center; /* Center vertically */
        align-items: center;     /* Center horizontally */
    }
    /* Ensure the image itself doesn't exceed its defined size */
    .aligned-image-container img {
        max-width: 425px; 
        height: auto;
    }
    /* Hide the caption which often disrupts vertical flow */
    .aligned-image-container .stCaption {
        display: none; 
    }
    </style>
    """, unsafe_allow_html=True)


    # Use columns. Ratio [1, 1] is fine now that the image is small.
# Use columns. Ratio [1, 1] is fine now that the image is small.


# Use columns. Ratio [1, 1] is fine for the features lists.
    col_features_left, col_features_right = st.columns([1, 1])

    # Content for the Left Column (Original Key Features List)
    with col_features_left:
        
        features_left = [
            "Instant price comparison across top platforms",
            "AI-powered product recognition from images",
            "Secure user authentication and data privacy",
            "User-friendly dashboard and personalized reports"
        ]
        for feat in features_left:
            # Assuming 'feature-card' is defined in your CSS/styling
            st.markdown(f"<div class='feature-card'>• {feat}</div>", unsafe_allow_html=True)

    # Content for the Right Column (New Key Features List)
    with col_features_right:
        
        # New features derived from the project documentation
        features_right = [
            # New features added from your document
            "Saves user time and money by finding the best deals ", 
            "Integrates with major e-commerce platforms ",
            "Displays detailed product information",
            "Provides alternative suggestions when prices are not found " 
        ]
        for feat in features_right:
            # Using the same styling for consistency
            st.markdown(f"<div class='feature-card'>• {feat}</div>", unsafe_allow_html=True)
            
    # --- END OF KEY FEATURES SECTION ---


    st.markdown("<h2 class='section-title'>E-Commerce Platforms Included</h2>", unsafe_allow_html=True)
    platforms = ["Amazon", "Flipkart", "Snapdeal"]  # Added Tata Cliq
    # Adjust columns dynamically for better spacing
    platform_cols = st.columns(len(platforms))
    for col, plat in zip(platform_cols, platforms):
        col.markdown(f"<div class='platform-card'>{plat}</div>", unsafe_allow_html=True)



    st.markdown("<h2 class='section-title'>About compario</h2>", unsafe_allow_html=True)
    about_text = """
    Compario is designed to simplify your online shopping experience. 
    With the growing number of online shopping platforms, finding the absolute lowest price can be time-consuming and frustrating. 
    Our cutting-edge AI technology allows you to simply upload a photo of the product you want, and we instantly scan and compare prices across numerous retailers. 
    Stop wasting time searching, and start saving money effortlessly!
    """
    st.markdown(f"<div class='about-card'>{about_text}</div>", unsafe_allow_html=True)
    
    # --- INSERT NEW TESTIMONIALS SECTION HERE ---
    show_testimonials()
    # ---------------------------------------------

    show_custom_footer()

# ===========================
# DASHBOARD PAGE - FIXED
# ===========================
def dashboard_page():
    show_topbar()
    st.markdown(f"<h2 style='text-align:center; color:{PRIMARY_COLOR}; margin-top:20px;'>Welcome to Your Dashboard, {st.session_state.name}!</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:18px; color:gray;'>Upload a product image below to begin your price comparison journey.</p>", unsafe_allow_html=True)

    st.markdown("<div class='about-card'>🖼 Use the uploader below! Our AI will identify the product and find the best current price.</div>", unsafe_allow_html=True)

    st.markdown(f"<h3 style='text-align:center; color:{ACCENT_COLOR}; margin-top:40px;'>Upload Your Product Image for Analysis</h3>", unsafe_allow_html=True)
    
    # Use a container for the main upload area to keep it clean
    with st.container(border=True):
        uploaded_file = st.file_uploader("Choose an image (JPG, JPEG, PNG)...", type=["jpg","jpeg","png"])
        
        # NOTE: Assuming ProductIdentifier class and fetch_prices function are defined/imported
        product_identifier = ProductIdentifier() 
        
        if uploaded_file is not None:
            # Store the uploaded image to display in the results section if needed
            st.session_state.uploaded_img = Image.open(uploaded_file)
            st.image(st.session_state.uploaded_img, caption='Uploaded Product Image', width=300) # Fixed width for consistency
            st.success("✅ Image ready for analysis!")

            if st.button("🔍 Analyze and Compare Prices"):
                
                # Clear previous search results
                st.session_state.price_results = None 
                
                with st.spinner("Analyzing image and searching databases..."):
                    try:
                        # 1. AI Identification
                        label, confidence = product_identifier.identify_product(uploaded_file)
                        st.session_state.identified_product = label
                        st.session_state.confidence = confidence
                        
                        # 2. Price Fetching
                        if confidence >= 50: # Only proceed if AI has moderate to high confidence
                            st.info(f"Using identified product name: **{label}**")
                            # Call the function from price_fetcher.py
                            st.session_state.price_results = get_price(label)
                        else:
                            st.warning("Confidence is too low (<50%). Refusing to search. Please upload a clearer image.")
                            st.session_state.price_results = None
                            
                    except Exception as e:
                        st.error(f"An error occurred during analysis or fetching: {e}")
                        st.session_state.price_results = None
                        
    # ---------------------------------------------------------------------
    # --- FIXED: Results Display Logic moved to the correct location ---
    # ---------------------------------------------------------------------

    # Display AI Identification Info
    if 'identified_product' in st.session_state and st.session_state.identified_product:
        label = st.session_state.identified_product
        confidence = st.session_state.confidence
        
        # Logic for color/emoji remains here
        if confidence >= 80:
            color = PRIMARY_COLOR
            bg_color = "#E8F5E9" # Light Green
            emoji = "🚀"
            message = "High confidence! Searching for the best prices now..."
        elif confidence >= 50:
            color = ACCENT_COLOR
            bg_color = "#FFFDE7" # Light Yellow
            emoji = "🧐"
            message = "Moderate confidence. Check the product name before purchase."
        else:
            color = ALERT_COLOR
            bg_color = "#FFEBEE" # Light Red
            emoji = "⚠"
            message = "Low confidence. Please upload a clearer image."

        st.markdown(
            f"""
            <div style='
                padding:20px; 
                background-color:{bg_color}; 
                border-radius:12px; 
                text-align:center;
                border: 2px solid {color};
                margin-top:20px;
            '>
                <h3 style='color:{color}; font-weight:900;'>{emoji} Identified Product: {label}</h3>
                <p style='font-size:18px; color:black;'>Confidence Score: <b>{confidence:.2f}%</b></p>
                <p style='font-size:16px; color:gray;'>{message}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Display Price Comparison Results
    if 'price_results' in st.session_state and st.session_state.price_results:
    
        st.markdown(f"<h3 style='text-align:center; color:{PRIMARY_COLOR}; margin-top:40px; margin-bottom:20px;'>💵 Price Comparison Results for: {st.session_state.identified_product}</h3>", unsafe_allow_html=True)

        # --------------------------------------------------------------------------------------------------
        # 🎯 FIX: Filter out non-dictionary items before sorting. This prevents the TypeError.
        # --------------------------------------------------------------------------------------------------
        valid_results = [
            item for item in st.session_state.price_results 
            if isinstance(item, dict)
        ]

        # Sort results to show the lowest price first, handling None prices
        sorted_results = sorted(
            valid_results, # Use the filtered list here
            # Use .get() defensively to ensure safe key access
            key=lambda x: x.get('price', float('inf')) if x.get('price') is not None else float('inf')
        )
        
        # Check if 'price' is the key used in your scraper results. 
        # Based on your scraper code: item["price"] is the correct key for the float price.
        # If the app relies on 'Price (₹)' for sorting/display, ensure your data preparation 
        # transforms 'price' (float) into 'Price (₹)' (formatted string/integer) first.
        
        # Assuming your results dicts use the key 'price' (from the scraper's output):
        # If your data preparation layer converts 'price' to 'Price (₹)', 
        # then the original key can be kept, but using .get() is safer.
        
        # --------------------------------------------------------------------------------------------------
        # UPDATED COLUMN CONFIGURATION
        col_img, col_info, col_rating, col_price, col_delivery, col_deal = st.columns([1, 2.5, 1.5, 1.5, 2, 1.5])
        
        # Display header row
        col_img.markdown('**Image**', unsafe_allow_html=True)
        col_info.markdown('**Product Details**', unsafe_allow_html=True)
        col_rating.markdown('**Rating**', unsafe_allow_html=True)
        col_price.markdown('**Price (₹)**', unsafe_allow_html=True)
        col_delivery.markdown('**Delivery**', unsafe_allow_html=True)
        col_deal.markdown('**Action**', unsafe_allow_html=True)
        
        # Add a separator
        st.markdown('---') 
        # --------------------------------------------------------------------------------------------------

        for i, item in enumerate(sorted_results):
            # UPDATED COLUMN INSTANTIATION
            col_img, col_info, col_rating, col_price, col_delivery, col_deal = st.columns([1, 2.5, 1.5, 1.5, 2, 1.5])

            # 🎯 FIX: Use item.get('Price (₹)') to safely retrieve the value
            # This prevents a KeyError if the key is missing, and works correctly 
            # because 'item' is now guaranteed to be a dict.
            price_value = item.get('Price (₹)') 
            
            # Ensure the price is a number before formatting, and use .get()
            price_display = f"₹ {price_value:,}" if isinstance(price_value, (int, float)) else "N/A"
            
            # You'll need to add the rest of your loop logic here, like:
            # col_price.markdown(f"**{price_display}**")
            # col_info.markdown(f"[{item.get('title', 'N/A')}]({item.get('url')})", unsafe_allow_html=True)
                
            # 1. Image Column
            if item['Image']:
                col_img.image(item['Image'], width=100)
            elif st.session_state.uploaded_img:
                col_img.image(st.session_state.uploaded_img, width=100) # Fallback to uploaded image
            else:
                col_img.write("No Img")

            # 2. Info Column
            col_info.markdown(f"""
                <div class='result-website'>{item['Website']}</div>
                <div class='result-title'>{item['Title']}</div>
                """, unsafe_allow_html=True)

            # 3. New Rating Column
            rating = item.get('Rating') # Assumed key in the data structure
            reviews = item.get('Reviews') # Assumed key in the data structure
            
            if rating and reviews:
                try:
                    rating_value = float(rating)
                except:
                    rating_value = 0.0

                # Generate star icons (full, half, and empty)
                full_stars = int(rating_value)
                half_star = 1 if rating_value - full_stars >= 0.5 else 0
                empty_stars = 5 - full_stars - half_star

                star_html = (
                    '<span style="color: gold; font-size: 18px;">' + '★' * full_stars + '</span>' +
                    ('<span style="color: gold; font-size: 18px;">☆</span>' if half_star else '') +
                    '<span style="color: lightgray; font-size: 18px;">' + '☆' * empty_stars + '</span>'
                )

                rating_html = f"""
                    <div style="display: flex; align-items: center; gap: 6px;">
                        {star_html}
                        <span style="font-size: 16px; font-weight: bold; color: {PRIMARY_COLOR};">
                            {rating_value:.1f}
                        </span>
                    </div>
                    <div style="font-size: 12px; color: gray;">
                        {reviews}
                    </div>
                """
                col_rating.markdown(rating_html, unsafe_allow_html=True)

            else:
                col_rating.markdown("N/A", unsafe_allow_html=True)

            # 4. Price Column
            is_lowest = (i == 0 and item['Price (₹)'] is not None)
            price_style = f"font-size: 28px; font-weight: 900; color: {ALERT_COLOR if is_lowest else PRIMARY_COLOR}; white-space: nowrap;"
            
            if item.get("Error"):
                    col_price.error("Fetch Error")
            else:
                col_price.markdown(f"<div style='{price_style}'>{price_display}</div>", unsafe_allow_html=True)
                if is_lowest:
                    col_price.markdown('**🎉 Lowest Price!**', unsafe_allow_html=True)

            # 5. New Delivery Column
            delivery_date = item.get('Delivery Date') # Assumed key in the data structure
            
            if item['Price (₹)'] is None or delivery_date is None:
                col_delivery.markdown("<span style='color: gray; font-size: 14px;'>Check on site</span>", unsafe_allow_html=True)
            else:
                # Display the estimated delivery date
                col_delivery.markdown(f"<span style='color: green; font-size: 14px;'>{delivery_date}</span>", unsafe_allow_html=True)

            # 6. Action Column
            if item['Price (₹)'] is not None:
                # Use markdown to create a styled link button
                deal_button_html = f"""
                <a href="{item['URL']}" target="_blank" style="
                    background-color: {ALERT_COLOR}; 
                    color: white; 
                    padding: 10px 15px; 
                    text-align: center; 
                    text-decoration: none; 
                    display: inline-block; 
                    border-radius: 8px;
                    font-weight: bold;
                    margin-top: 10px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                ">
                Go to Deal ↗
                </a>
                """
                col_deal.markdown(deal_button_html, unsafe_allow_html=True)
            else:
                col_deal.write("Link N/A")
            st.markdown('---')


        # Prevent duplicates when rerunning
        

# make sure uploaded_img, identified_product, price_results exist in session
        if st.session_state.get('identified_product') and st.session_state.get('price_results'):

            # Use a guard flag to only save once per analysis
            if st.session_state.get('saved_to_history') is not True:
                try:
                    image_buffer = io.BytesIO()
                    # ensure we have Pillow Image object
                    if isinstance(st.session_state.uploaded_img, Image.Image):
                        st.session_state.uploaded_img.save(image_buffer, format="PNG")
                    else:
                        # if it's a raw bytes object from file_uploader, convert
                        st.session_state.uploaded_img.save(image_buffer, format="PNG")
                    added = add_to_history(
                        st.session_state.username,
                        st.session_state.identified_product,
                        st.session_state.confidence,
                        image_buffer.getvalue(),
                        st.session_state.price_results
                    )
                    st.session_state['saved_to_history'] = True
                    if added:
                        st.toast = st.success("Saved search to history.")
                    else:
                        # duplicate prevented — no action needed
                        st.info("Result already saved recently; skipping duplicate save.")
                except Exception as e:
                    st.error(f"Unable to save history: {e}")
    
            # Add a separator after each row
        
# ===========================
# MY PROFILE PAGE
# ===========================
def profile_page():
    # Apply CSS styles for a modern look
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {BACKGROUND_COLOR};
        }}
        .profile-card {{
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-top: 20px;
        }}
        .stButton>button {{
            background: linear-gradient(90deg, {PRIMARY_COLOR}, {ACCENT_COLOR});
            color: white !important;
            border: none;
            padding: 10px 18px;
            border-radius: 10px;
            font-size: 15px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.3s;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        }}
        .stButton>button:hover {{
            background: linear-gradient(90deg, {ACCENT_COLOR}, {PRIMARY_COLOR});
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(0,0,0,0.3);
        }}

        /* ✅ Remove unwanted white box below heading */
        div[data-testid="stVerticalBlock"] > div:has(h2) + div {{
            background: transparent !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    show_dashboard_header("My Profile")
    st.markdown(f"<h2 style='text-align:center; color:{ACCENT_COLOR};'>Personal Details</h2>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    /* Remove unwanted white box below heading */
    div[data-testid="stVerticalBlock"] > div:has(h2) + div {
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

    # Ensure user is logged in
    if 'username' not in st.session_state or not st.session_state.username:
        st.warning("⚠️ Please log in to view your profile.")
        return

    # Fetch user data
    if 'user_data' not in st.session_state:
        user_data = get_user_data(st.session_state.username)
        if user_data:
            st.session_state.user_data = user_data
        else:
            st.error("❌ Unable to fetch user data from database.")
            return

    # Initialize edit mode flag
    if 'editing_profile' not in st.session_state:
        st.session_state.editing_profile = False

    st.markdown('<div class="profile-card">', unsafe_allow_html=True)

    if st.session_state.editing_profile:
        # ---------------------------
        # ✏️ EDIT PROFILE SECTION
        # ---------------------------
        with st.form("edit_profile_form"):
            st.subheader("Edit Details")

            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Full Name", st.session_state.user_data['name'])
                new_email = st.text_input("Email", st.session_state.user_data['email'])
                new_dob = st.text_input("Date of Birth", st.session_state.user_data['dob'])
            with col2:
                new_age = st.number_input("Age", min_value=1, max_value=120, value=st.session_state.user_data['age'])
                new_gender = st.selectbox("Gender", ["Male", "Female", "Other"],
                                          index=["Male", "Female", "Other"].index(st.session_state.user_data['gender']))
                new_address = st.text_input("Address", st.session_state.user_data['address'])

            col_save, col_cancel = st.columns(2)
            save = col_save.form_submit_button("💾 Save Changes")
            cancel = col_cancel.form_submit_button("❌ Cancel")

            if save:
                success = update_user_data(
                    username=st.session_state.user_data['username'],
                    name=new_name,
                    age=new_age,
                    dob=new_dob,
                    gender=new_gender,
                    address=new_address,
                    email=new_email,
                )
                if success:
                    st.session_state.user_data.update({
                        'name': new_name,
                        'email': new_email,
                        'dob': new_dob,
                        'age': new_age,
                        'gender': new_gender,
                        'address': new_address,
                    })
                    st.session_state.editing_profile = False
                    st.success("✅ Profile updated successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to update profile.")
            elif cancel:
                st.session_state.editing_profile = False
                st.rerun()

    else:
        # ---------------------------
        # 👤 VIEW PROFILE SECTION
        # ---------------------------
        st.info("Click 'Edit Profile' to change your details.")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Full Name:** {st.session_state.user_data['name']}")
            st.markdown(f"**Username:** {st.session_state.user_data['username']}")
            st.markdown(f"**Email:** {st.session_state.user_data['email']}")
            st.markdown(f"**Date of Birth:** {st.session_state.user_data['dob']}")
        with col2:
            st.markdown(f"**Age:** {st.session_state.user_data['age']}")
            st.markdown(f"**Gender:** {st.session_state.user_data['gender']}")
            st.markdown(f"**Address:** {st.session_state.user_data['address']}")

        st.markdown("---")
        if st.button("✏️ Edit Profile"):
            st.session_state.editing_profile = True
            st.rerun()

        # ---------------------------
        # 🔒 PASSWORD CHANGE SECTION
        # ---------------------------
        st.markdown("### 🔒 Change Password")
        with st.form("password_change_form"):
            current_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            submitted = st.form_submit_button("Update Password")

            if submitted:
                if not current_pw or not new_pw or not confirm_pw:
                    st.warning("Please fill all fields.")
                elif new_pw != confirm_pw:
                    st.error("❌ New passwords do not match.")
                else:
                    hashed_current = make_hash(current_pw)
                    user = login_user(st.session_state.username, hashed_current)
                    if user:
                        new_hashed_pw = make_hash(new_pw)
                        if reset_password(st.session_state.username, new_hashed_pw):
                            st.success("✅ Password changed successfully!")
                        else:
                            st.error("❌ Failed to update password in database.")
                    else:
                        st.error("❌ Current password is incorrect.")

    st.markdown('</div>', unsafe_allow_html=True)



# ===========================
# MY SAVED PRODUCTS PAGE
# ===========================
# def saved_products_page():
    # show_dashboard_header("My Saved Products")
    # st.markdown(f"<h2 style='text-align:center; color:{ACCENT_COLOR};'>⭐ Your Favorite Products</h2>", unsafe_allow_html=True)

    # if not st.session_state.get('saved_products'):
    #     st.info("You haven't saved any products yet. Go to the Dashboard to analyze and save.")
    #     return

    # # Use a unique key for deletion based on the product's timestamp
    # for i, item in enumerate(st.session_state.saved_products):
    #     st.markdown(f"<div style='border: 1px solid #ccc; border-radius: 8px; padding: 15px; margin-bottom: 15px; background-color: white;'>", unsafe_allow_html=True)
        
    #     col_img, col_details, col_price, col_action = st.columns([1, 4, 1.5, 1.5])
        
    #     # 1. Image
    #     col_img.image(item['image'], width=60)
        
    #     # 2. Details
    #     col_details.markdown(f"**Product:** {item['product']}")
    #     col_details.markdown(f"Saved On: {item['timestamp']}")
        
    #     # 3. Lowest Price from saved results
    #     lowest_price = min(
    #         [r['Price (₹)'] for r in item['results'] if r['Price (₹)'] is not None], 
    #         default=None
    #     )
    #     price_display = f"₹ {lowest_price:,}" if lowest_price is not None else "N/A"
    #     col_price.markdown(f"<div style='font-size: 24px; font-weight: 900; color: {PRIMARY_COLOR};'>{price_display}</div>", unsafe_allow_html=True)
    #     col_price.markdown("Lowest Price Found")
        
    #     # 4. Action
    #     if col_action.button("View Deals", key=f'view_deals_{item["timestamp"]}_{i}'):
    #         # Load product data back to dashboard
    #         st.session_state.identified_product = item['product']
    #         st.session_state.confidence = item['confidence']
    #         st.session_state.price_results = item['results']
    #         st.session_state.uploaded_img = item['image']
    #         st.session_state.page = 'dashboard'
    #         st.rerun()
        
    #     if col_action.button("❌ Remove", key=f'remove_{item["timestamp"]}_{i}'):
    #         st.session_state.saved_products.pop(i)
    #         st.success(f"Removed {item['product']} from saved products.")
    #         st.rerun()

    #     st.markdown("</div>", unsafe_allow_html=True)


# ===========================
# MY HISTORY PAGE
# ===========================
from utils import show_dashboard_header 
def history_page():
    show_dashboard_header("My History")

    st.markdown("<h2 style='text-align:center; color:#2C3E50;'>📜 Recently Analyzed Products</h2>", unsafe_allow_html=True)

    username = st.session_state.get('username', None)
    if not username:
        st.warning("Please log in to view your product history.")
        return

    # Always fetch a fresh history at the start of the render
    history = get_user_history(username)

    if not history:
        st.info("Your history is empty. Analyze a product image on the Dashboard to start tracking!")
        return

    # Clear All (confirm+clear)
    if st.button("🗑 Clear All History", key="clear_all_history"):
        clear_user_history(username)
        st.session_state['view_details_id'] = None
        st.success("✅ All history cleared successfully!")
        st.rerun()


    # Render each row
    for item in history:
        with st.container():
            st.markdown("<hr>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 4, 1])

            # Image
            if item['image']:
                try:
                    image = Image.open(BytesIO(item['image']))
                    col1.image(image, width=100)
                except Exception:
                    col1.write("Image error")
            else:
                col1.write("No Image")

            # Info
            col2.markdown(f"**Product:** {item['product']}")
            col2.markdown(f"**Confidence:** {item['confidence']:.2f}%")
            col2.markdown(f"**Analyzed On:** {item['timestamp']}")

            # Buttons
            view_key = f"view_{item['id']}"
            del_key = f"delete_{item['id']}"

            view_btn = col3.button("View Details", key=view_key)
            del_btn = col3.button("Delete", key=del_key)

            # Delete: remove from DB then rerun so we fetch fresh rows
            if del_btn:
                success = delete_history_item(item['id'], username)
                if success:
                    st.success(f"🗑 Deleted {item['product']} from history!")
                else:
                    st.error("Could not delete (check owner/ID).")
                st.rerun()


            # View toggle: toggle open/close the selected item
            if view_btn:
                if st.session_state.get('view_details_id') == item['id']:
                    st.session_state['view_details_id'] = None
                else:
                    st.session_state['view_details_id'] = item['id']

            # Show details for only the selected item
            if st.session_state.get('view_details_id') == item['id']:
                st.markdown(f"<h4 style='color:#1E88E5;'>💵 Price Comparison for {item['product']}</h4>", unsafe_allow_html=True)
                results = item.get('results', [])
                if isinstance(results, list) and results:
                    for res in results:
                        with st.expander(f"🔹 {res.get('Website', 'Unknown Site')}"):
                            st.write(f"**Title:** {res.get('Title', 'N/A')}")
                            st.write(f"**Price (₹):** {res.get('Price (₹)', 'N/A')}")
                            st.write(f"**Rating:** {res.get('Rating', 'N/A')}")
                            st.write(f"**Reviews:** {res.get('Reviews', 'N/A')}")
                            st.write(f"**Delivery:** {res.get('Delivery Date', 'N/A')}")
                            url = res.get('URL', '#')
                            st.markdown(f"[🔗 Go to Deal]({url})", unsafe_allow_html=True)
                else:
                    st.info("No detailed results available.")



# LOGIN / SIGNUP (No change here)
# ===========================
def login_page():
    show_topbar()
    
    # Updated tab headers for better visual integration
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Create Account"])

    with tab1:
        st.markdown(f"<h2 style='text-align:center; color:{PRIMARY_COLOR};'>🚀 Log in now to Save Big 💰 and Shop Smart 🛒</h2>", unsafe_allow_html=True)
        st.subheader("Login to compario")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                hashed_pw = make_hash(password)
                result = login_user(username, hashed_pw)
                if result:
                    st.session_state.logged_in = True
                    st.session_state.username = result[1]
                    st.session_state.name = result[3] if len(result) > 3 else result[1]
                    st.success(f"Welcome back, {st.session_state.name}!")
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("Invalid Username or Password.")

    with tab2:
        st.markdown(f"<h2 style='text-align:center; color:{PRIMARY_COLOR};'>🌟 Become a Member of compario and Shop Smart Every Day! 🛍💳</h2>", unsafe_allow_html=True)
        st.subheader("Create Your Compario Account")
        with st.form("signup_form"):
            st.markdown(f"<h3 style='color:{ACCENT_COLOR};'>Personal Details</h3>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *")
            with col2:
                email = st.text_input("Email Address *")
            col3, col4, col5 = st.columns(3)
            with col3:
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            with col4:
                age = st.number_input("Age", min_value=1, max_value=120, value=25)
            with col5:
                dob = st.date_input("Date of Birth")
            address = st.text_input("Address (optional)")

            st.markdown(f"<h3 style='color:{ACCENT_COLOR};'>Account Credentials</h3>", unsafe_allow_html=True)
            username = st.text_input("Username *")
            col6, col7 = st.columns(2)
            with col6:
                password = st.text_input("Password *", type="password")
            with col7:
                confirm_password = st.text_input("Confirm Password *", type="password")

            submitted = st.form_submit_button("Sign Up Now 🚀")
            if submitted:
                if not all([name, username, gender, age, dob, email, password, confirm_password]):
                    st.error("❌ Please fill all required fields (*).")
                elif password != confirm_password:
                    st.error("❌ Passwords do not match.")
                else:
                    error = validate_password(password)
                    if error:
                        st.error("❌ " + error)
                    else:
                        success = add_userdata(username, make_hash(password), name, age, str(dob), gender, address, email)
                        if success:
                            st.success("✅ Account created successfully! Please proceed to Login.")
                        else:
                            st.error("❌ Username already taken. Please choose a different username.")
                            
# ===========================
# MAIN EXECUTION
# ===========================
if "page" not in st.session_state:
    st.session_state.page = "home"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "name" not in st.session_state:
    st.session_state.name = None
# New state variables for price fetching results
if "identified_product" not in st.session_state:
    st.session_state.identified_product = None
if "confidence" not in st.session_state:
    st.session_state.confidence = 0
if "price_results" not in st.session_state:
    st.session_state.price_results = None
if "uploaded_img" not in st.session_state:
    st.session_state.uploaded_img = None


# ===========================
# MAIN EXECUTION (UPDATED)
# ===========================
page = st.session_state.page

if st.session_state.logged_in:
    # --- AUTHENTICATED USER FLOW (Uses Sidebar) ---
    show_sidebar() 
    
    if st.session_state.page == 'dashboard':
        dashboard_page()
    elif st.session_state.page == 'profile':
        profile_page()
    # elif st.session_state.page == 'saved_products':
    #     saved_products_page()
    elif st.session_state.page == 'history':
        history_page()
    elif st.session_state.page == 'logout':
        # Perform logout and redirect to home
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.name = None
        st.session_state.page = "home"
        st.rerun()
    else:
        # Default authenticated page
        dashboard_page()
else:
    # --- UN-AUTHENTICATED USER FLOW (Uses Topbar/Tabs) ---
    if page == "home":
        # show_topbar() is called inside home_page
        home_page() 
    elif page == "login":
        # show_topbar() is called inside login_page
        login_page()
    else:
        # Default unauthenticated page
        home_page()