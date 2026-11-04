import { connect } from 'react-redux';

import type { RootState } from '../../../../redux/store';

import { IPopupCommentFieldProps, PopupCommentField } from './PopupCommentField';

export type TPopupCommentFieldStoreProps = Pick<IPopupCommentFieldProps, 'user'>;

export function mapStateToProps({ authUser }: RootState): TPopupCommentFieldStoreProps {
  return { user: authUser };
}

export const PopupCommentFieldContainer = connect<TPopupCommentFieldStoreProps, {}>(mapStateToProps)(PopupCommentField);
