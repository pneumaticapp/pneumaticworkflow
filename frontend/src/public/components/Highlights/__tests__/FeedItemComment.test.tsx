import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';

import { EWorkflowLogEvent } from '../../../types/workflow';
import { FeedItemComment } from '../FeedItemComment';
import { IFeedItemCommentProps } from '../types';

jest.mock('../../RichText', () => ({
  RichText: ({ text }: { text: string }) => <span>{text}</span>,
}));

jest.mock('../../Attachments', () => ({
  Attachments: () => null,
}));

jest.mock('../Ellipsis', () => ({
  Ellipsis: () => <span data-testid="ellipsis" />,
}));

jest.mock('../utils/TruncatedContent', () => ({
  TruncatedContent: ({ children }: { children: React.ReactNode }) => children,
}));

describe('FeedItemComment', () => {
  it('remeasures expandability when comment text changes', async () => {
    let commentHeight = 0;
    const offsetHeightMock = jest
      .spyOn(HTMLElement.prototype, 'offsetHeight', 'get')
      .mockImplementation(() => commentHeight);
    const props: IFeedItemCommentProps = {
      attachments: [],
      isTextExpanded: false,
      onExpand: jest.fn(),
      task: null,
      text: 'Short comment',
      type: EWorkflowLogEvent.TaskComment,
    };
    const { rerender } = render(<FeedItemComment {...props} />);

    await waitFor(() => expect(screen.queryByTestId('ellipsis')).not.toBeInTheDocument());

    commentHeight = 120;
    rerender(<FeedItemComment {...props} text="Updated long comment" />);

    await waitFor(() => expect(screen.getByTestId('ellipsis')).toBeInTheDocument());
    offsetHeightMock.mockRestore();
  });
});
