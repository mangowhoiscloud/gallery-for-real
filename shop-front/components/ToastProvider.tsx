'use client';

import { createContext, useCallback, useContext, useState } from 'react';
import * as RadixToast from '@radix-ui/react-toast';
import { Toast } from './ui/Toast';

export type ToastVariant = 'success' | 'error' | 'info';

export interface ToastItem {
  id: string;
  variant: ToastVariant;
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
}

interface ToastContextValue {
  toasts: ToastItem[];
  toast: (options: Omit<ToastItem, 'id'>) => string;
  dismiss: (id: string) => void;
}

export const ToastContext = createContext<ToastContextValue>({
  toasts: [],
  toast: () => '',
  dismiss: () => {},
});

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const toast = useCallback((options: Omit<ToastItem, 'id'>): string => {
    const id = Math.random().toString(36).slice(2, 9);
    setToasts((prev) => [...prev, { ...options, id }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
    return id;
  }, []);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <RadixToast.Provider>
      <ToastContext.Provider value={{ toasts, toast, dismiss }}>
        {children}
        {toasts.map((t) => (
          <Toast key={t.id} item={t} onDismiss={dismiss} />
        ))}
        <RadixToast.Viewport className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 p-4 max-h-screen overflow-hidden" />
      </ToastContext.Provider>
    </RadixToast.Provider>
  );
}

export function useToast(): ToastContextValue {
  return useContext(ToastContext);
}
