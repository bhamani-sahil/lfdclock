import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';

export const CountdownTimer = ({ targetDate, className }) => {
  const [timeLeft, setTimeLeft] = useState(calculateTimeLeft());

  function calculateTimeLeft() {
    const now = new Date();
    const target = new Date(targetDate);
    const diff = target - now;

    if (diff <= 0) {
      return { days: 0, hours: 0, minutes: 0, seconds: 0, expired: true };
    }

    return {
      days: Math.floor(diff / (1000 * 60 * 60 * 24)),
      hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
      minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
      seconds: Math.floor((diff % (1000 * 60)) / 1000),
      expired: false
    };
  }

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft(calculateTimeLeft());
    }, 1000);

    return () => clearInterval(timer);
  }, [targetDate]);

  if (timeLeft.expired) {
    return (
      <div className={cn('font-mono text-red-600 font-bold', className)}>
        EXPIRED
      </div>
    );
  }

  const totalHours = timeLeft.days * 24 + timeLeft.hours;
  const isWarning = totalHours < 48 && totalHours >= 24;
  const isCritical = totalHours < 24;

  return (
    <div className={cn('font-mono tabular-nums', className)}>
      <div className={cn(
        'flex items-baseline gap-1',
        isCritical && 'text-red-600',
        isWarning && !isCritical && 'text-amber-600'
      )}>
        {timeLeft.days > 0 && (
          <>
            <span className="text-xl font-bold">{timeLeft.days}</span>
            <span className="text-xs text-muted-foreground mr-2">d</span>
          </>
        )}
        <span className="text-xl font-bold">
          {String(timeLeft.hours).padStart(2, '0')}
        </span>
        <span className="text-xs text-muted-foreground">h</span>
        <span className="text-xl font-bold">
          {String(timeLeft.minutes).padStart(2, '0')}
        </span>
        <span className="text-xs text-muted-foreground">m</span>
        <span className="text-xl font-bold">
          {String(timeLeft.seconds).padStart(2, '0')}
        </span>
        <span className="text-xs text-muted-foreground">s</span>
      </div>
    </div>
  );
};

export const CompactCountdown = ({ hoursRemaining, className }) => {
  const days = Math.floor(hoursRemaining / 24);
  const hours = Math.round(hoursRemaining % 24);

  const isCritical = hoursRemaining < 24;
  const isWarning = hoursRemaining < 48 && !isCritical;

  if (hoursRemaining <= 0) {
    return <span className={cn('font-mono text-red-600 font-bold', className)}>EXPIRED</span>;
  }

  return (
    <span className={cn(
      'font-mono font-medium',
      isCritical && 'text-red-600',
      isWarning && 'text-amber-600',
      className
    )}>
      {days > 0 ? `${days}d ${hours}h` : `${Math.round(hoursRemaining)}h`}
    </span>
  );
};
