import { IHighlightsItem } from '../../types/highlights';

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
