from fastapi import FastAPI, HTTPException, UploadFile, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from agent import SpaceAI  # Ensure SpaceAI is correctly implemented and imported

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spaceai-api")

app = FastAPI()

# Pydantic model for chat request
class ChatRequest(BaseModel):
    user_id: str
    data_directory: str
    query: str
    mode: int

@app.post("/upload")
async def upload_file_endpoint(
    data_directory: str = Form(...), 
    uploaded_file: UploadFile = None
):
    try:
        if not uploaded_file:
            raise HTTPException(status_code=400, detail="No file uploaded.")

        # Initialize SpaceAI and save the uploaded file
        space_ai = SpaceAI(data_directory=data_directory, query=None, mode=None)
        file_path = await space_ai.save_uploaded_file(uploaded_file)

        logger.info(f"File uploaded successfully: {file_path}")
        return {"file_path": file_path}
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Initialize SpaceAI with chat parameters
        space_ai = SpaceAI(
            data_directory=request.data_directory, 
            query=request.query, 
            mode=request.mode
        )
        response, urls = await space_ai.handle_user_message(request.user_id)

        logger.info(f"User {request.user_id} query: {request.query}")
        logger.info(f"Response: {response}")
        return {"response": response, "urls": urls}
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")
