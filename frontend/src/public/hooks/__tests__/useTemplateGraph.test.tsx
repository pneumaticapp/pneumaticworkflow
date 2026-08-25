import * as React from 'react';
import { useEffect } from 'react';
import { act, render, waitFor } from '@testing-library/react';
import { Node } from 'reactflow';

import { GRAPH_SHOWCASE_TEMPLATE } from '../../components/TemplateEdit/TemplateGraphEditor/fixtures/graphShowcaseTemplate';
import { GRAPH_JUNCTION_SIZE, GRAPH_NODE_WIDTH } from '../../components/TemplateEdit/TemplateGraphEditor/utils/graphGeometry';
import { getGraphNodePositions } from '../../components/TemplateEdit/TemplateGraphEditor/utils/graphPositionsStorage';
import { useTemplateGraph } from '../useTemplateGraph';

type TTemplateGraphResult = ReturnType<typeof useTemplateGraph>;

interface IHookHarnessProps {
  onChange: (graph: TTemplateGraphResult) => void;
}

const HookHarness = ({ onChange }: IHookHarnessProps) => {
  const graph = useTemplateGraph({ ...GRAPH_SHOWCASE_TEMPLATE, id: 42 });

  useEffect(() => {
    onChange(graph);
  }, [graph, onChange]);

  return null;
};

describe('useTemplateGraph', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('should persist a moved card and update the graph state', async () => {
    let currentGraph: TTemplateGraphResult | undefined;
    const handleChange = jest.fn((graph: TTemplateGraphResult) => {
      currentGraph = graph;
    });

    render(<HookHarness onChange={handleChange} />);

    await waitFor(() => {
      expect(currentGraph?.nodes.length).toBeGreaterThan(0);
    });

    const taskNode = currentGraph!.nodes.find((node) => node.id === 'task-linear');
    const nextPosition = { x: 900, y: 450 };

    expect(taskNode).toBeDefined();

    act(() => {
      currentGraph!.onNodeDragStop(
        {} as React.MouseEvent<Element>,
        { ...taskNode!, position: nextPosition } as Node,
        [],
      );
    });

    await waitFor(() => {
      expect(currentGraph?.nodes.find((node) => node.id === 'task-linear')?.position).toEqual(nextPosition);
    });

    expect(getGraphNodePositions(42)['task-linear']).toEqual(nextPosition);
  });

  it('should realign junctions and edges while a card is dragged without saving', async () => {
    let currentGraph: TTemplateGraphResult | undefined;
    const handleChange = jest.fn((graph: TTemplateGraphResult) => {
      currentGraph = graph;
    });

    render(<HookHarness onChange={handleChange} />);

    await waitFor(() => {
      expect(currentGraph?.nodes.some((node) => node.id === 'junction-fork-task-url-title')).toBe(true);
    });

    const taskNode = currentGraph!.nodes.find((node) => node.id === 'task-url-title');
    const nextPosition = { x: (taskNode?.position.x ?? 0) + 200, y: taskNode?.position.y ?? 0 };
    const nodesDuringDrag = currentGraph!.nodes.map((node) => (
      node.id === 'task-url-title' ? { ...node, position: nextPosition } : node
    ));

    expect(taskNode).toBeDefined();

    act(() => {
      currentGraph!.onNodeDrag(
        {} as React.MouseEvent<Element>,
        { ...taskNode!, position: nextPosition } as Node,
        nodesDuringDrag as Node[],
      );
    });

    await waitFor(() => {
      const fork = currentGraph?.nodes.find((node) => node.id === 'junction-fork-task-url-title');
      expect(fork?.position.x).toBe(nextPosition.x + GRAPH_NODE_WIDTH / 2 - GRAPH_JUNCTION_SIZE / 2);
    });

    expect(getGraphNodePositions(42)['task-url-title']).toBeUndefined();
  });

  it('should reroute edge anchors while a card is dragged through onNodesChange', async () => {
    let currentGraph: TTemplateGraphResult | undefined;
    const handleChange = jest.fn((graph: TTemplateGraphResult) => {
      currentGraph = graph;
    });

    render(<HookHarness onChange={handleChange} />);

    await waitFor(() => {
      expect(currentGraph?.edges.some((edge) => edge.target === 'task-linear' && edge.data?.targetAnchor)).toBe(true);
    });

    const first = currentGraph!.nodes.find((node) => node.id === 'task-linear');
    const inbound = currentGraph!.edges.find((edge) => edge.target === 'task-linear');
    const nextPosition = { x: (first?.position.x ?? 0) + 280, y: first?.position.y ?? 0 };
    const previousAnchor = inbound?.data?.targetAnchor;

    expect(first).toBeDefined();
    expect(previousAnchor).toBeDefined();

    act(() => {
      currentGraph!.onNodesChange([
        { id: 'task-linear', type: 'position', dragging: true, position: nextPosition },
      ]);
    });

    await waitFor(() => {
      const moved = currentGraph?.nodes.find((node) => node.id === 'task-linear');
      const edgeAfter = currentGraph?.edges.find((edge) => edge.id === inbound?.id);

      expect(moved?.position).toEqual(nextPosition);
      expect(edgeAfter?.data?.targetAnchor?.x).toBe((previousAnchor?.x ?? 0) + 280);
    });
  });

  it('should keep every card when React Flow reports only the dragged node', async () => {
    let currentGraph: TTemplateGraphResult | undefined;
    const handleChange = jest.fn((graph: TTemplateGraphResult) => {
      currentGraph = graph;
    });

    render(<HookHarness onChange={handleChange} />);

    await waitFor(() => {
      expect(currentGraph?.nodes.filter((node) => node.type === 'task').length).toBeGreaterThan(1);
    });

    const taskCount = currentGraph!.nodes.filter((node) => node.type === 'task').length;
    const nodeCount = currentGraph!.nodes.length;
    const taskNode = currentGraph!.nodes.find((node) => node.id === 'task-linear');
    const nextPosition = { x: 640, y: 280 };

    expect(taskNode).toBeDefined();

    act(() => {
      currentGraph!.onNodeDrag(
        {} as React.MouseEvent<Element>,
        { ...taskNode!, position: nextPosition } as Node,
        [{ ...taskNode!, position: nextPosition } as Node],
      );
    });

    await waitFor(() => {
      expect(currentGraph?.nodes.find((node) => node.id === 'task-linear')?.position).toEqual(nextPosition);
      expect(currentGraph?.nodes).toHaveLength(nodeCount);
      expect(currentGraph?.nodes.filter((node) => node.type === 'task')).toHaveLength(taskCount);
    });
  });
});
