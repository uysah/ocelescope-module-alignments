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

@router.get("/{ocel_id}/alignments", operation_id="get_alignments")
def get_alignments(ocel:ApiOcel, object_type:str) -> AlignmentsResponse:
    return compute_alignments(ocel,object_type)


@router.get("/{ocel_id}/objects/types", operation_id="objectTypes")
def get_object_types(ocel: ApiOcel) -> list[str]:
    return ocel.objects.types