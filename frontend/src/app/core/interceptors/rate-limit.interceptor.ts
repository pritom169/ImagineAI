import { HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';

import { NotificationService } from '../services/notification.service';

export const rateLimitInterceptor: HttpInterceptorFn = (req, next) => {
  const notification = inject(NotificationService);

  return next(req).pipe(
    catchError((error) => {
      if (error.status === 429) {
        const retryAfter = error.headers?.get('Retry-After');
        const seconds = retryAfter ? parseInt(retryAfter, 10) : 60;
        notification.error(
          `Rate limit exceeded. Please try again in ${seconds} seconds.`
        );
      }
      return throwError(() => error);
    })
  );
};
