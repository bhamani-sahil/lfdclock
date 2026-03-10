import React from 'react';
import { cn } from '@/lib/utils';

export const TrafficLight = ({ status, size = 'md', showLabel = true, className }) => {
  const sizeClasses = {
    sm: 'w-2.5 h-2.5',
    md: 'w-3 h-3',
    lg: 'w-4 h-4'
  };

  const statusConfig = {
    safe: {
      color: 'bg-emerald-500',
      glowColor: 'text-emerald-500',
      label: 'Safe'
    },
    warning: {
      color: 'bg-amber-500',
      glowColor: 'text-amber-500',
      label: 'Warning'
    },
    critical: {
      color: 'bg-red-500',
      glowColor: 'text-red-500',
      label: 'Critical'
    },
    expired: {
      color: 'bg-slate-400',
      glowColor: 'text-slate-400',
      label: 'Expired'
    },
    unknown: {
      color: 'bg-slate-300',
      glowColor: 'text-slate-300',
      label: 'Unknown'
    }
  };

  const config = statusConfig[status] || statusConfig.unknown;

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span
        className={cn(
          'rounded-full traffic-light-pulse',
          sizeClasses[size],
          config.color,
          config.glowColor
        )}
        style={{
          boxShadow: status !== 'expired' && status !== 'unknown' 
            ? `0 0 8px currentColor` 
            : 'none'
        }}
      />
      {showLabel && (
        <span className="text-sm font-medium capitalize">{config.label}</span>
      )}
    </div>
  );
};

export const StatusBadge = ({ status, children, className }) => {
  const statusClasses = {
    safe: 'status-safe',
    warning: 'status-warning',
    critical: 'status-critical',
    expired: 'bg-slate-100 text-slate-600 border-slate-300',
    unknown: 'bg-slate-100 text-slate-500 border-slate-200'
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm text-xs font-medium border',
        statusClasses[status] || statusClasses.unknown,
        className
      )}
    >
      <TrafficLight status={status} size="sm" showLabel={false} />
      {children}
    </span>
  );
};
