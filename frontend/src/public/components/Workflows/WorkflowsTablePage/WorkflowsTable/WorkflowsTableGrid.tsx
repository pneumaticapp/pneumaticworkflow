import React from 'react';
import classNames from 'classnames';

import { SKELETON_ROWS } from './constants';
import { defaultSystemSkeletonTable } from './Columns/Cells';
import { SkeletonDefaultCell80 } from './Columns/Cells/SystemDefaultColumns';
import { Skeleton } from '../../../UI/Skeleton';
import { CustomHeaderGroup, TableColumns, WorkflowsTableGridProps } from './types';

import styles from './WorkflowsTable.css';

const getSkeletonWidth = (width?: number) => `${width ? Math.max(width * 0.7, 80) : 80}px`;

export function WorkflowsTableGrid({
  table,
  tableRef,
  tableHeight,
  columns,
  colWidths,
  handleMouseDown,
  itemsCount,
  shouldSkeletonBody,
  shouldSkeletonDefaultTable,
  shouldSkeletonOptionalTable,
}: WorkflowsTableGridProps) {
  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = table;

  const getTableBodyContent = () => {
    if (shouldSkeletonDefaultTable) {
      return SKELETON_ROWS.map((row) => (
        <tr className={styles['row']} key={row}>
          {defaultSystemSkeletonTable.map((column) => (
            <td key={column.accessor as string} className={styles['column']}>
              {(column as any).Cell({})}
            </td>
          ))}
        </tr>
      ));
    }

    if (itemsCount === 0 && (shouldSkeletonBody || shouldSkeletonOptionalTable)) {
      return SKELETON_ROWS.map((row) => (
        <tr className={styles['row']} key={row}>
          {columns.map((column) => (
            <td key={column.accessor as string} className={styles['column']} aria-label="Loading">
              <Skeleton width={getSkeletonWidth(column.width as number)} height="2rem" />
            </td>
          ))}
        </tr>
      ));
    }

    return rows.map((row) => {
      prepareRow(row);
      const workflowId = row.original['system-column-workflow'].id;

      return (
        <tr {...row.getRowProps()} className={styles['row']} key={workflowId}>
          {row.cells.map((cell) => (
            <td
              {...cell.getCellProps({
                style: {
                  width: colWidths[cell.column.id],
                  maxWidth: colWidths[cell.column.id],
                  minWidth: colWidths[cell.column.id],
                },
              })}
              className={styles['column']}
            >
              {shouldSkeletonOptionalTable || shouldSkeletonBody ? (
                <Skeleton width={getSkeletonWidth(colWidths[cell.column.id])} height="2rem" />
              ) : (
                cell.render('Cell')
              )}
            </td>
          ))}
        </tr>
      );
    });
  };

  return (
    <table {...getTableProps()} className={styles['table']} ref={tableRef}>
      <thead className={styles['thead']}>
        {shouldSkeletonDefaultTable ? (
          <tr>
            {defaultSystemSkeletonTable.map((column) => (
              <th
                key={column.accessor as string}
                style={{
                  position: 'relative',
                  width: (column as any).width,
                  maxWidth: (column as any).width,
                  minWidth: (column as any).width,
                }}
                className={classNames(styles['column-header'], styles['column'])}
              >
                {(column as any).Header}
              </th>
            ))}
          </tr>
        ) : (
          headerGroups.map((headerGroup) => (
            <tr {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map((column: CustomHeaderGroup<TableColumns>) => (
                <th
                  {...column.getHeaderProps({
                    style: {
                      position: 'relative',
                      width: colWidths[column.id],
                      maxWidth: colWidths[column.id],
                      minWidth: colWidths[column.id],
                    },
                  })}
                  className={classNames(styles['column-header'], styles['column'])}
                >
                  {shouldSkeletonOptionalTable ? <SkeletonDefaultCell80 /> : column.render('Header')}
                  <div className={styles['column-header__hover-zone']} style={{ height: tableHeight }}>
                    <div
                      className={styles['column-header__resize']}
                      style={{ height: tableHeight }}
                      onMouseDown={(event) => handleMouseDown(event, column.id, column.minWidth)}
                      role="button"
                      aria-label={`Resize column ${column.id}`}
                      tabIndex={0}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault();
                        }
                      }}
                    >
                      <div className={styles['column-header__dashed-line']} style={{ height: tableHeight }} />
                    </div>
                  </div>
                </th>
              ))}
            </tr>
          ))
        )}
      </thead>
      <tbody {...getTableBodyProps()}>{getTableBodyContent()}</tbody>
    </table>
  );
}
