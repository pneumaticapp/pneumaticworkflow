import * as React from 'react';
import { Column } from 'react-table';
import { TableColumns } from '../../types';
import { Skeleton } from '../../../../../UI/Skeleton';
import { ETableViewFieldsWidth } from './WorkflowTableConstants';

const SKELETON_SIZES = {
  SMALL: '2rem',
  MEDIUM: '8rem',
  LARGE: '24rem',
} as const;

export const SkeletonDefaultCell80 = () => <Skeleton width={SKELETON_SIZES.MEDIUM} height={SKELETON_SIZES.SMALL} />;

const WorkflowSkeletonCell = () => (
  <div style={{ display: 'flex', gap: '1.6rem' }}>
    <Skeleton width={SKELETON_SIZES.SMALL} height={SKELETON_SIZES.SMALL} />
    <Skeleton width={SKELETON_SIZES.SMALL} height={SKELETON_SIZES.SMALL} />
    <Skeleton width={SKELETON_SIZES.LARGE} height={SKELETON_SIZES.SMALL} />
  </div>
);

const StarterSkeletonCell20 = () => (
  <div style={{ display: 'flex', justifyContent: 'center' }}>
    <Skeleton width={SKELETON_SIZES.SMALL} height={SKELETON_SIZES.SMALL} />
  </div>
);

const TaskSkeletonCell240 = () => <Skeleton width={SKELETON_SIZES.LARGE} height={SKELETON_SIZES.SMALL} />;

const PerformerSkeletonCell = () => (
  <div style={{ display: 'flex', gap: '0.2rem' }}>
    <Skeleton width={SKELETON_SIZES.SMALL} height={SKELETON_SIZES.SMALL} />
    <Skeleton width={SKELETON_SIZES.SMALL} height={SKELETON_SIZES.SMALL} />
    <Skeleton width={SKELETON_SIZES.SMALL} height={SKELETON_SIZES.SMALL} />
  </div>
);

export const defaultSystemSkeletonTable: Column<TableColumns>[] = [
  {
    Header: <SkeletonDefaultCell80 />,
    accessor: 'system-column-workflow',
    Cell: WorkflowSkeletonCell,
    width: ETableViewFieldsWidth['system-column-workflow'],
  },
  {
    Header: <SkeletonDefaultCell80 />,
    accessor: 'system-column-starter',
    Cell: StarterSkeletonCell20,
    width: ETableViewFieldsWidth['system-column-starter'],
  },
  {
    Header: <SkeletonDefaultCell80 />,
    accessor: 'system-column-progress',
    Cell: SkeletonDefaultCell80,
    width: ETableViewFieldsWidth['system-column-progress'],
  },
  {
    Header: <SkeletonDefaultCell80 />,
    accessor: 'system-column-step',
    Cell: TaskSkeletonCell240,
    width: ETableViewFieldsWidth['system-column-step'],
  },
  {
    Header: <SkeletonDefaultCell80 />,
    accessor: 'system-column-performer',
    Cell: PerformerSkeletonCell,
    width: ETableViewFieldsWidth['system-column-performer'],
  },
];
