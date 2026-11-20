import { isRecord } from '../core/json.js';
import type { PneumaticClient } from '../pneumatic/client.js';
import { forgetPeople } from '../pneumatic/directory.js';
import { present } from './output.js';

export function workflowDetail(client: PneumaticClient, raw: unknown) {
  return present(client, (presenter) => presenter.workflow(raw, { isDetailed: true }), { shouldLoadPeople: true });
}

export function taskDetail(client: PneumaticClient, raw: unknown) {
  return present(client, (presenter) => presenter.taskDetail(raw), { shouldLoadPeople: true });
}

export function templateDetail(client: PneumaticClient, raw: unknown) {
  return present(client, (presenter) => presenter.templateDetail(raw));
}

export function datasetDetail(client: PneumaticClient, raw: unknown) {
  return present(client, (presenter) => ({
    ...presenter.pick(raw, ['id', 'name', 'description']),
    items: presenter.objects(
      isRecord(raw) ? raw.items : undefined,
      (item) => presenter.pick(item, ['id', 'value']),
      1000,
    ),
  }));
}

// Users and groups are presented after a change, so cached names may be stale.
export function userDetail(client: PneumaticClient, raw: unknown) {
  forgetPeople(client);
  return present(client, (presenter) => presenter.user(raw, { isDetailed: true }));
}

export function groupDetail(client: PneumaticClient, raw: unknown) {
  forgetPeople(client);
  return present(client, (presenter) => presenter.group(raw));
}
