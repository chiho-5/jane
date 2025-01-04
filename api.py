from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
# from fastapi_sessions import SessionData, SessionManager
from space_ai import SpaceAI
import tempfile
import logging
import hashlib
# FastAPI instance
app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
# session_manager = SessionManager()


# In-memory store (for simplicity, consider a database in production)
processed_files = set()

def compute_file_hash(file_path: str) -> str:
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

@app.post("/execute/")
async def execute_query(
    mode: int = Form(...),
    query: str = Form(...),
    file: UploadFile = File(None),
    # session_data: SessionData = Depends(session_manager.get_session),
):
    """
    Unified endpoint to execute a query.
    For mode 3, accepts an uploaded file and passes its path to embedchain for processing.
    """
    try:
        # Create SpaceAI instance
        space_ai = SpaceAI(mode=mode, query=query)

        if mode == 3:
            if not file:
                raise HTTPException(status_code=400, detail="File must be uploaded for mode 3.")

            # Save uploaded file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
                temp_file.write(await file.read())
                temp_file_path = temp_file.name

            file_hash = compute_file_hash(temp_file_path)
            if file_hash in processed_files:
                return JSONResponse(content={"response": "File already processed. Skipping."})

            # Add the file hash to the set
            # session_data.setdefault("processed_files", set()).add(file_hash)
            processed_files.add(file_hash)
            # Execute Mode 3 with file path
            response = space_ai.execute_mode(content=temp_file_path)
        else:
            # Execute other modes without additional content
            response = space_ai.execute_mode()

        # Parse the response to extract the "answer"
        # Assuming the response is a JSON-like string with "query" and "answer" fields
        try:
            import json
            parsed_response = json.loads(response)  # Parse the response as JSON
            answer = parsed_response.get("answer", "Answer not found.")  # Default if no "answer" field
        except json.JSONDecodeError:
            # If the response is not JSON, fallback to previous logic
            answer_start = response.find("Answer:")
            if answer_start != -1:
                answer = response[answer_start + len("Answer:"):].strip()
            else:
                answer = response.strip()  # Return the full response if no "Answer:" is found

        return JSONResponse(content={"response": answer})

    except ValueError as e:
        logger.error(f"ValueError: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")




# @app.post("/execute/")
# async def execute_query(
#     mode: int = Form(...),
#     query: str = Form(...),
#     file: UploadFile = File(None),
# ):
#     """
#     Unified endpoint to execute a query.
#     For mode 3, accepts an uploaded file and passes its path to embedchain for processing.
#     """
#     try:
#         # Create SpaceAI instance
#         space_ai = SpaceAI(mode=mode, query=query)

#         if mode == 3:
#             if not file:
#                 raise HTTPException(status_code=400, detail="File must be uploaded for mode 3.")

#             # Save uploaded file to a temporary location
#             with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
#                 temp_file.write(await file.read())
#                 temp_file_path = temp_file.name

#             # Execute Mode 3 with file path
#             response = space_ai.execute_mode(content=temp_file_path)
#         else:
#             # Execute other modes without additional content
#             response = space_ai.execute_mode()

#         # Extract the answer from the response
#         answer_start = response.find("Answer:")
#         if answer_start != -1:
#             answer = response[answer_start + len("Answer:"):].strip()
#         else:
#             answer = response.strip()  # Return the full response if no "Answer:" is found

#         return JSONResponse(content={"response": answer})

#     except ValueError as e:
#         logger.error(f"ValueError: {e}")
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         logger.error(f"Unexpected error: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail="An unexpected error occurred.")
