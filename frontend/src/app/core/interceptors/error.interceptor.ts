import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { NotificationService } from '../services/notification.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const notification = inject(NotificationService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 0) {
        notification.error('Network error. Please check your connection.');
      } else if (error.status >= 500) {
        notification.error('Server error. Please try again later.');
      } else if (error.status === 422) {
        const detail = error.error?.detail;
        if (typeof detail === 'string') {
          notification.error(detail);
        }
      }
      return throwError(() => error);
    }),
  );
};
