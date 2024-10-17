import { getBrowserConfig } from "../utils/getConfig";

export function isTenant() {
  const {user: {account}} = getBrowserConfig();

  return account && account.leaseLevel === 'tenant';
}
