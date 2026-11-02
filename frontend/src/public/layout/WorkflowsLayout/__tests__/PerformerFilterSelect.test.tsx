import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useDispatch, useSelector } from 'react-redux';

import { PerformerFilterSelect } from '../PerformerFilterSelect';
import { makeUser } from '../../../__stubs__/users.factory';
import { EWorkflowsStatus } from '../../../types/workflow';
import { setFilterPerformers, setFilterPerformersGroup } from '../../../redux/workflows/slice';
import {
  getWorkflowPerformersCounters,
  getWorkflowPerformersGroupsIdsFilter,
  getWorkflowPerformersIdsFilter,
  getWorkflowsStatus,
} from '../../../redux/selectors/workflows';
import { getRegularGroupsList } from '../../../redux/selectors/groups';
import { getAccountsUsers } from '../../../redux/selectors/accounts';

jest.mock('react-redux', () => ({
  useDispatch: jest.fn(),
  useSelector: jest.fn(),
}));

jest.mock('../../../hooks/useCheckDevice', () => ({
  useCheckDevice: () => ({ isMobile: false }),
}));

jest.mock('../../../components/UI', () => ({
  Avatar: () => null,
}));

const dispatch = jest.fn();

const mockState = ({ groupIds = [] as number[], userIds = [] as number[] } = {}) => {
  const values = new Map<unknown, unknown>([
    [getWorkflowPerformersGroupsIdsFilter, groupIds],
    [getWorkflowPerformersIdsFilter, userIds],
    [getWorkflowPerformersCounters, []],
    [getWorkflowsStatus, EWorkflowsStatus.Running],
    [getRegularGroupsList, [{ id: 1, name: 'Designers', users: [] }]],
    [getAccountsUsers, [makeUser({ id: 1, firstName: 'Ada', lastName: 'Lovelace' })]],
  ]);
  (useSelector as jest.Mock).mockImplementation((selector: unknown) => values.get(selector));
};

describe('PerformerFilterSelect', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useDispatch as jest.Mock).mockReturnValue(dispatch);
  });

  it('keeps a group and a user with the same id as separate selections', () => {
    mockState({ groupIds: [1] });
    render(<PerformerFilterSelect />);

    userEvent.click(screen.getByRole('button', { name: 'Designers' }));
    const [groupCheckbox, userCheckbox] = screen.getAllByRole('checkbox') as HTMLInputElement[];
    expect(groupCheckbox.checked).toBe(true);
    expect(userCheckbox.checked).toBe(false);

    userEvent.click(screen.getByText('Ada Lovelace'));

    expect(dispatch).toHaveBeenCalledWith(setFilterPerformers([1]));
    expect(dispatch).toHaveBeenCalledWith(setFilterPerformersGroup([1]));
  });

  it('clears users and groups from the pill', () => {
    mockState({ userIds: [1] });
    render(<PerformerFilterSelect />);

    userEvent.click(screen.getByRole('button', { name: 'Clear selected options' }));

    expect(dispatch).toHaveBeenCalledWith(setFilterPerformers([]));
    expect(dispatch).toHaveBeenCalledWith(setFilterPerformersGroup([]));
  });
});
