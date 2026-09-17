"use client";

import { useEffect } from 'react';

export function useScrollRestoration(storageKey: string, dependencies: any[]) {
  useEffect(() => {
    if (typeof window !== 'undefined' && 'scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }

    let timeoutId: NodeJS.Timeout;
    const handleScroll = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        if (window.scrollY > 0) {
          sessionStorage.setItem(storageKey, window.scrollY.toString());
        }
      }, 100);
    };
    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
      clearTimeout(timeoutId);
      sessionStorage.removeItem(storageKey); // Sadece sayfa değiştiğinde (unmount) temizle, F5'te temizlenmez
    };
  }, [storageKey]);

  useEffect(() => {
    // Only attempt restoration if the main dependencies (like data array length) suggest the page is loaded
    const isLoaded = dependencies.every(dep => {
        if (typeof dep === 'boolean') return !dep; // e.g. !loading
        if (typeof dep === 'number') return dep > 0; // e.g. items.length > 0
        return true;
    });

    if (isLoaded) {
      const savedPos = sessionStorage.getItem(storageKey);
      if (savedPos) {
        const pos = parseInt(savedPos);
        if (pos > 0) {
          setTimeout(() => window.scrollTo({ top: pos, behavior: 'instant' }), 10);
          setTimeout(() => window.scrollTo({ top: pos, behavior: 'instant' }), 100);
          setTimeout(() => window.scrollTo({ top: pos, behavior: 'instant' }), 500);
        }
      }
    }
  }, dependencies);
}
