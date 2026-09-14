from fastapi import APIRouter,HTTPException
from pydantic import BaseModel
from ocelescope_module_example.models.alignment import AlignmentsResponse
from ocelescope_backend.app.dependencies import ApiSession, ApiOcel
from ocelescope_module_example.utils.alignments import compute_alignments, AlignmentComputationError
from ocelescope import PetriNet
from typing import cast
from ocelescope_backend.app.sse_manager import ErrorNotification, sse_manager

router = APIRouter()


class HelloResponse(BaseModel):
    message: str


@router.get("/{ocel_id}/alignments", operation_id="get_alignments")
def get_alignments(
    ocel: ApiOcel, session: ApiSession, object_type: str, resource_id: str | None = None
) -> AlignmentsResponse:
    try:
        if resource_id:
            resource_store = cast(PetriNet,session.get_resource(resource_id))
            petri_net = PetriNet(**resource_store.data)
        else:
            petri_net = None 

        return compute_alignments(ocel, object_type, petri_net)
    except AlignmentComputationError as e:
        sse_manager.send_safe(
            session_id=session.id,
            message=ErrorNotification(
                type="error",
                title="Alignment computation failed",
                message=str(e),
                trace=e.trace
            ),
        )
        raise HTTPException(status_code=422, detail=str(e)) from e



@router.get("/{ocel_id}/objects/types", operation_id="objectTypes")
def get_object_types(ocel: ApiOcel) -> list[str]:
    return ocel.objects.types
