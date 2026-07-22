import { resolveNotificationUrl } from '../resolveNotificationUrl';

describe('resolveNotificationUrl', () => {
  const hostWithoutSlash = 'http://localhost';
  const hostWithSlash = 'http://localhost/';

  it('prefers backend-provided link', () => {
    expect(
      resolveNotificationUrl(
        {
          link: 'http://localhost/workflows/42',
          task_id: '1',
        },
        hostWithoutSlash,
      ),
    ).toBe('http://localhost/workflows/42');
  });

  it('builds task url when link is missing and host has no trailing slash', () => {
    expect(
      resolveNotificationUrl({ task_id: '123' }, hostWithoutSlash),
    ).toBe('http://localhost/tasks/123/');
  });

  it('builds task url when link is missing and host has trailing slash', () => {
    expect(
      resolveNotificationUrl({ task_id: '123' }, hostWithSlash),
    ).toBe('http://localhost/tasks/123/');
  });

  it('returns null when payload has neither link nor task_id', () => {
    expect(resolveNotificationUrl({}, hostWithoutSlash)).toBeNull();
  });

  it('returns null for empty payload', () => {
    expect(resolveNotificationUrl(null, hostWithoutSlash)).toBeNull();
    expect(resolveNotificationUrl(undefined, hostWithoutSlash)).toBeNull();
  });
});
