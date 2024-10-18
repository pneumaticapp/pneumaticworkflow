import { connect } from 'react-redux';

import { IApplicationState } from '../../../../types/redux';

import { IPopupCommentFieldProps, PopupCommentField } from './PopupCommentField';

export type TPopupCommentFieldStoreProps = Pick<IPopupCommentFieldProps, 'user'>;

export function mapStateToProps({ authUser }: IApplicationState): TPopupCommentFieldStoreProps {
  return { user: authUser };
}

export const PopupCommentFieldContainer = connect<TPopupCommentFieldStoreProps, {}>(mapStateToProps)(PopupCommentField);
