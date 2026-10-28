import { IExtraField, ITemplateClient, ITemplateTaskClient } from '../../../../types/template';
import {
  EConditionLogicOperations,
  TConditionRule,
} from '../../TaskForm/Conditions';
import { EStartingType } from '../../TaskForm/Conditions/utils/getDropdownOperators';
import { IGraphConditionClause, TGraphEdge } from '../types';
import { getGraphEdgeVisual } from './edgeStyles';
import { isCheckIfCondition } from './countCheckIfConditions';
import { KICKOFF_NODE_ID, KICKOFF_START_AFTER } from './graphConstants';
import { GRAPH_EDGE_Z_INDEX } from './graphGeometry';

function fieldName(fields: IExtraField[], apiName: string): string | null {
  return fields.find((field) => field.apiName === apiName)?.name ?? null;
}

function buildFieldOwnerMap(template: ITemplateClient, sortedTasks: ITemplateTaskClient[]): Map<string, string> {
  const owners = new Map<string, string>();

  (template.kickoff?.fields ?? []).forEach((field) => {
    owners.set(field.apiName, KICKOFF_NODE_ID);
  });

  sortedTasks.forEach((task) => {
    task.fields.forEach((field) => {
      owners.set(field.apiName, task.apiName);
    });
  });

  return owners;
}

function resolveSource(
  rule: TConditionRule,
  fieldOwners: Map<string, string>,
  taskApiNameSet: Set<string>,
): string | null {
  if (rule.fieldType === EStartingType.Kickoff) {
    return KICKOFF_NODE_ID;
  }

  if (rule.fieldType === EStartingType.Task && rule.field && taskApiNameSet.has(rule.field)) {
    return rule.field;
  }

  if (rule.field && fieldOwners.has(rule.field)) {
    return fieldOwners.get(rule.field) ?? null;
  }

  return null;
}

function resolveFieldLabel(
  rule: TConditionRule,
  template: ITemplateClient,
  sortedTasks: ITemplateTaskClient[],
): string {
  if (rule.fieldType === EStartingType.Kickoff) {
    return KICKOFF_START_AFTER;
  }

  if (rule.fieldType === EStartingType.Task) {
    return sortedTasks.find((task) => task.apiName === rule.field)?.name || rule.field || '';
  }

  if (!rule.field) {
    return '';
  }

  const kickoffName = fieldName(template.kickoff?.fields ?? [], rule.field);
  if (kickoffName) {
    return kickoffName;
  }

  const ownerTask = sortedTasks.find((task) => task.fields.some((field) => field.apiName === rule.field));

  return fieldName(ownerTask?.fields ?? [], rule.field) || rule.field;
}

function formatClauseValue(rule: TConditionRule): string | undefined {
  if (rule.value == null || rule.value === '') {
    return undefined;
  }

  return String(rule.value);
}

function buildClause(
  rule: TConditionRule,
  template: ITemplateClient,
  sortedTasks: ITemplateTaskClient[],
): IGraphConditionClause {
  return {
    fieldLabel: resolveFieldLabel(rule, template, sortedTasks),
    operator: rule.operator,
    value: formatClauseValue(rule),
    logicOperation: rule.logicOperation,
  };
}

function joinSummary(clauses: IGraphConditionClause[]): string {
  return clauses
    .map((clause, index) => {
      const parts = [clause.fieldLabel, clause.operator, clause.value].filter(Boolean);
      const text = parts.join(' ');

      if (index === 0) {
        return text;
      }

      const logic = clause.logicOperation === EConditionLogicOperations.Or ? 'or' : 'and';

      return `${logic} ${text}`;
    })
    .join(' ');
}

function buildCheckIfEdge(
  sourceId: string,
  targetId: string,
  index: number,
  clauses: IGraphConditionClause[],
): TGraphEdge {
  return {
    id: `edge-${sourceId}-${targetId}-checkif-${index}`,
    source: sourceId,
    target: targetId,
    sourceHandle: 'source-bottom',
    targetHandle: 'target-top',
    type: 'smoothstep',
    zIndex: GRAPH_EDGE_Z_INDEX,
    data: {
      isConditional: true,
      clauses,
      summary: joinSummary(clauses),
    },
    labelShowBg: false,
    ...getGraphEdgeVisual(true),
  };
}

export function buildCheckIfEdges(
  template: ITemplateClient,
  sortedTasks: ITemplateTaskClient[],
  taskApiNameSet: Set<string>,
): TGraphEdge[] {
  const fieldOwners = buildFieldOwnerMap(template, sortedTasks);
  const nodeIds = new Set<string>([KICKOFF_NODE_ID, ...taskApiNameSet]);

  return sortedTasks.flatMap((task) => {
    const grouped = new Map<string, IGraphConditionClause[]>();

    task.conditions.forEach((condition) => {
      if (!isCheckIfCondition(condition)) {
        return;
      }

      condition.rules.forEach((rule) => {
        const sourceId = resolveSource(rule, fieldOwners, taskApiNameSet);

        if (!sourceId || sourceId === task.apiName || !nodeIds.has(sourceId)) {
          return;
        }

        const clauses = grouped.get(sourceId) ?? [];
        clauses.push(buildClause(rule, template, sortedTasks));
        grouped.set(sourceId, clauses);
      });
    });

    return [...grouped.entries()].map(([sourceId, clauses], index) => (
      buildCheckIfEdge(sourceId, task.apiName, index, clauses)
    ));
  });
}
