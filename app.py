import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
from PIL import Image
import io
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Page config
st.set_page_config(
    page_title="No Bad Days Club - Challenge Verifier",
    page_icon="🎒",
    layout="wide"
)

# Initialize session state for data persistence
if 'task_data' not in st.session_state:
    st.session_state.task_data = pd.DataFrame({
        'task_id': [1, 2, 3],
        'task_desc': [
            'upload a pic of JP Licks Ice cream',
            'upload a pic of Mikes Pastry\'s Cannoli',
            'upload a receipt of mango Smoothie from Trader Joe\'s'
        ],
        'points': [50, 75, 100]
    })

if 'player_data' not in st.session_state:
    st.session_state.player_data = pd.DataFrame({
        'player_id': [1, 2, 3],
        'player_name': ['vizzy', 'lindsay', 'shreya']
    })

if 'transaction_data' not in st.session_state:
    st.session_state.transaction_data = pd.DataFrame({
        'pk': ['a11111', 'a21221', 'a32132', 'a42222', 'a53113', 'a63212'],
        'player_id': [1, 2, 3, 2, 3, 3],
        'task_id': [1, 2, 1, 2, 1, 2],
        'timestamp': [
            '2025-09-01T14:30:22',
            '2025-09-01T15:12:45',
            '2025-09-02T09:45:33',
            '2025-09-02T10:22:18',
            '2025-09-03T13:15:29',
            '2025-09-03T14:01:56'
        ],
        'points_earned': [50, 50, 75, 75, 75, 75]
    })

