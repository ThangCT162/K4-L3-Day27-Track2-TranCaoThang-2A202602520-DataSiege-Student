"""
Your defense. Implement register(ctx) and a handler per event type.
See ../README.md for the full interface + toolkit reference, and
../RULES.md before you start.
"""
from api import Verdict


def register(ctx):
    ctx.on("data_batch", check_data_batch)
    ctx.on("contract_checkpoint", check_contract_checkpoint)
    ctx.on("lineage_run", check_lineage_run)
    ctx.on("feature_materialization", check_feature_materialization)
    ctx.on("embedding_batch", check_embedding_batch)


def check_data_batch(payload, ctx):
    p = ctx.tools.batch_profile(payload["batch_id"])
    if "error" in p:
        return Verdict(alert=False, pillar="checks", reason="profile unavailable")
    b = ctx.baseline
    reasons = []
    if p.get("row_count", 0) < b["row_count_min"] * 1.10 or p.get("row_count", 0) > b["row_count_max"] * 0.90:
        reasons.append("row_count")
    if p.get("null_rate", {}).get("customer_id", 0) > b["null_rate_max"] * 0.90:
        reasons.append("null_rate")
    if p.get("mean_amount", 0) < b["mean_amount_min"] * 1.02 or p.get("mean_amount", 0) > b["mean_amount_max"] * 0.98:
        reasons.append("mean_amount")
    if p.get("staleness_min", 0) > b["staleness_min_max"] * 0.90:
        reasons.append("staleness")
    return Verdict(alert=bool(reasons), pillar="checks", reason=",".join(reasons))


def check_contract_checkpoint(payload, ctx):
    d = ctx.tools.contract_diff(payload["contract_id"], payload["checkpoint_batch_id"])
    if "error" in d:
        return Verdict(alert=False, pillar="contracts", reason="contract unavailable")
    reasons = list(d.get("violations") or [])
    if d.get("freshness_delay_min", 0) > ctx.baseline["freshness_delay_max_min"] * 0.90:
        reasons.append("freshness")
    return Verdict(alert=bool(reasons), pillar="contracts", reason=",".join(reasons))


def check_lineage_run(payload, ctx):
    d = ctx.tools.lineage_graph_slice(payload["run_id"])
    if "error" in d:
        return Verdict(alert=False, pillar="lineage", reason="lineage unavailable")
    reasons = []
    if d.get("duration_ms", 0) > ctx.baseline["lineage_duration_ms_max"] * 0.90:
        reasons.append("runtime")
    if not d.get("actual_upstream") or len(d.get("actual_upstream", [])) < 2:
        reasons.append("missing_upstream")
    if d.get("actual_downstream_count", 0) <= 0:
        reasons.append("orphan_output")
    return Verdict(alert=bool(reasons), pillar="lineage", reason=",".join(reasons))


def check_feature_materialization(payload, ctx):
    d = ctx.tools.feature_drift(payload["feature_view"], payload["batch_id"])
    if "error" in d:
        return Verdict(alert=False, pillar="ai_infra", reason="feature drift unavailable")
    limit = ctx.baseline["feature_mean_shift_sigma_max"] * 0.90
    return Verdict(alert=d.get("mean_shift_sigma", 0) > limit,
                   pillar="ai_infra", reason="mean_shift_sigma")


def check_embedding_batch(payload, ctx):
    d = ctx.tools.embedding_drift(payload["corpus"], payload["chunk_batch_id"])
    if "error" in d:
        return Verdict(alert=False, pillar="ai_infra", reason="embedding drift unavailable")
    b = ctx.baseline
    reasons = []
    if d.get("centroid_shift", 0) > b["embedding_centroid_shift_max"] * 0.90:
        reasons.append("centroid_shift")
    if d.get("avg_doc_age_days", 0) > b["corpus_avg_doc_age_days_max"] * 0.95:
        reasons.append("corpus_staleness")
    return Verdict(alert=bool(reasons), pillar="ai_infra", reason=",".join(reasons))
