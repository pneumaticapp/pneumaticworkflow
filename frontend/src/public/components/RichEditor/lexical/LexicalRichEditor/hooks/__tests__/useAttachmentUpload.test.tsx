import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { MutableRefObject } from 'react';
import type { LexicalEditor } from 'lexical';
import { useAttachmentUpload } from '../useAttachmentUpload';
import { INSERT_ATTACHMENT_COMMAND } from '../../../plugins';

jest.mock('../../../../../../utils/uploadFiles', () => ({
  uploadFiles: jest.fn(),
}));
jest.mock('../../../../../Attachments/utils/getAttachmentType', () => ({
  getAttachmentTypeByUrl: jest.fn(),
}));
jest.mock('../../../../../UI/Notifications', () => ({
  NotificationManager: { warning: jest.fn() },
}));

const uploadFiles = require('../../../../../../utils/uploadFiles').uploadFiles as jest.Mock;
const getAttachmentTypeByUrl =
  require('../../../../../Attachments/utils/getAttachmentType').getAttachmentTypeByUrl as jest.Mock;
const NotificationManager = require('../../../../../UI/Notifications').NotificationManager;

function TestWrapper({
  editorRef,
  accountId,
  handlerRef,
}: {
  editorRef: MutableRefObject<LexicalEditor | null>;
  accountId: number | undefined;
  handlerRef?: React.MutableRefObject<((e: React.ChangeEvent<HTMLInputElement>) => Promise<void>) | null>;
}) {
  const handleUpload = useAttachmentUpload(editorRef, accountId);
  if (handlerRef) handlerRef.current = handleUpload;
  return (
    <input
      data-testid="file-input"
      type="file"
      multiple
      onChange={handleUpload}
    />
  );
}

