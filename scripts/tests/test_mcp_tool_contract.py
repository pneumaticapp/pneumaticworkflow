"""Check the public MCP catalogue against the independent core allowlist."""

from string import Formatter

import pytest
from django.urls import resolve
from pneumatic_mcp.tool_catalog import TOOL_SPECS, ToolSpec
from src.mcp.enums import McpTool
from src.mcp.operations import OPERATIONS, get_operation


def test_public_catalogue__core_operations__complete():
    # arrange
    public_names = {spec.name for spec in TOOL_SPECS}
    internal_names = set(McpTool.FILE_SERVICE_TOOLS)

    # act
    core_names = set(OPERATIONS) - internal_names

    # assert
    assert len(public_names) == len(TOOL_SPECS)
    assert public_names == core_names


@pytest.mark.parametrize("spec", TOOL_SPECS, ids=lambda spec: spec.name)
def test_tool_contract__core_route_and_scopes__match(spec: ToolSpec):
    # arrange
    path_fields = {
        name for _, name, _, _ in Formatter().parse(spec.path) if name
    }
    path_args = {
        name: "00000000-0000-0000-0000-000000000001"
        if name == "upload_id"
        else 1
        for name in path_fields
    }
    path = spec.path.format(**path_args)

    # act
    operation = get_operation(tool=spec.name, method=spec.method, path=path)
    match = resolve(path)
    schema = spec.schema()
    wire_schema = schema.model_dump(by_alias=True, exclude_none=True)

    # assert
    assert operation is not None
    assert set(spec.scopes) == operation.required_scopes
    assert spec.file_links == (spec.name in McpTool.FILE_LINK_WRITES)
    assert spec.write == (operation.method == "POST")
    assert "idempotency_key" not in schema.input_schema["properties"]
    assert path_fields <= spec.model.model_fields.keys()
    if spec.field_values is not None:
        assert spec.field_values in spec.model.model_fields
    assert wire_schema["outputSchema"] == spec.output.model_json_schema()
    assert wire_schema["inputSchema"] == spec.model.model_json_schema()
    assert schema.security_schemes == [
        {"type": "oauth2", "scopes": list(spec.scopes)},
    ]
    callback = match.func
    if hasattr(callback, "actions"):
        assert spec.method.lower() in callback.actions
    else:
        assert hasattr(callback.cls, spec.method.lower())
