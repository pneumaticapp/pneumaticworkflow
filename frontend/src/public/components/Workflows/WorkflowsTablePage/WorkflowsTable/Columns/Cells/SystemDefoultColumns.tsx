import React from 'react';
import { Column } from 'react-table';
import { TableColumns } from '../../types';
import { Skeleton } from '../../../../../UI/Skeleton';
import { ETableViewFieldsWidth } from './WorkflowTableConstants';

const SKELETON_SIZES = {
  SMALL: '2rem',
  MEDIUM: '8rem',
  LARGE: '24rem',
} as const;

const SkeletonDefaultCell80 = () => (
  <Skeleton width={SKELETON_SIZES.MEDIUM} height={SKELETON_SIZES.SMALL} aria-label="Loading header" />
);

const WorkflowSkeletonCell = () => (
  <div style={{ display: 'flex', gap: '1.6rem' }}>
    <Skeleton width={SKELETON_SIZES.SMALL} height={SKELETON_SIZES.SMALL} aria-label="Loading icon" />
    <Skeleton width={SKELETON_SIZES.SMALL} height={SKELETON_SIZES.SMALL} aria-label="Loading status" />
    <Skeleton width={SKELETON_SIZES.LARGE} height={SKELETON_SIZES.SMALL} aria-label="Loading workflow name" />
  </div>
);

const StarterSkeletonCell20 = () => (
  <div style={{ display: 'flex', justifyContent: 'center' }}>
    <Skeleton width={SKELETON_SIZES.SMALL} height={SKELETON_SIZES.SMALL} aria-label="Loading starter" />
  </div>
);

const TaskSkeletonCell240 = () => (
  <Skeleton width={SKELETON_SIZES.LARGE} height={SKELETON_SIZES.SMALL} aria-label="Loading task" />
);

const PerformerSkeletonCell = () => (
  <div style={{ display: 'flex', gap: '0.2rem' }}>
    <Skeleton width={SKELETON_SIZES.SMALL} height={SKELETON_SIZES.SMALL} aria-label="Loading performer 1" />
    <Skeleton width={SKELETON_SIZES.SMALL} height={SKELETON_SIZES.SMALL} aria-label="Loading performer 2" />
    <Skeleton width={SKELETON_SIZES.SMALL} height={SKELETON_SIZES.SMALL} aria-label="Loading performer 3" />
  </div>
);

export const defaultSystemColumns: Column<TableColumns>[] = [
  {
    Header: <SkeletonDefaultCell80 />,
    accessor: 'workflow',
    Cell: WorkflowSkeletonCell,
    width: ETableViewFieldsWidth.workflow,
  },
  {
    Header: <SkeletonDefaultCell80 />,
    accessor: 'starter',
    Cell: StarterSkeletonCell20,
    width: ETableViewFieldsWidth.starter,
  },
  {
    Header: <SkeletonDefaultCell80 />,
    accessor: 'progress',
    Cell: SkeletonDefaultCell80,
    width: ETableViewFieldsWidth.progress,
  },
  {
    Header: <SkeletonDefaultCell80 />,
    accessor: 'step',
    Cell: TaskSkeletonCell240,
    width: ETableViewFieldsWidth.step,
  },
  {
    Header: <SkeletonDefaultCell80 />,
    accessor: 'performer',
    Cell: PerformerSkeletonCell,
    width: ETableViewFieldsWidth.performer,
  },
];