# NEW: human review queue
if 'human_review_queue' not in st.session_state:
    st.session_state.human_review_queue = pd.DataFrame(columns=[
        'player_id', 'player_name', 'task_desc', 'reason', 'submitted_at'
    ])

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .badge-card {
        background: #f7f3ff;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #764ba2;
    }
    .stats-box {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🎒 No Bad Days Club</h1>
    <p>Gamified Challenge Verifier - Demo Version</p>
</div>
""", unsafe_allow_html=True)

# Sidebar navigation
page = st.sidebar.selectbox(
    "Navigate",
    ["🏠 User Dashboard", "📊 Admin Panel", "⚙️ Settings"]
)

# Function to verify image with Gemini
def verify_image_with_gemini(image, task_description, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        prompt = f"""
        You are verifying an uploaded receipt for a gamified challenge app. 
        The user needs to: {task_description}

        Specifically check if the receipt is from Trader Joe's and contains an item 
        matching "Mango Smoothie" (case-insensitive, small variations acceptable).

        Please analyze the image and determine if it successfully completes the challenge.

        Respond with ONLY:
        1. "VERIFIED" or "NOT VERIFIED"
        2. A brief explanation (one sentence)
        3. Confidence percentage (0-100)

        Format: VERIFIED|Explanation|95
        """


        response = model.generate_content([prompt, Image.open(io.BytesIO(img_byte_arr))])
        return response.text.strip()

    except Exception as e:
        return f"ERROR|Failed to verify: {str(e)}|0"

# Function to resize image while maintaining aspect ratio
def resize_image(image, max_width=400):
    """Resize image to have a maximum width while maintaining aspect ratio"""
    width, height = image.size
    if width > max_width:
        ratio = max_width / width
        new_width = max_width
        new_height = int(height * ratio)
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return image

# USER DASHBOARD
if page == "🏠 User Dashboard":
    st.title("Complete Your Challenge! 🎯")

    col1, col2 = st.columns([2, 1])
    with col1:
        # Select player
        st.subheader("👤 Select Your Profile")
        selected_player = st.selectbox(
            "Choose your username:",
            st.session_state.player_data['player_name'].tolist()
        )
        player_id = st.session_state.player_data[
            st.session_state.player_data['player_name'] == selected_player
        ]['player_id'].values[0]

        st.divider()

        # Select task
        st.subheader("🎯 Select Your Challenge")
        task_options = [f"{row['task_desc']} (+{row['points']} points)" for _, row in st.session_state.task_data.iterrows()]
        selected_task_display = st.selectbox("Choose a challenge to complete:", task_options)

        task_index = task_options.index(selected_task_display)
        selected_task_id = st.session_state.task_data.iloc[task_index]['task_id']
        selected_task_desc = st.session_state.task_data.iloc[task_index]['task_desc']
        selected_task_points = st.session_state.task_data.iloc[task_index]['points']

        st.markdown(f"""
        <div class="badge-card">
            <h4>Challenge Details:</h4>
            <p><strong>📝 Task:</strong> {selected_task_desc}</p>
            <p><strong>🏆 Points:</strong> {selected_task_points}</p>
            <p><strong>📍 Location:</strong> Boston, MA</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Upload proof
        st.subheader("📸 Upload Your Proof")
        uploaded_file = st.file_uploader("Choose an image...", type=['png', 'jpg', 'jpeg'])

        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            
            # Create two columns for the image display
            img_col1, img_col2 = st.columns([1, 2])
            
            st.info("📷 Image uploaded successfully! Click 'Submit Challenge' to verify.")
            
            with img_col1:
                # Resize image for display (keeping original for verification)
                display_image = resize_image(image, max_width=300)
                st.image(display_image, caption="Your uploaded image", use_container_width=True)
            
            # with img_col2:
            #     st.info("📷 Image uploaded successfully! Click 'Submit Challenge' to verify.")

            if st.button("🚀 Submit Challenge", type="primary", use_container_width=True):
                if api_key:
                    with st.spinner("🔍 Verifying your challenge with AI..."):
                        progress_bar = st.progress(0)
                        for i in range(100):
                            time.sleep(0.01)
                            progress_bar.progress(i + 1)

                        result = verify_image_with_gemini(image, selected_task_desc, api_key)

                        parts = result.split('|')
                        if len(parts) >= 3:
                            status, explanation, confidence = parts[0], parts[1], parts[2]
                        else:
                            status, explanation, confidence = "ERROR", result, "0"

                        # Store verification result in session state
                        st.session_state['last_verification'] = {
                            'status': status,
                            'explanation': explanation,
                            'confidence': confidence,
                            'player_id': player_id,
                            'player_name': selected_player,
                            'task_desc': selected_task_desc,
                            'task_id': selected_task_id,
                            'task_points': selected_task_points
                        }

                        if "VERIFIED" in status and "NOT" not in status:
                            st.balloons()
                            st.success(f"""
                            ✅ **Challenge Completed!**
                            🎯 {explanation}
                            📊 Confidence: {confidence}%
                            You earned **{selected_task_points} points**!
                            """)

                            new_transaction = {
                                'pk': f'a{len(st.session_state.transaction_data)+1}{player_id}{selected_task_id}',
                                'player_id': player_id,
                                'task_id': selected_task_id,
                                'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                                'points_earned': selected_task_points
                            }
                            st.session_state.transaction_data = pd.concat([
                                st.session_state.transaction_data,
                                pd.DataFrame([new_transaction])
                            ], ignore_index=True)

                        else:
                            st.error(f"""
                            ❌ **Challenge Not Verified**
                            {explanation}
                            Please try again with a clearer image that matches the challenge requirements.
                            """)
                else:
                    st.error("🚨 GOOGLE_API_KEY is not set. Please add it to your Streamlit Cloud secrets.")
                    
            # Handle human review button separately
            if 'last_verification' in st.session_state:
                verification = st.session_state['last_verification']
                if "VERIFIED" not in verification['status'] or "NOT" in verification['status']:
                    if st.button("🧑‍⚖️ Submit for Human Review", type="secondary", use_container_width=True):
                        new_review = {
                            'player_id': verification['player_id'],
                            'player_name': verification['player_name'],
                            'task_desc': verification['task_desc'],
                            'reason': verification['explanation'],
                            'submitted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        st.session_state.human_review_queue = pd.concat([
                            st.session_state.human_review_queue,
                            pd.DataFrame([new_review])
                        ], ignore_index=True)
                        st.success("✅ Submitted for human verification! The admin team will review it.")
                        # Clear the last verification to hide the button
                        del st.session_state['last_verification']
                        # st.rerun()

    with col2:
        st.subheader("📊 Your Stats")
        player_transactions = st.session_state.transaction_data[
            st.session_state.transaction_data['player_id'] == player_id
        ]
        total_points = player_transactions['points_earned'].sum() if not player_transactions.empty else 0
        st.metric("Total Points", f"{total_points} 🏆")
        st.metric("Challenges Completed", f"{len(player_transactions)} ✅")

        st.subheader("🏆 Leaderboard")
        leaderboard = st.session_state.transaction_data.groupby('player_id').agg({
            'points_earned': 'sum'
        }).reset_index().merge(st.session_state.player_data, on='player_id')
        leaderboard = leaderboard.sort_values('points_earned', ascending=False)
        leaderboard['rank'] = range(1, len(leaderboard) + 1)
        for _, player in leaderboard.iterrows():
            if player['player_name'] == selected_player:
                st.markdown(f"**#{player['rank']} {player['player_name']} - {player['points_earned']} pts** ⭐")
            else:
                st.markdown(f"#{player['rank']} {player['player_name']} - {player['points_earned']} pts")

