import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';
import { IntlProvider } from 'react-intl';

import { GraphViewToggle } from '../GraphViewToggle';
import { EGraphViewMode } from '../../../types';
import { setViewMode } from '../../../../../../redux/templateGraphView/slice';
import { enMessages } from '../../../../../../lang/locales/en_US';

jest.mock('../../../../../UI', () => ({
  Tabs: ({
    values,
    onChange,
    activeValueId,
  }: {
    values: { id: string; label: React.ReactNode }[];
    onChange: (id: string) => void;
    activeValueId: string;
  }) => (
    <div>
      {values.map((value) => (
        <button
          key={String(value.id)}
          type="button"
          onClick={() => {
            if (value.id !== activeValueId) {
              onChange(value.id);
            }
          }}
        >
          {value.label}
        </button>
      ))}
    </div>
  ),
}));

const mockDispatch = jest.fn();

const renderToggle = (
  viewMode: EGraphViewMode = EGraphViewMode.List,
  selectedTaskApiName: string | null = null,
) => {
  (useDispatch as jest.Mock).mockReturnValue(mockDispatch);
  (useSelector as jest.Mock).mockImplementation((selector: (state: unknown) => unknown) =>
    selector({
      templateGraphView: {
        viewMode,
        selectedTaskApiName,
      },
    }),
  );

  return render(
    <IntlProvider locale="en" messages={enMessages}>
      <GraphViewToggle />
    </IntlProvider>,
  );
};

describe('GraphViewToggle', () => {
  beforeEach(() => {
    mockDispatch.mockClear();
  });

  it('should render Line and Graph segments', () => {
    renderToggle();

    expect(screen.getByRole('group', { name: 'View mode' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Line' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Graph' })).toBeInTheDocument();
  });

  it('should dispatch graph view mode when Graph is clicked', () => {
    renderToggle();

    userEvent.click(screen.getByRole('button', { name: 'Graph' }));

    expect(mockDispatch).toHaveBeenCalledWith(setViewMode(EGraphViewMode.Graph));
  });

  it('should dispatch list view mode when Line is clicked', () => {
    renderToggle(EGraphViewMode.Graph);

    userEvent.click(screen.getByRole('button', { name: 'Line' }));

    expect(mockDispatch).toHaveBeenCalledWith(setViewMode(EGraphViewMode.List));
  });

  it('should not change view mode when the active segment is clicked again', () => {
    renderToggle(EGraphViewMode.Graph, 'task-1');

    userEvent.click(screen.getByRole('button', { name: 'Graph' }));

    expect(mockDispatch).not.toHaveBeenCalled();
  });
});
