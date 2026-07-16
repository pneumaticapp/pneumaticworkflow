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
    });

    expect(mockedCommonRequest).toHaveBeenCalledTimes(1);

    const [url, options] = mockedCommonRequest.mock.calls[0];
    expect(url).toBe('/workflows/comments/42');
    expect(options.method).toBe('PATCH');
  });

  it('sends only text in body', () => {
    editComment({
      id: 10,
      text: 'hello',
    });

    const [, options] = mockedCommonRequest.mock.calls[0];
    expect(options.data).toEqual({
      text: 'hello',
    });
  });

  it('sends null text', () => {
    editComment({
      id: 5,
      text: null,
    });

    const [, options] = mockedCommonRequest.mock.calls[0];
    expect(options.data.text).toBeNull();
  });

  it('uses shouldThrow option', () => {
    editComment({
      id: 1,
      text: 'test',
    });

    const [, , extra] = mockedCommonRequest.mock.calls[0];
    expect(extra).toEqual({ shouldThrow: true });
  });
});