describe('useAttachmentUpload', () => {
  let editorRef: MutableRefObject<LexicalEditor | null>;
  const dispatchCommand = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    editorRef = { current: { dispatchCommand } as unknown as LexicalEditor };
    getAttachmentTypeByUrl.mockReturnValue('file');
  });

  describe('successful upload', () => {
    it('calls uploadFiles with files array and accountId', async () => {
      uploadFiles.mockResolvedValue([{ url: 'https://cdn.example.com/a.pdf', id: 1, name: 'a.pdf' }]);
      render(<TestWrapper editorRef={editorRef} accountId={42} />);
      const input = screen.getByTestId('file-input');
      const file = new File(['content'], 'doc.pdf', { type: 'application/pdf' });
      await userEvent.upload(input, file);
      expect(uploadFiles).toHaveBeenCalledWith([file], 42);
    });

    it('dispatches INSERT_ATTACHMENT_COMMAND for each uploaded file with url', async () => {
      uploadFiles.mockResolvedValue([
        { url: 'https://a.com/1.pdf', id: 1, name: '1.pdf' },
        { url: 'https://a.com/2.jpg', id: 2, name: '2.jpg' },
      ]);
      getAttachmentTypeByUrl.mockImplementation((url: string) =>
        url.endsWith('.jpg') ? 'image' : 'file',
      );
      render(<TestWrapper editorRef={editorRef} accountId={1} />);
      const input = screen.getByTestId('file-input');
      await userEvent.upload(input, [new File([''], '1.pdf'), new File([''], '2.jpg')]);
      expect(dispatchCommand).toHaveBeenCalledTimes(2);
      expect(dispatchCommand).toHaveBeenNthCalledWith(1, INSERT_ATTACHMENT_COMMAND, {
        id: 1,
        url: 'https://a.com/1.pdf',
        name: '1.pdf',
        type: 'file',
      });
      expect(dispatchCommand).toHaveBeenNthCalledWith(2, INSERT_ATTACHMENT_COMMAND, {
        id: 2,
        url: 'https://a.com/2.jpg',
        name: '2.jpg',
        type: 'image',
      });
    });

    it('uses type from getAttachmentTypeByUrl or file as default', async () => {
      uploadFiles.mockResolvedValue([{ url: 'https://x.com/v.mp4', id: 1, name: 'v.mp4' }]);
      getAttachmentTypeByUrl.mockReturnValue('video');
      render(<TestWrapper editorRef={editorRef} accountId={1} />);
      const input = screen.getByTestId('file-input');
      await userEvent.upload(input, new File([''], 'v.mp4'));
      expect(dispatchCommand).toHaveBeenCalledWith(
        INSERT_ATTACHMENT_COMMAND,
        expect.objectContaining({ type: 'video' }),
      );
    });

    it('does not dispatch for items without url', async () => {
      uploadFiles.mockResolvedValue([
        { id: 1, name: 'no-url.pdf' },
        { url: 'https://a.com/yes.pdf', id: 2, name: 'yes.pdf' },
      ]);
      render(<TestWrapper editorRef={editorRef} accountId={1} />);
      const input = screen.getByTestId('file-input');
      await userEvent.upload(input, new File([''], 'a.pdf'));
      expect(dispatchCommand).toHaveBeenCalledTimes(1);
      expect(dispatchCommand).toHaveBeenCalledWith(
        INSERT_ATTACHMENT_COMMAND,
        expect.objectContaining({ url: 'https://a.com/yes.pdf' }),
      );
    });

    it('clears input value after handling (finally)', async () => {
      uploadFiles.mockResolvedValue([]);
      render(<TestWrapper editorRef={editorRef} accountId={1} />);
      const input = screen.getByTestId('file-input') as HTMLInputElement;
      await userEvent.upload(input, new File([''], 'x.pdf'));
      expect(input.value).toBe('');
    });
  });

  describe('early return', () => {
    it('does not call uploadFiles when files is empty', async () => {
      const handlerRef: React.MutableRefObject<((e: React.ChangeEvent<HTMLInputElement>) => Promise<void>) | null> =
        { current: null };
      render(<TestWrapper editorRef={editorRef} accountId={1} handlerRef={handlerRef} />);
      const syntheticEvent = {
        target: { files: [], value: 'x' },
      } as unknown as React.ChangeEvent<HTMLInputElement>;
      await handlerRef.current?.(syntheticEvent);
      expect(uploadFiles).not.toHaveBeenCalled();
    });

    it('does not call uploadFiles when accountId is undefined', async () => {
      render(<TestWrapper editorRef={editorRef} accountId={undefined} />);
      const input = screen.getByTestId('file-input');
      await userEvent.upload(input, new File([''], 'x.pdf'));
      expect(uploadFiles).not.toHaveBeenCalled();
    });

    it('does not call uploadFiles when accountId is null', async () => {
      render(<TestWrapper editorRef={editorRef} accountId={null as unknown as number | undefined} />);
      const input = screen.getByTestId('file-input');
      await userEvent.upload(input, new File([''], 'x.pdf'));
      expect(uploadFiles).not.toHaveBeenCalled();
    });

    it('does not call uploadFiles when editorRef.current is missing', async () => {
      editorRef.current = null;
      render(<TestWrapper editorRef={editorRef} accountId={1} />);
      const input = screen.getByTestId('file-input');
      await userEvent.upload(input, new File([''], 'x.pdf'));
      expect(uploadFiles).not.toHaveBeenCalled();
    });
  });

  describe('error handling', () => {
    it('calls NotificationManager.warning on uploadFiles error', async () => {
      uploadFiles.mockRejectedValue(new Error('Network error'));
      render(<TestWrapper editorRef={editorRef} accountId={1} />);
      const input = screen.getByTestId('file-input');
      await userEvent.upload(input, new File([''], 'x.pdf'));
      expect(NotificationManager.warning).toHaveBeenCalledWith({
        message: 'workflows.tasks-failed-to-upload-files',
      });
    });

    it('still clears value on error (finally)', async () => {
      uploadFiles.mockRejectedValue(new Error('Fail'));
      render(<TestWrapper editorRef={editorRef} accountId={1} />);
      const input = screen.getByTestId('file-input') as HTMLInputElement;
      await userEvent.upload(input, new File([''], 'x.pdf'));
      expect(input.value).toBe('');
    });
  });
});
