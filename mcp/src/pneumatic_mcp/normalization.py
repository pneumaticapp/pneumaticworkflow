"""Convert core responses and bound their structural and text size."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import JsonValue

from pneumatic_mcp.errors import CoreError
from pneumatic_mcp.outputs import (
    MAX_NESTED_ITEMS,
    MAX_RESULT_BYTES,
    Output,
    Upload,
)


@dataclass
class Compact:
    text_budget: int = 20 * 1024
    truncated: bool = False

    def value(self, value: JsonValue, *, depth: int = 0) -> JsonValue:
        if isinstance(value, str):
            encoded = value.encode("utf-8")
            maximum = min(2048, self.text_budget)
            self.text_budget -= min(len(encoded), maximum)
            if len(encoded) > maximum:
                self.truncated = True
                return encoded[:maximum].decode("utf-8", errors="ignore")
            return value
        if isinstance(value, list):
            if len(value) > 20 or (value and depth >= 4):
                self.truncated = True
            return (
                [
                    self.value(value=item, depth=depth + 1)
                    for item in value[:20]
                ]
                if depth < 4
                else []
            )
        if isinstance(value, dict):
            if len(value) > 20 or depth >= 4:
                self.truncated = True
            return (
                {
                    key: self.value(value=item, depth=depth + 1)
                    for key, item in list(value.items())[:20]
                }
                if depth < 4
                else {}
            )
        return value

    def pick(self, record: dict, keys: tuple[str, ...]) -> dict:
        if not isinstance(record, dict):
            raise CoreError(code="invalid_response")
        identifiers = {
            "id",
            "api_name",
            "file_id",
            "field_api_name",
            "upload_url",
            "expires_at",
        }
        data = {}
        for key in keys:
            if key not in record:
                continue
            value = record[key]
            if key in identifiers:
                if isinstance(value, str) and len(value) > 2048:
                    raise CoreError(code="invalid_response")
                data[key] = value
            else:
                data[key] = self.value(value=value)
        return data

    def objects(
        self,
        values: list[Any],
        converter: Callable[..., dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not isinstance(values, list):
            raise CoreError(code="invalid_response")
        if len(values) > MAX_NESTED_ITEMS:
            self.truncated = True
        return [converter(item) for item in values[:MAX_NESTED_ITEMS]]

    def fields(self, values: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def field(record: dict[str, Any]) -> dict[str, Any]:
            data = self.pick(
                record=record,
                keys=(
                    "api_name",
                    "name",
                    "type",
                    "is_required",
                    "is_hidden",
                    "description",
                    "default",
                    "value",
                ),
            )
            data["selections"] = self.objects(
                values=record.get("selections", []),
                converter=lambda item: (
                    self.pick(record=item, keys=("id", "api_name", "value"))
                    if isinstance(item, dict)
                    else {"value": self.value(value=item)}
                ),
            )
            return data

        return self.objects(values=values, converter=field)

    def fieldsets(self, values: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def fieldset(record: dict[str, Any]) -> dict[str, Any]:
            data = self.pick(record=record, keys=("api_name", "name"))
            data["fields"] = self.fields(values=record.get("fields", []))
            return data

        return self.objects(values=values, converter=fieldset)

    def task(
        self, record: dict[str, Any], *, detail: bool = False
    ) -> dict[str, Any]:
        data = self.pick(
            record=record,
            keys=("id", "name", "status", "is_completed", "due_date_tsp"),
        )
        workflow = record.get("workflow")
        data["workflow_id"] = (
            workflow.get("id")
            if isinstance(workflow, dict)
            else record.get("workflow_id")
        )
        if detail:
            data["description"] = self.value(value=record.get("description"))
            data["output"] = self.fields(values=record.get("output", []))
            data["fieldsets"] = self.fieldsets(
                values=record.get("fieldsets", [])
            )
        return data

    def workflow(
        self, record: dict[str, Any], *, detail: bool = False
    ) -> dict[str, Any]:
        data = self.pick(
            record=record,
            keys=("id", "name", "status", "is_urgent", "due_date_tsp"),
        )
        template = record.get("template")
        data["template_id"] = (
            template.get("id")
            if isinstance(template, dict)
            else record.get("template_id")
        )
        if detail:
            data["description"] = self.value(value=record.get("description"))
            data["tasks"] = self.objects(
                values=record.get("tasks", []), converter=self.task
            )
            kickoff = record.get("kickoff") or {}
            data["kickoff"] = self.fields(
                values=kickoff.get("output", kickoff.get("fields", []))
            )
            data["kickoff_fieldsets"] = self.fieldsets(
                values=kickoff.get("fieldsets", [])
            )
        return data

    def event(self, record: dict[str, Any]) -> dict[str, Any]:
        data = self.pick(
            record=record,
            keys=("id", "type", "text", "created_tsp", "workflow_id"),
        )
        task = record.get("task")
        data["task_id"] = (
            task.get("id") if isinstance(task, dict) else record.get("task_id")
        )
        return data


def normalize(
    name: str,
    raw: dict[str, Any] | list[Any],
    args: dict[str, Any],
    output: type[Output],
) -> dict[str, Any]:
    compact = Compact()
    data = _convert(name=name, raw=raw, args=args, compact=compact)
    result = output.model_validate(
        {"data": data, "truncated": compact.truncated}
    )
    return _bound_result(wire=result.model_dump(exclude_none=True), args=args)


def _convert(
    name: str,
    raw: dict[str, Any] | list[Any],
    args: dict[str, Any],
    compact: Compact,
) -> dict[str, Any]:
    list_converters = {
        "list_templates": lambda item: compact.pick(
            record=item, keys=("id", "name", "description", "is_active")
        ),
        "list_workflows": compact.workflow,
        "list_my_tasks": compact.task,
        "get_workflow_events": compact.event,
        "list_attachments": lambda item: compact.pick(
            record=item, keys=("id", "file_id", "access_type", "source_type")
        ),
    }
    if name in list_converters:
        items = (
            raw
            if isinstance(raw, list)
            else raw.get("results", raw.get("items"))
        )
        if not isinstance(items, list):
            raise CoreError(code="invalid_response")
        limit, offset = args.get("limit", 20), args.get("offset", 0)
        if len(items) > limit:
            compact.truncated = True
        items = compact.objects(
            values=items[:limit], converter=list_converters[name]
        )
        total = raw.get("count") if isinstance(raw, dict) else None
        data = {
            "items": items,
            "page": {
                "limit": limit,
                "offset": offset,
                "returned": len(items),
                "total": total,
                "next_offset": offset + len(items)
                if len(items) == limit
                else None,
            },
        }
    elif name == "get_template":
        kickoff = raw.get("kickoff") or {}
        data = compact.pick(
            record=raw,
            keys=("id", "name", "description", "is_active"),
        )
        data["tasks"] = compact.objects(
            values=raw.get("tasks", []),
            converter=lambda item: compact.pick(
                record=item,
                keys=("api_name", "name", "number"),
            ),
        )
        data["kickoff"] = compact.fields(
            values=kickoff.get("fields", kickoff.get("output", [])),
        )
        data["kickoff_fieldsets"] = compact.fieldsets(
            values=kickoff.get("fieldsets", []),
        )
    elif name == "get_template_kickoff":
        kickoff = raw.get("kickoff", raw)
        data = {
            "template_id": raw.get(
                "template_id", raw.get("id", args["template_id"])
            ),
            "name": compact.value(value=raw.get("name")),
            "fields": compact.fields(values=kickoff.get("fields", [])),
            "fieldsets": compact.fieldsets(
                values=kickoff.get("fieldsets", [])
            ),
        }
    elif name in {"get_workflow", "run_workflow"}:
        data = compact.workflow(record=raw, detail=True)
    elif name in {"get_task", "complete_task"}:
        data = compact.task(record=raw, detail=True)
    elif name in {"add_workflow_comment", "comment_task"}:
        data = compact.event(record=raw)
    elif name == "get_attachment":
        data = {
            "attachment": compact.pick(
                record=raw["attachment"],
                keys=("id", "file_id", "access_type", "source_type"),
            ),
            "file": compact.pick(
                record=raw["file"],
                keys=("file_id", "name", "size", "content_type"),
            ),
            # URLs/ticket expiry are capability data: preserve them exactly.
            "download": {
                key: raw["download"][key]
                for key in ("download_url", "expires_at", "expires_in")
            },
        }
    else:
        data = compact.pick(record=raw, keys=tuple(Upload.model_fields))
    return data


def _find_lists(value: JsonValue, lists: list[list[JsonValue]]) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _find_lists(value=child, lists=lists)
    elif isinstance(value, list) and value:
        lists.append(value)
        for child in value:
            _find_lists(value=child, lists=lists)


def _bound_result(
    wire: dict[str, Any], args: dict[str, Any]
) -> dict[str, Any]:
    # Total bound includes nested structural overhead, not only strings.
    while (
        len(json.dumps(wire, ensure_ascii=False).encode()) > MAX_RESULT_BYTES
    ):
        lists = []

        _find_lists(value=wire, lists=lists)
        if not lists:
            raise CoreError(code="invalid_response")
        largest = max(lists, key=lambda value: len(json.dumps(value).encode()))
        del largest[len(largest) // 2 :]
        wire["truncated"] = True
        if "page" in wire["data"]:
            wire["data"]["page"]["returned"] = len(wire["data"]["items"])
            wire["data"]["page"]["next_offset"] = args.get("offset", 0) + len(
                wire["data"]["items"]
            )
    return wire
