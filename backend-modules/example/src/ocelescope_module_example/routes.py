from fastapi import APIRouter
from pydantic import BaseModel
from ocelescope_module_example.models.alignment import AlignmentsResponse
from ocelescope_backend.app.dependencies import ApiSession, ApiOcel
from ocelescope_module_example.utils.alignments import compute_alignments
from ocelescope import PetriNet
from typing import Tuple

router = APIRouter()


class HelloResponse(BaseModel):
    message: str


@router.get("/hello", operation_id="hello", response_model=HelloResponse)
def hello() -> HelloResponse:
    return HelloResponse(message="Hello from the example backend module")

@router.get("/{ocel_id}/alignments", operation_id="get_alignments")
def get_alignments(ocel:ApiOcel) -> AlignmentsResponse:
    return compute_alignments(ocel)


@router.get("/debug/ocels")
def debug(session: ApiSession):
    return list(session.ocels.keys())