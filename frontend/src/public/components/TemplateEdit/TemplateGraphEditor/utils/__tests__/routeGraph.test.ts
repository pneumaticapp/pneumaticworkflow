import { GRAPH_APPROVAL_LADDER_TEMPLATE } from '../../fixtures/graphApprovalLadderTemplate';
import { GRAPH_SHOWCASE_TEMPLATE } from '../../fixtures/graphShowcaseTemplate';
import { GRAPH_TEMPLATE_259 } from '../../fixtures/graphTemplate259';
import { EGraphNodeType } from '../../types';
import { buildTemplateGraph } from '../buildTemplateGraph';
import { GRAPH_JUNCTION_SIZE, GRAPH_NODE_WIDTH } from '../graphGeometry';
import { applyMovedCard } from '../routeGraph';

describe('applyMovedCard', () => {
  it('should keep every node when one card moves', () => {
    const graph = buildTemplateGraph(GRAPH_SHOWCASE_TEMPLATE);
    const task = graph.nodes.find((node) => node.id === 'task-linear');
    const nodeIds = graph.nodes.map((node) => node.id).sort();

    expect(task).toBeDefined();

    const next = applyMovedCard(graph.nodes, graph.edges, {
      ...task!,
      position: { x: 900, y: 450 },
    });

    expect(next.nodes.map((node) => node.id).sort()).toEqual(nodeIds);
    expect(next.nodes.find((node) => node.id === 'task-linear')?.position).toEqual({ x: 900, y: 450 });
  });

  it('should realign a fork to the moved parent card', () => {
    const graph = buildTemplateGraph(GRAPH_SHOWCASE_TEMPLATE);
    const task = graph.nodes.find((node) => node.id === 'task-url-title');
    const nextPosition = { x: (task?.position.x ?? 0) + 200, y: task?.position.y ?? 0 };

    expect(task).toBeDefined();

    const next = applyMovedCard(graph.nodes, graph.edges, {
      ...task!,
      position: nextPosition,
    });
    const fork = next.nodes.find((node) => node.id === 'junction-fork-task-url-title');

    expect(fork?.position.x).toBe(nextPosition.x + GRAPH_NODE_WIDTH / 2 - GRAPH_JUNCTION_SIZE / 2);
  });

  it('should not drop sibling cards if only the moved node is passed as context', () => {
    const graph = buildTemplateGraph(GRAPH_SHOWCASE_TEMPLATE);
    const taskCount = graph.nodes.filter((node) => node.type === EGraphNodeType.Task).length;
    const task = graph.nodes.find((node) => node.id === 'task-linear');

    expect(task).toBeDefined();

    const next = applyMovedCard(graph.nodes, graph.edges, {
      ...task!,
      position: { x: 10, y: 20 },
    });

    expect(next.nodes.filter((node) => node.type === EGraphNodeType.Task)).toHaveLength(taskCount);
  });

  it('should update edge handles together with the line when a card moves', () => {
    const graph = buildTemplateGraph(GRAPH_SHOWCASE_TEMPLATE);
    const task = graph.nodes.find((node) => node.id === 'task-parallel-b');

    expect(task).toBeDefined();

    const next = applyMovedCard(graph.nodes, graph.edges, {
      ...task!,
      position: { x: (task?.position.x ?? 0) + 280, y: (task?.position.y ?? 0) + 120 },
    });
    const intoMoved = next.edges.find((edge) => edge.target === 'task-parallel-b');

    expect(next.nodes.find((node) => node.id === 'task-parallel-b')?.position.x).toBe((task?.position.x ?? 0) + 280);
    expect(intoMoved?.sourceHandle).toBeDefined();
    expect(intoMoved?.targetHandle).toBeDefined();
    expect(intoMoved?.data?.sourceAnchor).toBeDefined();
    expect(intoMoved?.data?.targetAnchor).toBeDefined();
  });

  it('should anchor every line while a card is still in flight', () => {
    const graph = buildTemplateGraph(GRAPH_APPROVAL_LADDER_TEMPLATE);
    const task = graph.nodes.find((node) => node.id === 'source-3');

    expect(task).toBeDefined();

    const next = applyMovedCard(graph.nodes, graph.edges, {
      ...task!,
      position: { x: (task?.position.x ?? 0) + 160, y: task?.position.y ?? 0 },
      dragging: true,
    });

    expect(next.edges).toHaveLength(graph.edges.length);
    expect(next.edges.every((edge) => edge.data?.sourceAnchor && edge.data?.targetAnchor)).toBe(true);
  });

  it('should keep the large template fully anchored while a card is in flight', () => {
    const graph = buildTemplateGraph(GRAPH_TEMPLATE_259);
    const task = graph.nodes.find((node) => node.id === 'template-259-task-20');

    expect(task).toBeDefined();

    const next = applyMovedCard(graph.nodes, graph.edges, {
      ...task!,
      position: { x: (task?.position.x ?? 0) + 160, y: task?.position.y ?? 0 },
      dragging: true,
    });

    expect(next.edges).toHaveLength(graph.edges.length);
    expect(next.edges.every((edge) => edge.data?.sourceAnchor && edge.data?.targetAnchor)).toBe(true);
  });

  it('should settle the routes only once the card is dropped', () => {
    const graph = buildTemplateGraph(GRAPH_APPROVAL_LADDER_TEMPLATE);
    const task = graph.nodes.find((node) => node.id === 'source-3');
    const moved = { ...task!, position: { x: (task?.position.x ?? 0) + 160, y: task?.position.y ?? 0 } };

    const inFlight = applyMovedCard(graph.nodes, graph.edges, { ...moved, dragging: true });
    const dropped = applyMovedCard(graph.nodes, graph.edges, { ...moved, dragging: false });

    const alleysWhileDragging = inFlight.edges.filter((edge) => edge.data?.laneY != null).length;
    const alleysAfterDrop = dropped.edges.filter((edge) => edge.data?.laneY != null).length;

    expect(alleysAfterDrop).toBeGreaterThan(alleysWhileDragging);
  });
});
