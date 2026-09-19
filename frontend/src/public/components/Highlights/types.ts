import { ChangeEvent } from 'react';

import { EHighlightsDateFilter, IHighlightsItem, THighlightsDateFilter } from '../../types/highlights';
import { ITemplateTitleBaseWithCount } from '../../types/template';
import { TUserListItem } from '../../types/user';

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

export interface IFeedItemHeaderProps extends IHighlightsItem {}

export interface IFeedItemCommentProps
  extends Pick<IFeedItemHeaderProps, 'attachments' | 'task' | 'text' | 'type'> {
  isTextExpanded: boolean;
  onExpand: () => void;
}

export interface IFeedItemOutputsProps extends Pick<IFeedItemHeaderProps, 'task' | 'type'> {
  kickoff: IFeedItemHeaderProps['workflow']['kickoff'];
  isTextExpanded: boolean;
  onExpand: () => void;
}

export interface IPerformerChangeProps
  extends Pick<IFeedItemHeaderProps, 'targetGroupId' | 'targetUserId' | 'type'> {}
