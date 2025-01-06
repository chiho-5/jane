# import streamlit as st
# import requests

# # Base URL of the FastAPI application
# API_BASE_URL = "http://localhost:8000"

# # Streamlit app title
# st.title("SpaceAI Client")

# # Sidebar for navigation
# st.sidebar.title("Navigation")
# options = ["Upload Files", "Chat"]
# selected_option = st.sidebar.selectbox("Choose an option:", options)

# if selected_option == "Upload Files":
#     st.header("Upload Files")
#     data_directory = st.text_input("Enter data directory:", value="./data")
#     uploaded_file = st.file_uploader("Upload a file", type=["txt", "pdf", "csv", "docx"])

#     if st.button("Upload"):
#         if not uploaded_file:
#             st.error("Please upload a file.")
#         elif not data_directory:
#             st.error("Please specify a data directory.")
#         else:
#             with st.spinner("Uploading file..."):
#                 # Prepare the form data
#                 files = {"uploaded_file": uploaded_file}
#                 data = {"data_directory": data_directory}
#                 try:
#                     # Call the FastAPI /upload endpoint
#                     response = requests.post(
#                         f"{API_BASE_URL}/upload",
#                         files={"uploaded_file": uploaded_file},
#                         data=data,
#                     )
#                     if response.status_code == 200:
#                         file_path = response.json().get("file_path")
#                         st.success(f"File uploaded successfully! Saved to: {file_path}")
#                     else:
#                         st.error(f"Error: {response.json().get('detail')}")
#                 except Exception as e:
#                     st.error(f"An error occurred: {str(e)}")

# elif selected_option == "Chat":
#     st.header("Chat with SpaceAI")
#     user_id = st.text_input("Enter User ID:")
#     data_directory = st.text_input("Enter data directory (used in chat):", value="./data")
#     query = st.text_area("Enter your query:")
#     mode = st.selectbox("Select mode:", options=[1, 2], index=0)

#     if st.button("Send Query"):
#         if not user_id or not data_directory or not query:
#             st.error("Please provide all the required fields.")
#         else:
#             with st.spinner("Processing your query..."):
#                 try:
#                     # Call the FastAPI /chat endpoint
#                     response = requests.post(
#                         f"{API_BASE_URL}/chat",
#                         data={
#                             "user_id": user_id,
#                             "data_directory": data_directory,
#                             "query": query,
#                             "mode": mode,
#                         },
#                     )
#                     if response.status_code == 200:
#                         chat_response = response.json().get("response")
#                         st.success("Response from SpaceAI:")
#                         st.write(chat_response)
#                     else:
#                         st.error(f"Error: {response.json().get('detail')}")
#                 except Exception as e:
#                     st.error(f"An error occurred: {str(e)}")


import streamlit as st
import requests

# Base URL of the FastAPI application
API_BASE_URL = "http://localhost:8000"

# Streamlit app title
st.title("SpaceAI Client")

# Sidebar for navigation
st.sidebar.title("Navigation")
options = ["Upload Files", "Chat"]
selected_option = st.sidebar.selectbox("Choose an option:", options)

if selected_option == "Upload Files":
    st.header("Upload Files")
    data_directory = st.text_input("Enter data directory:", value="./data")
    uploaded_file = st.file_uploader("Upload a file", type=["txt", "pdf", "csv", "docx"])

    if st.button("Upload"):
        if not uploaded_file:
            st.error("Please upload a file.")
        elif not data_directory:
            st.error("Please specify a data directory.")
        else:
            with st.spinner("Uploading file..."):
                # Prepare the form data
                files = {"uploaded_file": uploaded_file}
                data = {"data_directory": data_directory}
                try:
                    # Call the FastAPI /upload endpoint
                    response = requests.post(
                        f"{API_BASE_URL}/upload",
                        files={"uploaded_file": uploaded_file},
                        data=data,
                    )
                    if response.status_code == 200:
                        file_path = response.json().get("file_path")
                        st.success(f"File uploaded successfully! Saved to: {file_path}")
                    else:
                        st.error(f"Error: {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

elif selected_option == "Chat":
    st.header("Chat with SpaceAI")
    user_id = st.text_input("Enter User ID:")
    data_directory = st.text_input("Enter data directory (used in chat):", value="./data")
    query = st.text_area("Enter your query:")
    mode = st.selectbox("Select mode:", options=[1, 2, 3], index=0)

    if st.button("Send Query"):
        if not user_id or not data_directory or not query:
            st.error("Please provide all the required fields.")
        else:
            with st.spinner("Processing your query..."):
                try:
                    # Ensure the payload is sent as JSON
                    payload = {
                        "user_id": user_id,
                        "data_directory": data_directory,
                        "query": query,
                        "mode": mode,
                    }
                    response = requests.post(
                        f"{API_BASE_URL}/chat",
                        json=payload,  # Use the json parameter here
                    )
                    if response.status_code == 200:
                        chat_response = response.json().get("response")
                        urls = response.json().get("urls", [])
                        st.success("Response from SpaceAI:")
                        st.write(chat_response)
                        if urls:
                            st.info("Indexed URLs:")
                            for url in urls:
                                st.write(url)
                    else:
                        st.error(f"Error: {response.json().get('detail')}")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
