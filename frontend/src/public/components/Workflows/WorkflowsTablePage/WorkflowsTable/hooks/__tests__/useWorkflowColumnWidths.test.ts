/// <reference types="jest" />
import { Column } from 'react-table';

import { TableColumns } from '../../types';
import { mergeColumnWidths } from '../useWorkflowColumnWidths';

const performerColumn = (width: number): Column<TableColumns> => ({
  accessor: 'system-column-performer',
  width,
});

describe('mergeColumnWidths', () => {
  it('preserves a user-resized performer column when its minimum shrinks', () => {
    expect(mergeColumnWidths(
      { 'system-column-performer': 30 },
      [performerColumn(20)],
    )).toEqual({ 'system-column-performer': 30 });
  });

  it('expands the performer column when its minimum grows', () => {
    expect(mergeColumnWidths(
      { 'system-column-performer': 20 },
      [performerColumn(30)],
    )).toEqual({ 'system-column-performer': 30 });
  });
});
