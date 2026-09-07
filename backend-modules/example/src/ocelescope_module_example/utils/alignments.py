from ocelescope import PetriNet
from ocelescope_module_example.models.alignment import VariantAlignmentResult, AlignmentOptions,FitnessResult, Aggregated, TransitionStat, AlignmentsResponse, Net, NetArc, NetPlace, NetTransition
from typing import Optional,Tuple, List, Dict
import r4pm
import pm4py
import polars
from ocelescope import  OCEL

def preprocessing(ocel:OCEL, object_type) -> Tuple[str, PetriNet]: 
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
    process_model = r4pm.bindings.discover_alphaplusplusplus(proj_id)

    return proj_id, process_model

def variant_alignment(proj_id: str, process_model: PetriNet, options: Optional["AlignmentOptions"] = None) -> List[VariantAlignmentResult]:
    raw_result = r4pm.bindings.align_variants(process_model, proj_id, options)
    return [VariantAlignmentResult(**r) for r in raw_result]

def compute_fitness(alignments:List[VariantAlignmentResult], process_model:PetriNet) -> FitnessResult:
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

def convert_net(petri_net) -> Net:
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

def compute_alignments(ocel:OCEL, object_type:str, petri_net: PetriNet | None):
    (proj_id, process_model) = preprocessing(ocel,object_type)
    options = {"cost_fn": {"log_move_cost": 1, "model_move_cost": 1, "silent_move_cost": 0, "sync_move_cost": 0}}
    alignments = variant_alignment(proj_id,process_model,options)
    fitness = compute_fitness(alignments,process_model)
    aggregated = compute_aggregated(alignments)
    return AlignmentsResponse(net=convert_net(process_model), variant_alignments=alignments, fitness=fitness,aggregated=aggregated)