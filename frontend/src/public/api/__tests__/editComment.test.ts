// <reference types="jest" />
import { editComment } from '../workflows/editComment';
import { commonRequest } from '../commonRequest';

jest.mock('../commonRequest', () => ({
  commonRequest: jest.fn(),
}));

jest.mock('../../utils/mappers', () => ({
  mapRequestBody: jest.fn((body) => body),
}));

jest.mock('../../utils/getConfig', () => ({
  getBrowserConfigEnv: () => ({
    api: {
      urls: {
        workflowCommentEdit: '/workflows/comments/:id',
      },
    },
  }),
}));

describe('editComment', () => {
  const mockedCommonRequest = commonRequest as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('sends PATCH to correct URL with comment id', () => {
    editComment({
      id: 42,
      text: 'updated text',
      attachments: null,
    });

    expect(mockedCommonRequest).toHaveBeenCalledTimes(1);

    const [url, options] = mockedCommonRequest.mock.calls[0];
    expect(url).toBe('/workflows/comments/42');
    expect(options.method).toBe('PATCH');
  });

  it('sends text and attachments in body', () => {
    const attachments = [{ id: 'file-abc' }, { id: 'file-xyz' }];

    editComment({
      id: 10,
      text: 'hello',
      attachments,
    });

    const [, options] = mockedCommonRequest.mock.calls[0];
    expect(options.data).toEqual({
      text: 'hello',
      attachments,
    });
  });

  it('sends attachments as {id} objects, not full TUploadedFile', () => {
    const attachments = [{ id: 'abc-123' }];

    editComment({
      id: 1,
      text: 'test',
      attachments,
    });

    const [, options] = mockedCommonRequest.mock.calls[0];
    expect(options.data.attachments).toEqual([{ id: 'abc-123' }]);
    expect(options.data.attachments[0]).not.toHaveProperty('url');
    expect(options.data.attachments[0]).not.toHaveProperty('name');
    expect(options.data.attachments[0]).not.toHaveProperty('size');
  });

  it('sends null attachments when no files', () => {
    editComment({
      id: 5,
      text: 'no files',
      attachments: null,
    });

    const [, options] = mockedCommonRequest.mock.calls[0];
    expect(options.data.attachments).toBeNull();
  });

  it('uses shouldThrow option', () => {
    editComment({
      id: 1,
      text: 'test',
      attachments: null,
    });

    const [, , extra] = mockedCommonRequest.mock.calls[0];
    expect(extra).toEqual({ shouldThrow: true });
  });
});
