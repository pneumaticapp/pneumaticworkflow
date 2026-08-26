import { EGraphNodeType, IGraphInsertTaskIntent, TGraphEdge, TGraphNode } from '../../types';
import { GRAPH_EDGE_CLASS_CONDITIONAL } from '../edgeStyles';
import { applyGraphAddAffordances } from '../applyGraphAddAffordances';
import { createEmptyTaskDueDate } from '../../../../../utils/dueDate/createEmptyTaskDueDate';

function kickoffNode(): TGraphNode {
  return {
    id: 'kickoff',
    type: EGraphNodeType.Kickoff,
    position: { x: 0, y: 0 },
    data: {
      templateName: 'Template',
      kickoff: { description: '', fields: [], fieldsets: [] },
    },
  };
}

function taskNode(id: string): TGraphNode {
  return {
    id,
    type: EGraphNodeType.Task,
    position: { x: 0, y: 0 },
    data: {
      isSelected: false,
      onEdit: () => undefined,
      task: {
        apiName: id,
        name: id,
        description: '',
        number: 1,
        requireCompletionByAll: false,
        skipForStarter: false,
        fields: [],
        fieldsets: [],
        rawPerformers: [],
        delay: null,
        rawDueDate: createEmptyTaskDueDate(),
        conditions: [],
        uuid: `${id}-uuid`,
        checklists: [],
        revertTask: null,
        ancestors: [],
      },
    },
  };
}

function junctionNode(id: string, kind: 'fork' | 'join'): TGraphNode {
  return {
    id,
    type: EGraphNodeType.Junction,
    position: { x: 0, y: 0 },
    data: { kind },
  };
}

function grayEdge(source: string, target: string): TGraphEdge {
  return {
    id: `${source}->${target}`,
    source,
    target,
    data: { isConditional: false },
  };
}

function orangeEdge(source: string, target: string): TGraphEdge {
  return {
    id: `${source}->${target}-checkif`,
    source,
    target,
    className: GRAPH_EDGE_CLASS_CONDITIONAL,
    data: { isConditional: true },
  };
}

function continueAfter(nodes: TGraphNode[]): string[] {
  const ids: string[] = [];

  nodes.forEach((node) => {
    const intent = 'addTaskIntent' in node.data ? node.data.addTaskIntent : undefined;
    if (intent?.kind === 'continue') {
      ids.push(intent.afterId);
    }
  });

  return ids;
}

function insertIntents(edges: TGraphEdge[]): IGraphInsertTaskIntent[] {
  return edges
    .map((edge) => edge.data?.addTaskIntent)
    .filter((intent): intent is IGraphInsertTaskIntent => intent?.kind === 'insert');
}

describe('applyGraphAddAffordances', () => {
  it('should put continue on a leaf and insert on a unique gray edge', () => {
    const { nodes, edges } = applyGraphAddAffordances(
      [kickoffNode(), taskNode('task-a'), taskNode('task-b')],
      [grayEdge('kickoff', 'task-a'), grayEdge('task-a', 'task-b')],
    );

    expect(continueAfter(nodes)).toEqual(['task-b']);
    expect(insertIntents(edges)).toEqual([
      { kind: 'insert', afterId: 'kickoff', beforeId: 'task-a' },
      { kind: 'insert', afterId: 'task-a', beforeId: 'task-b' },
    ]);
  });

  it('should put continue on kickoff when it has no gray children', () => {
    const { nodes, edges } = applyGraphAddAffordances([kickoffNode()], []);

    expect(continueAfter(nodes)).toEqual(['kickoff']);
    expect(insertIntents(edges)).toEqual([]);
  });

  it('should treat a card with only check-if outgoing as a leaf', () => {
    const { nodes } = applyGraphAddAffordances(
      [kickoffNode(), taskNode('task-a')],
      [orangeEdge('kickoff', 'task-a')],
    );

    expect(continueAfter(nodes)).toEqual(['kickoff', 'task-a']);
  });

  it('should insert on fork→B and skip A→fork', () => {
    const { edges } = applyGraphAddAffordances(
      [taskNode('task-a'), junctionNode('fork-1', 'fork'), taskNode('task-b'), taskNode('task-c')],
      [
        grayEdge('task-a', 'fork-1'),
        grayEdge('fork-1', 'task-b'),
        grayEdge('fork-1', 'task-c'),
      ],
    );
    const inserts = insertIntents(edges);

    expect(inserts.find((intent) => intent.afterId === 'task-a' && intent.beforeId === 'task-b')).toEqual({
      kind: 'insert',
      afterId: 'task-a',
      beforeId: 'task-b',
    });
    expect(inserts.find((intent) => intent.afterId === 'task-a' && intent.beforeId === 'task-c')).toEqual({
      kind: 'insert',
      afterId: 'task-a',
      beforeId: 'task-c',
    });
    expect(edges.find((edge) => edge.source === 'task-a' && edge.target === 'fork-1')?.data?.addTaskIntent).toBeUndefined();
  });

  it('should insert on A→join and skip join→B', () => {
    const { edges } = applyGraphAddAffordances(
      [taskNode('task-a'), taskNode('task-c'), junctionNode('join-1', 'join'), taskNode('task-b')],
      [
        grayEdge('task-a', 'join-1'),
        grayEdge('task-c', 'join-1'),
        grayEdge('join-1', 'task-b'),
      ],
    );
    const inserts = insertIntents(edges);

    expect(inserts).toEqual([
      { kind: 'insert', afterId: 'task-a', beforeId: 'task-b' },
      { kind: 'insert', afterId: 'task-c', beforeId: 'task-b' },
    ]);
    expect(edges.find((edge) => edge.source === 'join-1')?.data?.addTaskIntent).toBeUndefined();
  });

  it('should skip insert on a conditional edge', () => {
    const { edges } = applyGraphAddAffordances(
      [taskNode('task-a'), taskNode('task-b')],
      [orangeEdge('task-a', 'task-b')],
    );

    expect(insertIntents(edges)).toEqual([]);
  });
});
