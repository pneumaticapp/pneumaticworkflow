import type { McpServer } from '@modelcontextprotocol/server';
import * as z from 'zod/v4';

interface PromptDef {
  name: string;
  title: string;
  description: string;
  args: Record<string, { description: string; optional?: boolean }>;
  tools: readonly string[];
  text: (args: Record<string, string | undefined>) => string;
}

export const prompts: readonly PromptDef[] = [
  {
    name: 'triage_inbox',
    title: 'Triage my Pneumatic inbox',
    description: 'Summarise active tasks and new notifications and suggest what to do first.',
    args: {},
    tools: ['list_tasks', 'list_notifications'],
    text: () =>
      'Review my Pneumatic work. Call list_tasks (ordering "overdue") and list_notifications (status "new"). ' +
      'Group the tasks into overdue, due soon and the rest, mention urgent ones, and summarise new comments ' +
      "and mentions. Include each task's webUrl. Suggest the next three actions, but do not complete, comment " +
      'or change anything until I confirm.',
  },
  {
    name: 'weekly_report',
    title: 'Process status report',
    description: 'Report started, completed and overdue work for a period, by template.',
    args: { days: { description: 'Number of past days to cover (default 7)', optional: true } },
    tools: ['get_dashboard', 'list_highlights', 'list_tasks'],
    text: ({ days }) =>
      `Prepare a status report for the last ${days || '7'} days. Use get_dashboard for scope "workflows" and ` +
      '"tasks" with breakdown "template" for that period, list_highlights for notable events, and list_tasks ' +
      'ordered by "overdue" for what is late. Present totals, the templates with the most overdue work and ' +
      'notable completions or returns, with webUrl links. Do not change anything.',
  },
  {
    name: 'start_process',
    title: 'Start a process',
    description: 'Find the right template, collect the kickoff values and start a workflow.',
    args: { request: { description: 'What should be started, e.g. "onboarding for Ada from Monday"' } },
    tools: ['list_templates', 'get_template_kickoff', 'run_workflow'],
    text: ({ request }) =>
      `Help me start a Pneumatic workflow for: ${request ?? ''}. Find active templates with list_templates, ` +
      'pick the best match (ask me if several fit), read its form with get_template_kickoff and fill the ' +
      'fields from my request. Ask me for missing required values, show me the final values and the workflow ' +
      "name, and call run_workflow only after I confirm. Reply with the new workflow's webUrl.",
  },
  {
    name: 'find_bottlenecks',
    title: 'Find process bottlenecks',
    description: 'Show where workflows of a template get stuck.',
    args: { template: { description: 'Template name or ID' } },
    tools: ['list_templates', 'get_template_step_stats', 'count_workflows'],
    text: ({ template }) =>
      `Find where workflows of the template "${template ?? ''}" get stuck. Resolve it with list_templates, ` +
      'then use get_template_step_stats (currentOnly true for now, and the last 30 days) and count_workflows ' +
      'with groupBy "step" and "performer". Name the steps with the most in-progress and overdue tasks and the ' +
      'people or groups holding them, and suggest improvements. Do not change anything.',
  },
  {
    name: 'offboard_user',
    title: "Hand over a user's work",
    description: 'Move templates, tasks and workflows of a leaving or absent user to someone else.',
    args: {
      user: { description: 'Name or email of the user' },
      successor: { description: 'Who takes over', optional: true },
    },
    tools: ['list_users', 'get_assignment_count', 'set_vacation', 'reassign_user', 'deactivate_user'],
    text: ({ user, successor }) =>
      `Help me hand over the work of ${user ?? ''}${successor ? ` to ${successor}` : ''}. Find the people with ` +
      'list_users, show get_assignment_count for the user and ask whether this is a temporary absence ' +
      '(set_vacation with substitutes) or a permanent handover (reassign_user, then optionally ' +
      'deactivate_user). Explain the effect and wait for my confirmation before each change.',
  },
  {
    name: 'design_process',
    title: 'Design a process template',
    description: 'Turn a process description into a template with steps, performers and fields.',
    args: { description: { description: 'What the process is about and who is involved' } },
    tools: ['list_library_templates', 'generate_template_steps', 'list_users', 'list_groups', 'create_template'],
    text: ({ description }) =>
      `Design a Pneumatic template for this process: ${description ?? ''}. Check list_library_templates for a ` +
      'close match and generate_template_steps for ideas, then propose steps with performers (resolve people ' +
      'with list_users / list_groups), output fields, checklists and due dates, plus kickoff fields. Show the ' +
      "proposal and call create_template only after I confirm. Reply with the template's webUrl.",
  },
];

export function registerPrompts(server: McpServer, offered: ReadonlySet<string>) {
  for (const { name, title, description, args, tools, text } of prompts) {
    if (!tools.every((tool) => offered.has(tool))) {
      continue;
    }
    const shape = Object.fromEntries(
      Object.entries(args).map(([key, { description: hint, optional }]) => [
        key,
        optional ? z.string().optional().describe(hint) : z.string().describe(hint),
      ]),
    );
    server.registerPrompt(
      name,
      { title, description, argsSchema: z.object(shape) },
      (values: Record<string, unknown>) => ({
        messages: [
          {
            role: 'user' as const,
            content: { type: 'text' as const, text: text(values as Record<string, string | undefined>) },
          },
        ],
      }),
    );
  }
}
