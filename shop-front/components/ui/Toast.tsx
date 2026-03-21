'use client';

import * as RadixToast from '@radix-ui/react-toast';
import type { ToastItem } from '@/components/ToastProvider';

const variantStyles: Record<string, string> = {
  success:
    'border-l-4 border-green-500 bg-green-50 text-green-900 dark:bg-green-950 dark:text-green-100',
  error:
    'border-l-4 border-red-500 bg-red-50 text-red-900 dark:bg-red-950 dark:text-red-100',
  info: 'border-l-4 border-blue-500 bg-blue-50 text-blue-900 dark:bg-blue-950 dark:text-blue-100',
};

interface ToastProps {
  item: ToastItem;
  onDismiss: (id: string) => void;
}

export function Toast({ item, onDismiss }: ToastProps) {
  return (
    <RadixToast.Root
      className={`flex items-start gap-3 rounded-lg p-4 shadow-lg min-w-[300px] max-w-sm ${variantStyles[item.variant]}`}
      defaultOpen
      onOpenChange={(open) => {
        if (!open) onDismiss(item.id);
      }}
    >
      <div className="flex-1 min-w-0">
        <RadixToast.Title className="font-semibold text-sm leading-snug">
          {item.title}
        </RadixToast.Title>
        {item.description && (
          <RadixToast.Description className="mt-1 text-xs opacity-80">
            {item.description}
          </RadixToast.Description>
        )}
      </div>
      {item.action && (
        <RadixToast.Action
          className="shrink-0 text-xs font-medium underline underline-offset-2 hover:no-underline"
          altText={item.action.label}
          onClick={item.action.onClick}
        >
          {item.action.label}
        </RadixToast.Action>
      )}
      <RadixToast.Close className="shrink-0 opacity-50 hover:opacity-100 transition-opacity text-lg leading-none">
        <span aria-hidden>×</span>
      </RadixToast.Close>
    </RadixToast.Root>
  );
}
