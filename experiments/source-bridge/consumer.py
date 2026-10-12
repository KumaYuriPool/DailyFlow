"""Independent, in-memory contract consumer; NOT imported by DailyFlow.

Consumes protocol-v2 records from explicitly bound sources. Transport, consent,
durable storage and production UI are deliberately outside this experiment.
Deletion is explicit only: neither an empty page nor a complete snapshot deletes.
"""
from copy import deepcopy
from datetime import date, datetime
from math import isfinite


class ContractError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ContractError(message)


def integer(value):
    return type(value) is int


def timestamp(value):
    return type(value) in (int, float) and isfinite(value) and value >= 0


def civil(value):
    require(isinstance(value, str), "date must be text")
    try:
        require(date.fromisoformat(value).isoformat() == value, "non-canonical date")
    except ValueError as exc:
        raise ContractError("invalid civil date") from exc


def validate(event, bound_source, registered_modules):
    require(isinstance(event, dict), "event must be an object")
    require(event.get("protocol_version") == 2, "only protocol v2 is supported")
    require(event.get("source_app") == bound_source, "source does not match trusted binding")
    module, record = event.get("source_module"), event.get("source_record_id")
    require(isinstance(module, str) and module in registered_modules, "unregistered module")
    require(isinstance(record, str) and bool(record), "record ID is required")
    revision = event.get("source_revision")
    require(integer(revision) and revision > 0, "revision must be a positive integer")
    identity = f"{bound_source}/{module}/{record}"
    require(event.get("event_id") == identity, "event ID must preserve source identity")
    require(event.get("change_id") == f"{identity}/{revision}", "change ID mismatch")
    operation = event.get("operation")
    require(operation in ("upsert", "delete"), "unknown operation")
    if operation == "delete":
        require(timestamp(event.get("deleted_at")), "invalid deleted_at")
        return (bound_source, module, record)
    civil(event.get("date"))
    end = event.get("end_date")
    require(isinstance(end, str), "end_date must be text")
    if end:
        civil(end)
        require(end >= event["date"], "reversed date interval")
    require(type(event.get("open_end")) is bool, "open_end must be boolean")
    require(not (event["open_end"] and end), "open interval cannot have an end")
    require(event.get("timezone") == "Asia/Shanghai", "unsupported timezone")
    status = event.get("status")
    require(status in ("occurred", "planned", "cancelled"), "unknown event status")
    precision = event.get("time_precision")
    require(precision in ("day", "minute"), "unsupported precision")
    for field in ("created_at", "recorded_at", "updated_at"):
        require(timestamp(event.get(field)), f"invalid {field}")
    require(event["recorded_at"] == event["created_at"], "recorded_at differs from creation")
    require(event["updated_at"] >= event["created_at"], "update precedes creation")
    if precision == "day":
        require(all(event.get(k) == "" for k in ("time", "occurred_at", "scheduled_at")), "invented day timestamp")
    else:
        time = event.get("time")
        require(isinstance(time, str) and len(time) == 5, "invalid minute time")
        try:
            require(datetime.strptime(time, "%H:%M").strftime("%H:%M") == time, "invalid minute time")
        except ValueError as exc:
            raise ContractError("invalid minute time") from exc
        stamp = event["date"] + "T" + time + ":00+08:00"
        expected = (stamp, "") if status == "occurred" else ("", stamp) if status == "planned" else ("", "")
        require((event.get("occurred_at"), event.get("scheduled_at")) == expected, "timestamp/status mismatch")
    require(isinstance(event.get("summary"), str), "summary must be text")
    require(isinstance(event.get("flow_ids"), list), "flow_ids must be an array")
    entry = event.get("entry")
    require(isinstance(entry, dict) and entry.get("record_id") == record and entry.get("source_revision") == revision, "source entry mismatch")
    require(integer(event.get("amount_minor")), "amount must use integer minor units")
    require(isinstance(event.get("currency"), str), "currency must be text")
    return (bound_source, module, record)


class Projection:
    def __init__(self, bindings):
        # Bindings come from the caller's trusted setup, never from a page/model.
        self.bindings = {source: frozenset(modules) for source, modules in bindings.items()}
        self.items, self.status, self.snapshots = {}, {}, {}

    def apply_page(self, bound_source, page):
        require(bound_source in self.bindings, "source is not bound")
        require(isinstance(page, dict), "page must be an object")
        status = page.get("status")
        require(status in ("ok", "denied", "unavailable"), "unknown source status")
        if status != "ok":
            self.status[bound_source] = status
            self.snapshots.pop(bound_source, None)
            return {"accepted": 0, "ignored": 0, "status": status}
        require(page.get("source_app") == bound_source, "page source mismatch")
        require(isinstance(page.get("events"), list), "events must be an array")
        require(type(page.get("complete")) is bool, "complete must be boolean")
        require(page["complete"] or bool(page["events"]), "incomplete page must advance")
        require(integer(page.get("offset")) and page["offset"] >= 0, "invalid offset")
        require(integer(page.get("snapshot_revision")) and page["snapshot_revision"] > 0, "invalid snapshot revision")
        snapshot = page["snapshot_revision"]
        offset = page["offset"]
        if offset:
            require(self.snapshots.get(bound_source) == (snapshot, offset), "stale or missing pagination boundary")
        candidate = deepcopy(self.items)
        accepted, ignored = 0, 0
        for event in page["events"]:
            key = validate(event, bound_source, self.bindings[bound_source])
            old = candidate.get(key)
            if old and old["source_revision"] > event["source_revision"]:
                ignored += 1
                continue
            if old and old["source_revision"] == event["source_revision"]:
                require(old == event, "same revision carries conflicting content")
                ignored += 1
                continue
            candidate[key] = deepcopy(event)
            accepted += 1
        # Commit only after the entire page validates. No absence-based deletion.
        self.items = candidate
        self.status[bound_source] = "ok" if page["complete"] else "partial"
        if page["complete"]:
            self.snapshots.pop(bound_source, None)
        else:
            self.snapshots[bound_source] = (snapshot, offset + len(page["events"]))
        return {"accepted": accepted, "ignored": ignored, "status": self.status[bound_source]}

    def visible(self):
        # Denial/unavailability retains internal test cache but hides its content.
        # A successful partial page stays labelled partial; never assert complete.
        return [deepcopy(event) for key, event in self.items.items()
                if event["operation"] == "upsert" and self.status.get(key[0]) in ("ok", "partial")]
