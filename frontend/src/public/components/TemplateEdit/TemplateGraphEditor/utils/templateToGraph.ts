import { ITemplateClient, ITemplateTaskClient } from '../../../../types/template';
import { EConditionAction } from '../../TaskForm/Conditions';
import { EStartingType } from '../../TaskForm/Conditions/utils/getDropdownOperators';
import { EGraphNodeType, IGraphState, TGraphEdge, TGraphNode } from '../types';
import { GRAPH_NODE_HEIGHT, GRAPH_NODE_WIDTH } from './graphGeometry';
import { getGraphEdgeVisual } from './edgeStyles';
import { insertJunctionNodes } from './insertJunctionNodes';

export const KICKOFF_NODE_ID = 'kickoff';

/** Marker for the kick-off form as an edge source; the label is localized in the UI. */
export const KICKOFF_START_AFTER = '__kickoff__';

function buildEdgeId(source: string, target: string, suffix: string): string {
  return `edge-${source}-${target}-${suffix}`;
}

function uniqueIds(ids: string[]): string[] {
  const seen = new Set<string>();

  return ids.filter((id) => {
    if (seen.has(id)) {
      return false;
    }

    seen.add(id);

    return true;
  });
}

function getStartAfterLabel(sourceId: string, sortedTasks: ITemplateTaskClient[]): string {
  if (sourceId === KICKOFF_NODE_ID) {
    return KICKOFF_START_AFTER;
  }

  const source = sortedTasks.find((task) => task.apiName === sourceId);

  return source?.name || sourceId;
}

function getStartAfterSources(task: ITemplateTaskClient, taskApiNameSet: Set<string>): string[] {
  const startCondition = task.conditions.find((condition) => condition.action === EConditionAction.StartTask);
  const sources: string[] = [];

  startCondition?.rules.forEach((rule) => {
    if (rule.fieldType === EStartingType.Kickoff) {
      sources.push(KICKOFF_NODE_ID);

      return;
    }

    if (rule.fieldType === EStartingType.Task && rule.field && taskApiNameSet.has(rule.field)) {
      sources.push(rule.field);
    }
  });

  return uniqueIds(sources);
}

/** `ancestors` from the API is a transitive closure; the graph only needs direct parents. */
function getDirectParents(
  task: ITemplateTaskClient,
  tasksByApiName: Map<string, ITemplateTaskClient>,
): string[] {
  return task.ancestors.filter((apiName) => {
    if (apiName === KICKOFF_NODE_ID) {
      return true;
    }

    if (!tasksByApiName.has(apiName)) {
      return false;
    }

    return !task.ancestors.some((otherApiName) => {
      if (otherApiName === apiName) {
        return false;
      }

      return tasksByApiName.get(otherApiName)?.ancestors.includes(apiName) ?? false;
    });
  });
}

function isUpstreamOf(
  maybeAncestorId: string,
  taskId: string,
  tasksByApiName: Map<string, ITemplateTaskClient>,
  taskApiNameSet: Set<string>,
): boolean {
  if (maybeAncestorId === KICKOFF_NODE_ID && taskId !== KICKOFF_NODE_ID) {
    return true;
  }

  const seen = new Set<string>();
  const stack = [taskId];

  while (stack.length > 0) {
    const currentId = stack.pop();

    if (currentId && !seen.has(currentId)) {
      if (currentId === maybeAncestorId) {
        return true;
      }

      seen.add(currentId);
      const current = tasksByApiName.get(currentId);

      if (current) {
        current.ancestors.forEach((ancestorId) => stack.push(ancestorId));
        getStartAfterSources(current, taskApiNameSet).forEach((sourceId) => stack.push(sourceId));
      }
    }
  }

  return false;
}

/** Drop a source if another listed source already sits downstream of it. */
function dropImpliedSources(
  sources: string[],
  tasksByApiName: Map<string, ITemplateTaskClient>,
  taskApiNameSet: Set<string>,
): string[] {
  return sources.filter((sourceId) => (
    !sources.some((otherId) => (
      otherId !== sourceId
      && isUpstreamOf(sourceId, otherId, tasksByApiName, taskApiNameSet)
    ))
  ));
}

function getIncomingSources(
  task: ITemplateTaskClient,
  taskIndex: number,
  sortedTasks: ITemplateTaskClient[],
  taskApiNameSet: Set<string>,
  tasksByApiName: Map<string, ITemplateTaskClient>,
): string[] {
  const fromStartAfter = getStartAfterSources(task, taskApiNameSet);
  if (fromStartAfter.length > 0) {
    return dropImpliedSources(fromStartAfter, tasksByApiName, taskApiNameSet);
  }

  const directParents = getDirectParents(task, tasksByApiName).filter(
    (apiName) => taskApiNameSet.has(apiName) || apiName === KICKOFF_NODE_ID,
  );
  if (directParents.length > 0) {
    return directParents;
  }

  return [taskIndex === 0 ? KICKOFF_NODE_ID : sortedTasks[taskIndex - 1].apiName];
}

function buildIncomingEdge(
  sourceId: string,
  task: ITemplateTaskClient,
  suffix: string,
  sortedTasks: ITemplateTaskClient[],
): TGraphEdge {
  return {
    id: buildEdgeId(sourceId, task.apiName, suffix),
    source: sourceId,
    target: task.apiName,
    sourceHandle: 'source-bottom',
    targetHandle: 'target-top',
    type: 'smoothstep',
    data: {
      isConditional: false,
      startAfter: [getStartAfterLabel(sourceId, sortedTasks)],
    },
    labelShowBg: false,
    ...getGraphEdgeVisual(false),
  };
}

function buildCardNodes(template: ITemplateClient, sortedTasks: ITemplateTaskClient[]): TGraphNode[] {
  const { kickoff, name } = template;
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

  return [kickoffNode, ...taskNodes];
}

export function templateToGraph(template: ITemplateClient): IGraphState {
  const { tasks = [] } = template;
  const sortedTasks = [...tasks].sort((a, b) => a.number - b.number);
  const taskApiNameSet = new Set<string>(sortedTasks.map((task) => task.apiName));
  const tasksByApiName = new Map(sortedTasks.map((task) => [task.apiName, task]));
  const nodes = buildCardNodes(template, sortedTasks);
  const edges: TGraphEdge[] = sortedTasks.flatMap((task, index) => (
    getIncomingSources(task, index, sortedTasks, taskApiNameSet, tasksByApiName).map((sourceId, idx) =>
      buildIncomingEdge(sourceId, task, String(idx), sortedTasks),
    )
  ));

  return insertJunctionNodes(nodes, edges);
}
