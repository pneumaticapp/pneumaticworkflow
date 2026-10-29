import { ChangeEvent } from 'react';

import { EHighlightsDateFilter, IHighlightsItem, THighlightsDateFilter } from '../../types/highlights';
import { ITemplateTitleBaseWithCount } from '../../types/template';
import { TUserListItem } from '../../types/user';
import { IHighlightsFilters } from '../../types/redux';

export interface IDateFilterProps {
  endDate: Date | null;
  selectedDateFilter: THighlightsDateFilter;
  startDate: Date | null;
  changeEndDate(date: Date): void;
  changeSelectedDateFilter(filter: EHighlightsDateFilter): () => void;
  changeStartDate(date: Date): void;
  /**
   * Reports whether Custom range draft is complete (both ends set),
   * or true for non-Custom presets. Used to disable Apply while editing.
   */
  onCustomRangeValidityChange?(isComplete: boolean): void;
}

export interface IUsersFilterProps {
  searchText: string;
  selectedUsers: number[];
  users: TUserListItem[];
  changeUsersFilter(userId: number): (e: ChangeEvent<HTMLInputElement>) => void;
  changeUsersSearchText(e: ChangeEvent<HTMLInputElement>): void;
}

export interface ITemplatesFilterProps {
  searchText: string;
  selectedTemplates: number[];
  templatesTitles: ITemplateTitleBaseWithCount[];
  isFiltersLoading: boolean;
  changeTemplatesSearchText(e: ChangeEvent<HTMLInputElement>): void;
  changeTemplatesFilter(templateId: number): (e: ChangeEvent<HTMLInputElement>) => void;
}

export type TFeedItemHeaderProps = IHighlightsItem;

export interface IFeedItemCommentProps extends Pick<TFeedItemHeaderProps, 'attachments' | 'task' | 'text' | 'type'> {
  isTextExpanded: boolean;
  onExpand: () => void;
}

export interface IFeedItemOutputsProps extends Pick<TFeedItemHeaderProps, 'task' | 'type'> {
  kickoff: TFeedItemHeaderProps['workflow']['kickoff'];
  isTextExpanded: boolean;
  onExpand: () => void;
}

export type TPerformerChangeProps = Pick<TFeedItemHeaderProps, 'targetGroupId' | 'targetUserId' | 'type'>;

export interface IHighlightsListProps {
  isFirstFetch: boolean;
}

export interface IHighlightsPlaceholderProps {
  hasChangedFilters: boolean;
}

export type THighlightsQuerySyncProps = Pick<
  IHighlightsFilters,
  'timeRange' | 'startDate' | 'endDate' | 'usersFilter' | 'templatesFilter'
>;
