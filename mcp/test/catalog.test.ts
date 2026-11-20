import { describe, expect, it } from 'vitest';

import { buildInstructions } from '../src/mcp/instructions.js';
import { prompts } from '../src/mcp/prompts.js';
import { availableTools, TOOLSETS, type ToolContext, type ToolSelection } from '../src/mcp/toolDef.js';
import { createPneumaticClient } from '../src/pneumatic/client.js';
import { allTools } from '../src/tools/index.js';

const context: ToolContext = {
  client: createPneumaticClient({ apiUrl: 'https://pneumatic.test' }, 'pn-key'),
  fetchRemote: async () => ({ data: Buffer.alloc(0) }),
};

describe('tool catalog', () => {
  it('has unique snake_case names and complete metadata', () => {
    const names = allTools.map(({ name }) => name);
    expect(new Set(names).size).toBe(names.length);
    for (const { name, title, description, annotations } of allTools) {
      expect(name, name).toMatch(/^[a-z]+(?:_[a-z]+)*$/);
      expect(title, name).toBeTruthy();
      expect(description.length, name).toBeGreaterThan(20);
      expect(annotations.readOnlyHint, name).toBeTypeOf('boolean');
    }
  });

  it('paginates every list tool the same way', () => {
    for (const { name, inputSchema } of allTools.filter(({ name }) => name.startsWith('list_'))) {
      expect(Object.keys(inputSchema.shape), name).toEqual(expect.arrayContaining(['limit', 'offset']));
    }
  });

  it('registers capability-bound tools only when the transport provides them', () => {
    const withoutUploads = availableTools(allTools, context).map(({ name }) => name);
    expect(withoutUploads).not.toContain('create_upload_link');
    const withUploads = availableTools(allTools, {
      ...context,
      uploads: { create: async () => ({ uploadId: '', uploadUrl: '', expiresAt: 0 }), get: async () => undefined },
    });
    expect(withUploads.map(({ name }) => name)).toEqual(
      expect.arrayContaining(['create_upload_link', 'get_upload_status']),
    );
  });

  it('keeps the reviewed set of destructive tools in the confirmation rule', () => {
    const instructions = buildInstructions(allTools);
    const destructive = allTools.filter(({ annotations }) => annotations.destructiveHint).map(({ name }) => name);
    expect(destructive.sort()).toEqual([
      'deactivate_user',
      'delete_comment',
      'delete_dataset',
      'delete_group',
      'delete_template',
      'finish_workflow',
      'reassign_user',
      'remove_task_performer',
      'remove_template_fields',
      'remove_template_step',
      'return_workflow_to_task',
      'revert_task',
      'terminate_workflow',
      'update_dataset',
      'update_group',
    ]);
    for (const name of destructive) {
      expect(instructions, name).toContain(name);
    }
  });
});

describe('toolsets and read-only mode', () => {
  it('puts every tool into a known toolset', () => {
    for (const { name, toolset } of allTools) {
      expect(['core', 'files', 'design', 'analytics', 'admin'], name).toContain(toolset);
    }
    const core = availableTools(allTools, context, { toolsets: ['core'] }).map(({ name }) => name);
    expect(core).toEqual(expect.arrayContaining(['list_tasks', 'complete_task', 'set_vacation', 'list_datasets']));
    expect(core).not.toContain('create_template');
    expect(core).not.toContain('reassign_user');
  });

  it('offers only read-only tools in read-only mode and tells the model so', () => {
    const tools = availableTools(allTools, context, { isReadOnly: true });
    expect(tools.every(({ annotations }) => annotations.readOnlyHint === true)).toBe(true);
    expect(tools.map(({ name }) => name)).toEqual(
      expect.arrayContaining(['get_task', 'list_workflows', 'download_file']),
    );
    const instructions = buildInstructions(tools);
    expect(instructions).toContain('This connector is read-only');
    expect(instructions).not.toMatch(/complete_task|create_template|upload_file|confirm with the user/);
  });

  it('describes only the areas whose tools are offered', () => {
    const instructions = buildInstructions(availableTools(allTools, context, { toolsets: ['core'] }));
    expect(instructions).not.toContain('Designing processes');
    expect(instructions).not.toContain('reassign_user');
    expect(instructions).toContain('complete_task');
  });

  const mentioned = (text: string) =>
    allTools.map(({ name }) => name).filter((name) => new RegExp(`\\b${name}\\b`).test(text));
  const selections: ToolSelection[] = [
    {},
    { isReadOnly: true },
    ...TOOLSETS.map((toolset) => ({ toolsets: [toolset] })),
    ...TOOLSETS.map((toolset) => ({ toolsets: [toolset], isReadOnly: true })),
  ];

  it.each(selections)('never mentions a tool that is not offered (%o)', (selection) => {
    const tools = availableTools(allTools, { ...context, uploads: {} as never }, selection);
    const offered = new Set(tools.map(({ name }) => name));
    expect(mentioned(buildInstructions(tools)).filter((name) => !offered.has(name))).toEqual([]);
  });

  it('declares every tool a prompt relies on', () => {
    for (const { name, tools, text } of prompts) {
      expect(tools, name).toEqual(expect.arrayContaining(mentioned(text({}))));
    }
  });

  it('offers the upload status check only together with upload links', () => {
    const withUploads = { ...context, uploads: {} as never };
    const names = (selection: ToolSelection) =>
      availableTools(allTools, withUploads, selection).map(({ name }) => name);
    expect(names({})).toContain('get_upload_status');
    expect(names({ isReadOnly: true })).not.toContain('get_upload_status');
  });
});
