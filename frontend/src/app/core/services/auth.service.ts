import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { TokenPair, User, UserCreate } from '../models/user.model';
import { OrganizationService } from './organization.service';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly apiUrl = environment.apiUrl;
  private readonly TOKEN_KEY = 'imagineai_access_token';
  private readonly REFRESH_KEY = 'imagineai_refresh_token';
  private readonly orgService = inject(OrganizationService);

  private currentUser = signal<User | null>(null);
  readonly user = this.currentUser.asReadonly();
  readonly isAuthenticated = computed(() => !!this.currentUser());

  constructor(
    private http: HttpClient,
    private router: Router,
  ) {
    if (this.getToken()) {
      this.loadUser();
    }
  }

  register(data: UserCreate): Observable<User> {
    return this.http.post<User>(`${this.apiUrl}/auth/register`, data);
  }

  login(email: string, password: string): Observable<TokenPair> {
    return this.http
      .post<TokenPair>(`${this.apiUrl}/auth/login`, { email, password })
      .pipe(
        tap((tokens) => {
          this.storeTokens(tokens);
          this.loadUser();
        }),
      );
  }

  refreshToken(): Observable<TokenPair> {
    const refreshToken = localStorage.getItem(this.REFRESH_KEY);
    return this.http
      .post<TokenPair>(`${this.apiUrl}/auth/refresh`, {
        refresh_token: refreshToken,
      })
      .pipe(tap((tokens) => this.storeTokens(tokens)));
  }

  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
    localStorage.removeItem('imagineai_org_id');
    this.currentUser.set(null);
    this.router.navigate(['/auth/login']);
  }

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  private storeTokens(tokens: TokenPair): void {
    localStorage.setItem(this.TOKEN_KEY, tokens.access_token);
    localStorage.setItem(this.REFRESH_KEY, tokens.refresh_token);
  }

  private loadUser(): void {
    this.http.get<User>(`${this.apiUrl}/auth/me`).subscribe({
      next: (user) => {
        this.currentUser.set(user);
        this.orgService.loadOrganizations().subscribe();
      },
      error: () => this.logout(),
    });
  }
}
