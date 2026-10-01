from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from services.interview_service import create_session, get_session, save_answer
from request_model.AnswerRequest import AnswerRequest
from response_model.AnswerResponse import AnswerResponse
from models.interview import InterviewStatusEnum
from services.ai_service import generate_questions_intro, generate_report
from util.file_util import extract_text, validate_file

router = APIRouter(
    prefix= "/interview",
    tags= ["Interview"]
)

# @router.get('/')
# async def hello():
#     return "AI Platform Interview"

@router.post("/generate-question")
async def generate_questions(
    job_title: str = Form(...),
    job_description: str = Form(...),
    resume: UploadFile = File(...)
):
    # Validate resume file
    await validate_file(resume)

    # Extract text from resume
    resume_text = await extract_text(resume)

    # Generate questions and intro text using title, decription, resume content
    resp = await generate_questions_intro(job_title=job_title, job_description=job_description, resume_text=resume_text)

    session = create_session()
    session.questions = resp.get("questions")
    session.introText = resp.get("introText")

    return { "session_id": session.session_id }

@router.get('/start')
async def start_interview():
    questions = ["What is your name ?",
                 "What is javascript?",
                 "what is python?"]
    session = create_session()
    session.questions = questions
    return {
        "introText": "hello there ! What about you ?",
        "session_id": session.session_id,
        "firstQuestion": questions[0]
    }

@router.post('/submit', response_model=AnswerResponse)
async def submit_answer(answerReq: AnswerRequest):
 #Check validate session
    session = get_session(answerReq.session_id)
    if not session or session.status == InterviewStatusEnum.COMPLETED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview session not found")
    
 #Save answer in interview session
    save_answer(answerReq.answer, answerReq.skip, session)

 #return
    if session.status == InterviewStatusEnum.COMPLETED:
        return {
            "interviewEnded": True
        }

    return {
        "interviewEnded": False,
        "nextQuestion": session.questions[session.current_index]
    }

@router.put("/end/{session_id}")
async def end_interview(session_id: str):
    # check valide session id
    session = get_session(session_id)
    if not session or session.status == InterviewStatusEnum.COMPLETED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview Session Not Found")

    session.status = InterviewStatusEnum.COMPLETED

    return {
        "interviewEnded": True
    }

@router.get("/report/{session_id}")
async def report(session_id: str):
    # Check valid session
    session = get_session(session_id)
    if not session or session.status == InterviewStatusEnum.COMPLETED:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview Session Not Found")

    return {
         "result": "Interview Report Successfully created !"
    }

@router.get("/report/{session_id}")
async def report(session_id: str):
    # Check valid session_id
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview Session Not Found")
    
    resp = await generate_report(session.answers)

    return { "result":  resp }
