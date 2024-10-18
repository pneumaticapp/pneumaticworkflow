import * as NodeCache from 'node-cache';

export class CacheUtils {
  private cache: NodeCache;

  private readonly expires: number = 60 * 60 * 12;

  public constructor(expires: number = 0) {
    this.expires = expires;
    this.cache = new NodeCache({
      stdTTL: expires,
    });
  }

  public getData<T>(key: string) {
    return this.cache.get<T>(key);
  }

  public setData<T>(key: string, value: T) {
    this.cache.set<T>(key, value);
  }

  public clearData() {
    this.cache = new NodeCache({
      stdTTL: this.expires,
    });
  }
}
