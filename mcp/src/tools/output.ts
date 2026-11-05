import type { ToolOutput } from '../mcp/result.js';
import type { PneumaticClient } from '../pneumatic/client.js';
import { loadPeople } from '../pneumatic/directory.js';
import { PneumaticPresenter, type Json } from '../presenters/index.js';

export function successOutput(): ToolOutput {
  return { data: { success: true } };
}

export async function present(
  client: PneumaticClient,
  render: (presenter: PneumaticPresenter) => Json,
  { shouldLoadPeople = false } = {},
): Promise<ToolOutput> {
  const presenter = new PneumaticPresenter({
    appUrl: client.appUrl,
    people: shouldLoadPeople ? await loadPeople(client).catch(() => undefined) : undefined,
  });
  return presenter.toOutput(render(presenter));
}
