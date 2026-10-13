// <reference types="jest" />
import { mcpContinuation, safeRedirect } from '../safeRedirect';

describe('safe login continuation', () => {
  const ID = '550e8400-e29b-41d4-a716-446655440000';
  it.each([
    'https://evil.example',
    '//evil.example',
    '/\\evil.example',
    '/%2f%2fevil.example',
    'javascript:alert(1)',
    '/tasks/%0aHeader:value',
    '/oauth/google/?redirectUri=https://evil.example',
    ['/', '/tasks/'],
    '',
    null,
    undefined,
    17,
  ])('test_safeRedirect__untrusted_value_%p__rejects', (value) => {
    // arrange
    const fileServiceUrl = 'https://my.pneumatic.app/files';

    // act
    const result = safeRedirect(value, fileServiceUrl);

    // assert
    expect(result).toBe('');
  });
  it('test_safeRedirect__task_route__preserves_query', () => {
    // arrange
    const target = '/tasks/123/?tab=files';

    // act
    const result = safeRedirect(target);

    // assert
    expect(result).toBe(target);
  });
  it('test_safeRedirect__configured_download__allows', () => {
    // arrange
    const target = 'https://my.pneumatic.app/files/abc-123';
    const fileServiceUrl = 'https://my.pneumatic.app/files';

    // act
    const result = safeRedirect(target, fileServiceUrl);

    // assert
    expect(result).toBe(target);
  });
  it('test_safeRedirect__download_origin_other_path__rejects', () => {
    // arrange
    const target = 'https://my.pneumatic.app/redirect?url=evil';
    const fileServiceUrl = 'https://my.pneumatic.app/files';

    // act
    const result = safeRedirect(target, fileServiceUrl);

    // assert
    expect(result).toBe('');
  });
  it('test_mcpContinuation__consent_step__preserves_target', () => {
    // arrange
    const target = `/mcp/connect?request_id=${ID}&step=consent`;

    // act
    const result = mcpContinuation(target);

    // assert
    expect(result).toBe(target);
  });
  it('test_safeRedirect__consent_step__preserves_target', () => {
    // arrange
    const target = `/mcp/connect?request_id=${ID}&step=consent`;

    // act
    const result = safeRedirect(target);

    // assert
    expect(result).toBe(target);
  });
  it.each(['step=evil', 'step=consent&step=consent', 'redirectUrl=https://evil.example', `request_id=${ID}`])(
    'test_mcpContinuation__extra_parameter_%s__rejects',
    (extra) => {
      // arrange
      const target = `/mcp/connect?request_id=${ID}&${extra}`;

      // act
      const result = mcpContinuation(target);

      // assert
      expect(result).toBe('');
    },
  );
  it('test_mcpContinuation__upload_traversal__rejects', () => {
    // arrange
    const target = `/mcp/uploads/${ID}/../connect`;

    // act
    const result = mcpContinuation(target);

    // assert
    expect(result).toBe('');
  });
});
