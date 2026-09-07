from ocelescope import PetriNet
from ocelescope_module_example.models.alignment import VariantAlignmentResult, AlignmentOptions,FitnessResult, Aggregated, TransitionStat, AlignmentsResponse, Net, NetArc, NetPlace, NetTransition
from typing import Optional,Tuple, List, Dict
import r4pm
import polars
from ocelescope import  OCEL
from r4pm.bindings.discovery.case_centric.alphappp.full import PetriNet as R4PMPetriNet
import uuid


def to_r4pm_format(petri_net: PetriNet) -> R4PMPetriNet:
    place_ids = {p.name: str(uuid.uuid4()) for p in petri_net.places}
    transition_ids = {t.name: str(uuid.uuid4()) for t in petri_net.transitions}
    def node_id(name: str) -> str:
        return place_ids.get(name) or transition_ids[name]

    places = {pid: {"id": pid} for pid in place_ids.values()}

    transitions = {tid: {"id": tid, "label": t.label} for t, tid in ((t, transition_ids[t.name]) for t in petri_net.transitions)}

    arcs = [
        {
            "from_to": {
                "type": "PlaceTransition" if arc.source in place_ids else "TransitionPlace",
                "nodes": [node_id(arc.source), node_id(arc.target)],
            },
            "weight": arc.weight,
        }
        for arc in petri_net.arcs
    ]

    initial_marking = {place_ids[name]: count for name, count in petri_net.initial_marking.items()}
    final_marking = {place_ids[name]: count for name, count in petri_net.final_marking.items()}

    return {
        "places": places,
        "transitions": transitions,
        "arcs": arcs,
        "initial_marking": initial_marking,
        "final_markings": [final_marking] if final_marking else [],
    }

def flatten(petri_net: PetriNet, object_type: str) -> PetriNet:
    place_names = {p.name for p in petri_net.places if p.object_type == object_type}
    places_flatten = [p for p in petri_net.places if p.name in place_names]

    arcs_flatten = []
    connected_transition_names = set()
    for arc in petri_net.arcs:
        source_is_place = arc.source in place_names
        target_is_place = arc.target in place_names
        if not (source_is_place or target_is_place):
            continue
        arcs_flatten.append(arc)
        if not source_is_place:
            connected_transition_names.add(arc.source)
        if not target_is_place:
            connected_transition_names.add(arc.target)

    transitions_flatten = [t for t in petri_net.transitions if t.name in connected_transition_names]

    initial_marking_flatten = {name: count for name, count in petri_net.initial_marking.items() if name in place_names}
    final_marking_flatten = {name: count for name, count in petri_net.final_marking.items() if name in place_names}

    return PetriNet(
        places=places_flatten,
        transitions=transitions_flatten,
        arcs=arcs_flatten,
        initial_marking=initial_marking_flatten,
        final_marking=final_marking_flatten,
    )

def convert_net(petri_net: R4PMPetriNet) -> Net:
    places = [NetPlace(id=p_id) for p_id in petri_net["places"].keys()]
    transitions = [
        NetTransition(id=t_id, label=t.get("label"))
        for t_id, t in petri_net["transitions"].items()
    ]
    arcs = [
        NetArc(
            nodes=(arc["from_to"]["nodes"][0], arc["from_to"]["nodes"][1]),
            weight=arc["weight"],
        )
        for arc in petri_net["arcs"]
    ]
    initial_marking = petri_net.get("initial_marking") or {}
    final_markings = petri_net.get("final_markings") or []
    final_marking = final_markings[0] if final_markings else {}

    return Net(
        places=places,
        transitions=transitions,
        arcs=arcs,
        initial_marking=initial_marking,
        final_marking=final_marking,
    )

def preprocessing(ocel:OCEL, object_type:str, petri_net: PetriNet | None) -> Tuple[str, R4PMPetriNet]: 
    event_log_df = ocel.sql(f"""
        SELECT
            rel."ocel:oid" as "case:concept:name",
            ev."ocel:timestamp" as "time:timestamp",
            ev."ocel:activity" as "concept:name"
        FROM
            e2o rel
            RIGHT JOIN (
                SELECT
                    *
                FROM
                    objects
                WHERE
                    "ocel:type" = '{object_type}'
                ) ob USING ("ocel:oid")
            LEFT JOIN (
            SELECT
            *
            FROM
            events
            ) ev USING ("ocel:eid")
            ORDER BY
            ("time:timestamp", "case:concept:name", "concept:name")
                """).pl()
    log_id = r4pm.import_item_from_df('EventLog', event_log_df)
    proj_id = r4pm.bindings.log_to_activity_projection(log_id)
    if petri_net:
        process_model = to_r4pm_format(flatten(petri_net,object_type))
    else:
        process_model = r4pm.bindings.discover_alphaplusplusplus(proj_id)
    return proj_id,process_model

    

def variant_alignment(proj_id: str, process_model: R4PMPetriNet, options: Optional["AlignmentOptions"] = None) -> List[VariantAlignmentResult]:
    raw_result = r4pm.bindings.align_variants(process_model, proj_id, options)
    return [VariantAlignmentResult(**r) for r in raw_result]

def compute_fitness(alignments:List[VariantAlignmentResult], process_model:R4PMPetriNet) -> FitnessResult:
    fitness = r4pm.bindings.compute_fitness([a.model_dump() for a in alignments],process_model)
    return FitnessResult(**fitness)


def compute_aggregated(variant_alignments: List[VariantAlignmentResult],) -> Aggregated:
    total_traces = sum(v.frequency for v in variant_alignments)
    transition_stats: Dict[str, Dict[str, int]] = {}
    log_move_counts: Dict[str, int] = {}

    for v in variant_alignments:
        result = v.result
        if "Ok" not in result:
            continue
        freq = v.frequency
        for move in result["Ok"]["moves"]:
            if "SyncMove" in move:
                t = move["SyncMove"]["transition"]
                stats = transition_stats.setdefault(t, {"sync_fires": 0, "model_fires": 0})
                stats["sync_fires"] += freq
            elif "ModelMove" in move:
                t = move["ModelMove"]["transition"]
                stats = transition_stats.setdefault(t, {"sync_fires": 0, "model_fires": 0})
                stats["model_fires"] += freq
            elif "LogMove" in move:
                idx = move["LogMove"]["trace_event_index"]
                activity = v.activities[idx]
                log_move_counts[activity] = log_move_counts.get(activity, 0) + freq

    return Aggregated(
        total_traces=total_traces,
        transition_stats={k: TransitionStat(**v) for k, v in transition_stats.items()},
        log_move_counts=log_move_counts,
    )


def compute_alignments(ocel:OCEL, object_type:str, petri_net: PetriNet | None):
    (proj_id, process_model) = preprocessing(ocel,object_type, petri_net)
    options = {"cost_fn": {"log_move_cost": 1, "model_move_cost": 1, "silent_move_cost": 0, "sync_move_cost": 0}}
    alignments = variant_alignment(proj_id,process_model,options)
    fitness = compute_fitness(alignments,process_model)
    aggregated = compute_aggregated(alignments)
    return AlignmentsResponse(net=convert_net(process_model), variant_alignments=alignments, fitness=fitness,aggregated=aggregated)