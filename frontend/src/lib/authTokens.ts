/**
 * Pont entre SessionContext et api() pour Bearer JWT + refresh,
 * sans importer React dans http.ts.
 */

export type AuthBundle = {
  apiToken: string | null;
  accessToken: string | null;
  refreshToken: string | null;
};

type Listener = (next: AuthBundle) => void;

let bundle: AuthBundle = {
  apiToken: null,
  accessToken: null,
  refreshToken: null,
};
let listener: Listener | null = null;

export function getAuthBundle(): AuthBundle {
  return bundle;
}

export function setAuthBundle(next: AuthBundle) {
  bundle = next;
}

export function onAuthBundleChange(cb: Listener | null) {
  listener = cb;
}

export function notifyAuthBundleChange(next: AuthBundle) {
  bundle = next;
  listener?.(next);
}