# ADMIN PANEL
elif page == "📊 Admin Panel":
    st.title("Admin Dashboard 🎛️")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Players", len(st.session_state.player_data))
    with col2:
        st.metric("Total Challenges", len(st.session_state.task_data))
    with col3:
        st.metric("Completions", len(st.session_state.transaction_data))
    with col4:
        st.metric("Points Awarded", st.session_state.transaction_data['points_earned'].sum())

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Tasks", "👥 Players", "📝 Transactions", "🧑‍⚖️ Human Review"])

    with tab1:
        st.markdown("### Current Tasks")
        st.dataframe(st.session_state.task_data, use_container_width=True)
        
        # Add new task
        st.markdown("### Add New Task")
        col1, col2 = st.columns(2)
        with col1:
            new_task_desc = st.text_input("Task Description")
        with col2:
            new_task_points = st.number_input("Points", min_value=10, max_value=500, step=5)
        
        if st.button("Add Task"):
            if new_task_desc:
                new_task = pd.DataFrame({
                    'task_id': [len(st.session_state.task_data) + 1],
                    'task_desc': [new_task_desc],
                    'points': [new_task_points]
                })
                st.session_state.task_data = pd.concat(
                    [st.session_state.task_data, new_task],
                    ignore_index=True
                )
                st.success("Task added successfully!")
                st.rerun()

    with tab2:
        st.markdown("### Current Players")
        st.dataframe(st.session_state.player_data, use_container_width=True)
        
        # Add new player
        st.markdown("### Add New Player")
        new_player_name = st.text_input("Player Name")
        
        if st.button("Add Player"):
            if new_player_name:
                new_player = pd.DataFrame({
                    'player_id': [len(st.session_state.player_data) + 1],
                    'player_name': [new_player_name]
                })
                st.session_state.player_data = pd.concat(
                    [st.session_state.player_data, new_player],
                    ignore_index=True
                )
                st.success("Player added successfully!")
                st.rerun()
    
    with tab3:
        st.markdown("### Transaction History")
        
        # Merge data for better display
        display_data = st.session_state.transaction_data.merge(
            st.session_state.player_data, on='player_id'
        ).merge(
            st.session_state.task_data, on='task_id'
        )
        
        display_data = display_data[['pk', 'player_name', 'task_desc', 'timestamp', 'points_earned']]
        display_data = display_data.sort_values('timestamp', ascending=False)
        
        st.dataframe(display_data, use_container_width=True)

    with tab4:
        st.subheader("Human Review Queue")
        if st.session_state.human_review_queue.empty:
            st.info("No pending human reviews 🚀")
        else:
            # Let admin pick a row to review
            review_options = [
                f"{row.player_name} - {row.task_desc} ({row.submitted_at})"
                for _, row in st.session_state.human_review_queue.iterrows()
            ]
            selected_index = st.selectbox(
                "Select a review to inspect:",
                range(len(review_options)),
                format_func=lambda i: review_options[i]
            )

            # Get the selected row
            review = st.session_state.human_review_queue.iloc[selected_index]

            st.markdown(f"""
            **👤 Player:** {review['player_name']}  
            **🎯 Task:** {review['task_desc']}  
            **📌 Reason:** {review['reason']}  
            **🕒 Submitted:** {review['submitted_at']}  
            """)

            colA, colB = st.columns(2)
            with colA:
                if st.button("✅ Accept", key=f"accept_{selected_index}"):
                    # Find task points
                    task_points = st.session_state.task_data[
                        st.session_state.task_data['task_desc'] == review['task_desc']
                    ]['points'].values[0]

                    new_transaction = {
                        'pk': f'a{len(st.session_state.transaction_data)+1}{review["player_id"]}',
                        'player_id': review['player_id'],
                        'task_id': st.session_state.task_data[
                            st.session_state.task_data['task_desc'] == review['task_desc']
                        ]['task_id'].values[0],
                        'timestamp': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
                        'points_earned': task_points
                    }
                    st.session_state.transaction_data = pd.concat([
                        st.session_state.transaction_data,
                        pd.DataFrame([new_transaction])
                    ], ignore_index=True)

                    # Remove from human review queue
                    st.session_state.human_review_queue = (
                        st.session_state.human_review_queue.drop(review.name)
                    )
                    st.success(f"✅ Challenge approved for {review['player_name']}!")
                    st.rerun()

            with colB:
                if st.button("❌ Reject", key=f"reject_{selected_index}"):
                    st.session_state.human_review_queue = (
                        st.session_state.human_review_queue.drop(review.name)
                    )
                    st.warning(f"❌ Challenge rejected for {review['player_name']}.")
                    st.rerun()

# SETTINGS
elif page == "⚙️ Settings":
    st.title("Settings ⚙️")
    st.info("Demo configuration and export options here...")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🎒 No Bad Days Club - Demo Version</p>
    <p>Where adventure is the currency.</p>
</div>
""", unsafe_allow_html=True)
