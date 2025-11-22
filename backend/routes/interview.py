from fastapi import APIRouter

router = APIRouter()


@router.get("/get-domains")
def get_domains():
    return {"domains": []}


@router.post("/start-interview")
def start_interview():
    return {"message": "start-interview placeholder"}


@router.post("/process-answer")
def process_answer():
    return {"message": "process-answer placeholder"}


@router.post("/end-interview")
def end_interview():
    return {"message": "end-interview placeholder"}
