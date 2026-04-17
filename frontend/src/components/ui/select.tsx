import React, { useState, useRef, useEffect } from 'react';

interface SelectContextType {
  value: string;
  setValue: (value: string) => void;
  open: boolean;
  setOpen: (open: boolean) => void;
  onValueChange?: (value: string) => void;
}

const SelectContext = React.createContext<SelectContextType | undefined>(undefined);

interface SelectProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
}

export const Select = React.forwardRef<HTMLDivElement, SelectProps>(
  ({ value: controlledValue, defaultValue = '', onValueChange, children, ...props }, ref) => {
    const [internalValue, setInternalValue] = useState(controlledValue || defaultValue);
    const [open, setOpen] = useState(false);

    const value = controlledValue !== undefined ? controlledValue : internalValue;

    const setValue = (newValue: string) => {
      if (controlledValue === undefined) {
        setInternalValue(newValue);
      }
      onValueChange?.(newValue);
      setOpen(false);
    };

    return (
      <SelectContext.Provider value={{ value, setValue, open, setOpen, onValueChange }}>
        <div ref={ref} {...props}>
          {children}
        </div>
      </SelectContext.Provider>
    );
  }
);
Select.displayName = 'Select';

function useSelectContext() {
  const context = React.useContext(SelectContext);
  if (!context) {
    throw new Error('useSelectContext must be used within a Select component');
  }
  return context;
}

export const SelectTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement>
>(({ className = '', children, ...props }, ref) => {
  const { open, setOpen } = useSelectContext();

  return (
    <button
      ref={ref}
      onClick={() => setOpen(!open)}
      className={`flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm placeholder-gray-400 shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      {...props}
    >
      {children}
      <svg
        className={`h-4 w-4 opacity-50 transition-transform ${open ? 'rotate-180' : ''}`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
      </svg>
    </button>
  );
});
SelectTrigger.displayName = 'SelectTrigger';

export const SelectValue = React.forwardRef<
  HTMLSpanElement,
  React.HTMLAttributes<HTMLSpanElement> & { placeholder?: string }
>(({ placeholder, className = '', ...props }, ref) => {
  const { value } = useSelectContext();

  return (
    <span ref={ref} className={className} {...props}>
      {value || placeholder || 'Select...'}
    </span>
  );
});
SelectValue.displayName = 'SelectValue';

export const SelectContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className = '', children, ...props }, ref) => {
  const { open } = useSelectContext();

  if (!open) return null;

  return (
    <div
      ref={ref}
      className={`absolute z-50 min-w-[8rem] overflow-hidden rounded-md border border-gray-200 bg-white shadow-md animate-in fade-in-0 zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
});
SelectContent.displayName = 'SelectContent';

interface SelectItemProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string;
}

export const SelectItem = React.forwardRef<HTMLDivElement, SelectItemProps>(
  ({ value, className = '', children, ...props }, ref) => {
    const { value: selectedValue, setValue } = useSelectContext();
    const isSelected = selectedValue === value;

    return (
      <div
        ref={ref}
        onClick={() => setValue(value)}
        className={`relative flex cursor-pointer select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-gray-100 focus:bg-gray-100 data-[disabled]:pointer-events-none data-[disabled]:opacity-50 ${
          isSelected ? 'bg-blue-50 text-blue-600' : ''
        } ${className}`}
        {...props}
      >
        {isSelected && (
          <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
            <svg fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </span>
        )}
        {children}
      </div>
    );
  }
);
SelectItem.displayName = 'SelectItem';
