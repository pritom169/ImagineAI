import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { RouterModule, Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthService } from '../../../core/services/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, RouterModule, MatCardModule,
    MatFormFieldModule, MatInputModule, MatButtonModule, MatIconModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <div class="auth-container">
      <mat-card class="auth-card">
        <div class="auth-header">
          <mat-icon class="auth-logo">auto_awesome</mat-icon>
          <h1>ImagineAI</h1>
          <p>Sign in to your account</p>
        </div>

        <form [formGroup]="form" (ngSubmit)="onSubmit()">
          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Email</mat-label>
            <input matInput formControlName="email" type="email" placeholder="you&#64;example.com">
            @if (form.get('email')?.hasError('required') && form.get('email')?.touched) {
              <mat-error>Email is required</mat-error>
            }
            @if (form.get('email')?.hasError('email') && form.get('email')?.touched) {
              <mat-error>Invalid email format</mat-error>
            }
          </mat-form-field>

          <mat-form-field appearance="outline" class="full-width">
            <mat-label>Password</mat-label>
            <input matInput formControlName="password" [type]="hidePassword ? 'password' : 'text'">
            <button mat-icon-button matSuffix type="button" (click)="hidePassword = !hidePassword">
              <mat-icon>{{ hidePassword ? 'visibility_off' : 'visibility' }}</mat-icon>
            </button>
            @if (form.get('password')?.hasError('required') && form.get('password')?.touched) {
              <mat-error>Password is required</mat-error>
            }
          </mat-form-field>

          <button mat-raised-button color="primary" type="submit"
                  class="full-width submit-btn" [disabled]="loading || form.invalid">
            @if (loading) {
              <mat-spinner diameter="20"></mat-spinner>
            } @else {
              Sign In
            }
          </button>
        </form>

        <div class="auth-footer">
          Don't have an account? <a routerLink="/auth/register">Sign up</a>
        </div>
      </mat-card>
    </div>
  `,
  styles: [`
    .auth-container {
      display: flex; justify-content: center; align-items: center;
      min-height: 100vh; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    .auth-card { width: 420px; padding: 40px; border-radius: 16px; }
    .auth-header { text-align: center; margin-bottom: 32px; }
    .auth-logo { font-size: 40px; width: 40px; height: 40px; color: #3f51b5; margin-bottom: 12px; }
    .auth-header h1 { font-size: 24px; font-weight: 700; margin: 8px 0; }
    .auth-header p { color: #666; font-size: 14px; }
    .full-width { width: 100%; }
    .submit-btn { height: 48px; font-size: 16px; margin-top: 8px; }
    .auth-footer { text-align: center; margin-top: 24px; font-size: 14px; color: #666; }
    .auth-footer a { color: #3f51b5; text-decoration: none; font-weight: 500; }
  `],
})
export class LoginComponent {
  form: FormGroup;
  loading = false;
  hidePassword = true;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private notification: NotificationService,
    private router: Router,
  ) {
    this.form = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required],
    });
  }

  onSubmit(): void {
    if (this.form.invalid) return;
    this.loading = true;
    const { email, password } = this.form.value;

    this.authService.login(email, password).subscribe({
      next: () => {
        this.notification.success('Welcome back!');
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading = false;
        this.notification.error(err.error?.detail || 'Login failed');
      },
    });
  }
}
