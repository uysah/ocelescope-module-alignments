from ocelescope import PetriNet
from ocelescope_module_example.models.alignment import VariantAlignmentResult, AlignmentOptions,FitnessResult, Aggregated, TransitionStat, AlignmentsResponse, Net, NetArc, NetPlace, NetTransition
from typing import Optional,Tuple, List, Dict
import r4pm
import pm4py
import polars
from ocelescope_backend.app.dependencies import  ApiOcel
import re

def eid_seq(eid: str) -> int:
        m = re.search(r'(\d+)$', eid)
        return int(m.group(1)) if m else -1

def preprocessing(ocel:ApiOcel, object_type) -> Tuple[str, PetriNet]: 
    e2o_df = ocel.e2o.df.reset_index(drop=True)
    case_relations = e2o_df[e2o_df["ocel:type"] == object_type]
    case_relations = case_relations.copy()

    case_relations["eid_seq"] = case_relations["ocel:eid"].apply(eid_seq)

    event_log_df = case_relations.rename(columns={
        "ocel:oid": "case:concept:name",
        "ocel:activity": "concept:name",
        "ocel:timestamp": "time:timestamp",
    })[["case:concept:name", "concept:name", "time:timestamp", "eid_seq"]]

    event_log_df = event_log_df.sort_values(
        ["case:concept:name", "time:timestamp", "eid_seq"], kind="stable"
    ).drop(columns="eid_seq")
    pl_df = polars.from_pandas(event_log_df)
    log_id = r4pm.import_item_from_df('EventLog', pl_df)
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

def compute_alignments(ocel:ApiOcel, object_type:str):
    (proj_id, process_model) = preprocessing(ocel,object_type)
    options = {"cost_fn": {"log_move_cost": 1, "model_move_cost": 1, "silent_move_cost": 0, "sync_move_cost": 0}}
    alignments = variant_alignment(proj_id,process_model,options)
    fitness = compute_fitness(alignments,process_model)
    aggregated = compute_aggregated(alignments)
    return AlignmentsResponse(net=convert_net(process_model), variant_alignments=alignments, fitness=fitness,aggregated=aggregated)