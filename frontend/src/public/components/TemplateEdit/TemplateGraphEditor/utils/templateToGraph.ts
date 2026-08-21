import { ITemplateClient, ITemplateTaskClient } from '../../../../types/template';
import {
  ICondition,
  EConditionAction,
  EConditionOperators,
  TConditionRule,
} from '../../TaskForm/Conditions';
import { EGraphNodeType, IGraphState, TGraphNode, TGraphEdge } from '../types';
import { applyConnectedHandles } from './applyConnectedHandles';
import { GRAPH_NODE_HEIGHT, GRAPH_NODE_WIDTH } from './applyDagreLayout';
import { EDGE_STYLE_DEFAULT, EDGE_STYLE_SKIP, GRAPH_EDGE_CLASS_SKIP } from './edgeStyles';
import { insertJunctionNodes } from './insertJunctionNodes';

export const KICKOFF_NODE_ID = 'kickoff';

function buildEdgeId(source: string, target: string, suffix: string): string {
  return `edge-${source}-${target}-${suffix}`;
}

function buildFieldMap(template: ITemplateClient): Map<string, string> {
  const map = new Map<string, string>();
  template.kickoff?.fields?.forEach((f) => map.set(f.apiName, f.name));
  template.tasks?.forEach((task) => task.fields?.forEach((f) => map.set(f.apiName, f.name)));

  return map;
}

function getOperatorLabel(operator: EConditionOperators | null): string {
  if (!operator) return '';
  const labels: Record<EConditionOperators, string> = {
    [EConditionOperators.Equal]: '=',
    [EConditionOperators.NotEqual]: '≠',
    [EConditionOperators.Exist]: 'filled',
    [EConditionOperators.NotExist]: 'empty',
    [EConditionOperators.Contain]: 'contains',
    [EConditionOperators.NotContain]: "doesn't contain",
    [EConditionOperators.MoreThan]: '>',
    [EConditionOperators.LessThan]: '<',
    [EConditionOperators.Completed]: 'completed',
    [EConditionOperators.Skipped]: 'skipped',
    [EConditionOperators.CompletedOrSkipped]: 'done/skipped',
  };

  return labels[operator] ?? operator;
}

function getRuleLabel(rule: TConditionRule, fieldMap: Map<string, string>): string {
  const fieldName = rule.field ? (fieldMap.get(rule.field) ?? rule.field) : '';
  const operatorLabel = getOperatorLabel(rule.operator);
  const ruleWithValue = rule as { value?: string | number | null };
  const value = ruleWithValue.value != null ? String(ruleWithValue.value) : '';
  const parts = [fieldName, operatorLabel, value].filter(Boolean);

  return parts.join(' ');
}

function getConditionSummary(condition: ICondition, fieldMap: Map<string, string>): string {
  if (condition.rules.length === 0) return 'condition';
  const firstLabel = getRuleLabel(condition.rules[0], fieldMap);
  const suffix = condition.rules.length > 1 ? ` +${condition.rules.length - 1}` : '';

  return (firstLabel || 'condition') + suffix;
}

function buildEdgesForTask(
  task: ITemplateTaskClient,
  taskIndex: number,
  sortedTasks: ITemplateTaskClient[],
  taskApiNameSet: Set<string>,
  fieldMap: Map<string, string>,
): TGraphEdge[] {
  const edges: TGraphEdge[] = [];
  const hasAncestors = task.ancestors.length > 0;
  const skipConditions = task.conditions.filter((c) => c.action === EConditionAction.SkipTask);
  const startConditions = task.conditions.filter((c) => c.action === EConditionAction.StartTask);
  const hasConditions = skipConditions.length > 0 || startConditions.length > 0;
  const incomingSummary = hasConditions
    ? startConditions.map((c) => getConditionSummary(c, fieldMap)).join(' | ') || undefined
    : undefined;

  if (!hasAncestors) {
    const sourceId = taskIndex === 0 ? KICKOFF_NODE_ID : sortedTasks[taskIndex - 1].apiName;
    edges.push({
      id: buildEdgeId(sourceId, task.apiName, '0'),
      source: sourceId,
      target: task.apiName,
      sourceHandle: 'source-bottom',
      targetHandle: 'target-top',
      type: 'smoothstep',
      data: {
        summary: incomingSummary,
        isConditional: false,
      },
      labelShowBg: false,
      style: EDGE_STYLE_DEFAULT,
    });
  } else {
    task.ancestors.forEach((ancestorApiName, idx) => {
      if (!taskApiNameSet.has(ancestorApiName) && ancestorApiName !== KICKOFF_NODE_ID) return;
      edges.push({
        id: buildEdgeId(ancestorApiName, task.apiName, String(idx)),
        source: ancestorApiName,
        target: task.apiName,
        sourceHandle: 'source-bottom',
        targetHandle: 'target-top',
        type: 'smoothstep',
        data: {
          summary: incomingSummary,
          isConditional: false,
        },
        labelShowBg: false,
        style: EDGE_STYLE_DEFAULT,
      });
    });
  }

  if (skipConditions.length > 0) {
    const nextTask = sortedTasks[taskIndex + 1];
    let sourceId: string;

    if (hasAncestors) {
      [sourceId] = task.ancestors;
    } else if (taskIndex === 0) {
      sourceId = KICKOFF_NODE_ID;
    } else {
      sourceId = sortedTasks[taskIndex - 1].apiName;
    }

    if (nextTask) {
      skipConditions.forEach((condition, idx) => {
        edges.push({
          id: buildEdgeId(sourceId, nextTask.apiName, `skip-${idx}`),
          source: sourceId,
          target: nextTask.apiName,
          sourceHandle: 'source-skip',
          targetHandle: 'target-skip',
          type: 'smoothstep',
          data: {
            summary: getConditionSummary(condition, fieldMap),
            isConditional: true,
          },
          labelShowBg: false,
          className: GRAPH_EDGE_CLASS_SKIP,
          style: EDGE_STYLE_SKIP,
        });
      });
    }
  }

  return edges;
}

export function templateToGraph(template: ITemplateClient): IGraphState {
  const { tasks = [], kickoff, name } = template;
  const sortedTasks = [...tasks].sort((a, b) => a.number - b.number);
  const taskApiNameSet = new Set<string>(sortedTasks.map((t) => t.apiName));
  const fieldMap = buildFieldMap(template);
  const nodeStyle = { width: GRAPH_NODE_WIDTH, height: GRAPH_NODE_HEIGHT };

  const kickoffNode: TGraphNode = {
    id: KICKOFF_NODE_ID,
    type: EGraphNodeType.Kickoff,
    position: { x: 0, y: 0 },
    style: nodeStyle,
    data: {
      kickoff: kickoff ?? { description: '', fields: [] },
      templateName: name ?? '',
    },
  };

  const taskNodes: TGraphNode[] = sortedTasks.map((task) => ({
    id: task.apiName,
    type: EGraphNodeType.Task,
    position: { x: 0, y: 0 },
    style: nodeStyle,
    data: {
      task,
      isSelected: false,
      onEdit: () => {},
    },
  }));

  const edges: TGraphEdge[] = sortedTasks.flatMap((task, index) =>
    buildEdgesForTask(task, index, sortedTasks, taskApiNameSet, fieldMap),
  );

  return applyConnectedHandles(insertJunctionNodes([kickoffNode, ...taskNodes], edges));
}
