import streamlit as st
import requests

# API endpoint
API_URL = "https://jane-ef36.onrender.com/execute/"

# Page title
st.title("SpaceAI Interface")
st.subheader("Interact with the SpaceAI API")

# Input fields for mode and query
mode = st.selectbox("Select Mode", [1, 2, 3], format_func=lambda x: f"Mode {x}")
query = st.text_area("Enter Your Query", placeholder="Type your query here...")

# File uploader for mode 3
uploaded_file = None
if mode == 3:
    st.subheader("Upload File")
    uploaded_file = st.file_uploader("Upload a file for content processing (Mode 3 only)", type=["txt", "pdf", "doc", "docx"])

# Submit button
if st.button("Execute"):
    if not query.strip():
        st.error("Query cannot be empty.")
    elif mode == 3 and not uploaded_file:
        st.error("Please upload a file when using Mode 3.")
    else:
        with st.spinner("Processing..."):
            try:
                # Prepare form data
                form_data = {"mode": mode, "query": query}
                files = None

                # Attach file for mode 3
                if mode == 3 and uploaded_file:
                    files = {
                        "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")
                    }

                # Send POST request
                response = requests.post(API_URL, data=form_data, files=files)

                # Process API response
                if response.status_code == 200:
                    data = response.json()
                    st.success("Query Executed Successfully!")
                    st.write("### Response")
                    st.markdown(data.get("response", "No response available"))
                else:
                    try:
                        error_message = response.json().get("detail", "Unknown error occurred.")
                    except ValueError:
                        error_message = response.text or "Unknown error occurred."
                    st.error(f"Error {response.status_code}: {error_message}")

            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
