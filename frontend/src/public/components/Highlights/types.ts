import { ChangeEvent } from 'react';

import { THighlightsDateFilter, EHighlightsDateFilter } from '../../types/highlights';
import { TUserListItem } from '../../types/user';
import { ITemplateTitleBaseWithCount } from '../../types/template';

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
