import { connect } from 'react-redux';
import { IApplicationState } from '../../types/redux';
import { getNotDeletedUsers } from '../../utils/users';
import { getMentionData } from './utils/getMentionData';
import { IRichEditorProps } from './RichEditor.props';
import { RichEditor } from './RichEditor';

type TStoreProps = Pick<IRichEditorProps, 'mentions' | 'accountId'>;
type TOwnProps = Partial<Pick<IRichEditorProps, 'accountId'>>;

const mapStateToProps = (
  { accounts: { users }, authUser: { account } }: IApplicationState,
  { accountId }: TOwnProps,
): TStoreProps => {
  const usersToMention = getNotDeletedUsers(users);

  return {
    mentions: getMentionData(usersToMention),
    accountId: account.id || accountId || -1,
  };
};

export const RichEditorContainer = connect(mapStateToProps, null, null, { forwardRef: true })(RichEditor);
