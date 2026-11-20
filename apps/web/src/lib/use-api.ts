"use client";

import { useEffect, useRef, useState } from "react";

export type AsyncState<T> = {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => void;
};

/**
 * Small fetch hook. The key controls re-fetching; the loader may close over
 * component state without forcing the effect to depend on its identity.
 */
export function useApi<T>(key: string, loader: (signal: AbortSignal) => Promise<T>): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [nonce, setNonce] = useState(0);
  const loaderRef = useRef(loader);
  loaderRef.current = loader;

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    setLoading(true);
    setError(null);
    loaderRef
      .current(controller.signal)
      .then((value) => {
        if (!active) return;
        setData(value);
        setLoading(false);
      })
      .catch((reason: unknown) => {
        if (!active || controller.signal.aborted) return;
        setError(reason instanceof Error ? reason.message : "Request failed");
        setLoading(false);
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [key, nonce]);

  return {
    data,
    error,
    loading,
    reload: () => setNonce((value) => value + 1),
  };
}
