from pydantic import BaseModel
from typing import List,Dict,Any, Optional, Union, Tuple
from ocelescope import PetriNet

class VariantAlignmentResult(BaseModel):
    activities: List[str] # The variant's activity sequence
    frequency: int  # How many traces follow this variant
    result: Union[Dict[str, Any]] # The alignment result or error for this variant

class FitnessResult(BaseModel):
    average_fitness: float  # Average trace fitness (across all traces)
    log_fitness: float  # Log fitness, as the total computed fitness (summing up the costs for all traces)
    perfectly_fitting_frac: float  # Fraction of traces that perfectly fit (i.e., have an alignment cost of `0`)
    total_costs: int  # The total cost, summed up from all traces

class CostFunction(BaseModel):
    log_move_cost: int  # Default cost for a log move (log event not matched by model)
    model_move_cost: int  # Default cost for a model move (visible transition fires without matching log event)
    silent_move_cost: int  # Default cost for a silent/tau move
    sync_move_cost: int  # Default cost for a synchronous move


class AlignmentOptions (BaseModel):
    cost_fn: CostFunction  # Cost function for alignment moves
    max_states: Optional[Optional[int]]  # Maximum number of states to visit before aborting (per trace).

class TransitionStat(BaseModel):
    sync_fires: int
    model_fires: int

class Aggregated(BaseModel):
    total_traces: int
    transition_stats: Dict[str, TransitionStat]
    log_move_counts: Dict[str, int]

class NetPlace(BaseModel):
    id: str

class NetTransition(BaseModel):
    id: str
    label: str | None

class NetArc(BaseModel):
    nodes: Tuple[str, str]
    weight: int

class ResponseNet(BaseModel):
    places: List[NetPlace]
    transitions: List[NetTransition]
    arcs: List[NetArc]
    initial_marking: Dict[str, int]
    final_marking: Dict[str, int]

class AlignmentsResponse(BaseModel):
    net: ResponseNet
    variant_alignments: List[VariantAlignmentResult]
    fitness: FitnessResult
    aggregated: Aggregated

