export interface INotificationPayloadData {
  link?: string;
  task_id?: string;
}

/**
 * Resolves the URL opened when a browser push notification is clicked.
 * Prefer the backend-provided `link`; fall back to a task URL built from host + task_id.
 * Keep in sync with firebase-messaging-sw.ejs.
 */
export function resolveNotificationUrl(
  data: INotificationPayloadData | null | undefined,
  host: string,
): string | null {
  if (!data) {
    return null;
  }

  if (data.link) {
    return data.link;
  }

  if (data.task_id) {
    const normalizedHost = host.replace(/\/$/, '');
    return `${normalizedHost}/tasks/${data.task_id}/`;
  }

  return null;
}
