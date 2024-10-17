import { ERoutes } from "../constants/routes";
import { getBrowserConfigEnv } from "./getConfig";
import { getQueryStringByParams } from "./history";

export function getAbsolutePath<T extends string = ''>(route: ERoutes, queryParams?: { [key in T]: string }) {
  const { host } = getBrowserConfigEnv();
  
  const path = `${route}${queryParams ? getQueryStringByParams(queryParams) : ''}`

  return new URL(path, host).href;
}