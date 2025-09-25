/* eslint-disable prefer-destructuring */
/* eslint-disable consistent-return */
import { Router, Request, Response, NextFunction } from 'express';

type TSubdomainHosts = string[];

export function forwardForSubdomain(subdomainHosts: TSubdomainHosts, customRouter: Router) {
  return (req: Request, res: Response, next: NextFunction) => {
    let host = req.headers.host ? req.headers.host : '';
    host = host.split(':')[0];

    const isSubdomain = (host && subdomainHosts.includes(host));
    
    console.log('forwardForSubdomain debug:', {
      originalHost: req.headers.host,
      cleanHost: host,
      subdomainHosts,
      isSubdomain,
      path: req.path
    });
    
    if (isSubdomain) {
      return customRouter(req, res, next);
    }

    next();
  };
}
