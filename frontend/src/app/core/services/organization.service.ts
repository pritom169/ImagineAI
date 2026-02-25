import { HttpClient } from '@angular/common/http';
import { Injectable, computed, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Organization, OrganizationCreate, OrganizationMember, InviteMemberRequest } from '../models/organization.model';

@Injectable({ providedIn: 'root' })
export class OrganizationService {
  private apiUrl = `${environment.apiUrl}/organizations`;

  currentOrganization = signal<Organization | null>(null);
  organizations = signal<Organization[]>([]);

  constructor(private http: HttpClient) {}

  loadOrganizations(): Observable<Organization[]> {
    return this.http.get<Organization[]>(this.apiUrl).pipe(
      tap((orgs) => {
        this.organizations.set(orgs);
        if (!this.currentOrganization() && orgs.length > 0) {
          this.selectOrganization(orgs[0]);
        }
      })
    );
  }

  selectOrganization(org: Organization): void {
    this.currentOrganization.set(org);
    localStorage.setItem('imagineai_org_id', org.id);
  }

  getSavedOrgId(): string | null {
    return localStorage.getItem('imagineai_org_id');
  }

  createOrganization(data: OrganizationCreate): Observable<Organization> {
    return this.http.post<Organization>(this.apiUrl, data).pipe(
      tap(() => this.loadOrganizations().subscribe())
    );
  }

  getMembers(orgId: string): Observable<OrganizationMember[]> {
    return this.http.get<OrganizationMember[]>(`${this.apiUrl}/${orgId}/members`);
  }

  inviteMember(orgId: string, data: InviteMemberRequest): Observable<OrganizationMember> {
    return this.http.post<OrganizationMember>(`${this.apiUrl}/${orgId}/members`, data);
  }

  removeMember(orgId: string, memberId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${orgId}/members/${memberId}`);
  }

  updateMemberRole(orgId: string, memberId: string, role: string): Observable<OrganizationMember> {
    return this.http.patch<OrganizationMember>(
      `${this.apiUrl}/${orgId}/members/${memberId}`, { role }
    );
  }
}
