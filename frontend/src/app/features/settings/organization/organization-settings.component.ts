import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { OrganizationService } from '../../../core/services/organization.service';
import { NotificationService } from '../../../core/services/notification.service';
import { OrganizationMember } from '../../../core/models/organization.model';

@Component({
  selector: 'app-organization-settings',
  standalone: true,
  imports: [
    CommonModule, FormsModule, MatCardModule, MatButtonModule, MatIconModule,
    MatInputModule, MatFormFieldModule, MatTableModule, MatChipsModule,
    MatSelectModule, MatProgressSpinnerModule,
  ],
  template: `
    <div class="page-container">
      <h1>Organization Settings</h1>

      @if (orgService.currentOrganization(); as org) {
        <mat-card class="org-card">
          <mat-card-header>
            <mat-card-title>{{ org.name }}</mat-card-title>
            <mat-card-subtitle>Slug: {{ org.slug }} | Plan: {{ org.plan }}</mat-card-subtitle>
          </mat-card-header>
        </mat-card>

        <h2>Members</h2>

        <mat-card class="invite-card">
          <mat-card-content>
            <div class="invite-form">
              <mat-form-field appearance="outline">
                <mat-label>Email</mat-label>
                <input matInput [(ngModel)]="inviteEmail" placeholder="user@example.com">
              </mat-form-field>
              <mat-form-field appearance="outline">
                <mat-label>Role</mat-label>
                <mat-select [(ngModel)]="inviteRole">
                  <mat-option value="member">Member</mat-option>
                  <mat-option value="admin">Admin</mat-option>
                  <mat-option value="viewer">Viewer</mat-option>
                </mat-select>
              </mat-form-field>
              <button mat-raised-button color="primary" (click)="inviteMember()">
                <mat-icon>person_add</mat-icon> Invite
              </button>
            </div>
          </mat-card-content>
        </mat-card>

        @if (loading()) {
          <div class="loading"><mat-spinner diameter="40"></mat-spinner></div>
        } @else {
          <div class="members-list">
            @for (member of members(); track member.id) {
              <mat-card class="member-card">
                <mat-card-content>
                  <div class="member-info">
                    <mat-icon>person</mat-icon>
                    <div>
                      <div class="member-email">{{ member.user_email || 'Unknown' }}</div>
                      <div class="member-name">{{ member.user_name || '' }}</div>
                    </div>
                  </div>
                  <div class="member-actions">
                    <span class="role-badge" [class]="'role-' + member.role">{{ member.role }}</span>
                    <button mat-icon-button color="warn" (click)="removeMember(member.id)">
                      <mat-icon>remove_circle</mat-icon>
                    </button>
                  </div>
                </mat-card-content>
              </mat-card>
            }
          </div>
        }

        <h2 style="margin-top: 32px;">Create New Organization</h2>
        <mat-card class="invite-card">
          <mat-card-content>
            <div class="invite-form">
              <mat-form-field appearance="outline">
                <mat-label>Name</mat-label>
                <input matInput [(ngModel)]="newOrgName">
              </mat-form-field>
              <mat-form-field appearance="outline">
                <mat-label>Slug</mat-label>
                <input matInput [(ngModel)]="newOrgSlug">
              </mat-form-field>
              <button mat-raised-button color="primary" (click)="createOrg()">
                <mat-icon>add</mat-icon> Create
              </button>
            </div>
          </mat-card-content>
        </mat-card>
      }
    </div>
  `,
  styles: [`
    .page-container { padding: 24px; }
    h1 { font-size: 24px; font-weight: 600; margin-bottom: 24px; }
    h2 { font-size: 18px; font-weight: 600; margin: 24px 0 12px; }
    .org-card { margin-bottom: 24px; border-radius: 12px; }
    .invite-card { margin-bottom: 16px; border-radius: 12px; }
    .invite-form { display: flex; gap: 12px; align-items: flex-start; flex-wrap: wrap; }
    .loading { display: flex; justify-content: center; padding: 24px; }
    .members-list { display: flex; flex-direction: column; gap: 8px; }
    .member-card { border-radius: 12px; }
    .member-card mat-card-content { display: flex; justify-content: space-between; align-items: center; }
    .member-info { display: flex; align-items: center; gap: 12px; }
    .member-email { font-weight: 500; }
    .member-name { color: #666; font-size: 13px; }
    .member-actions { display: flex; align-items: center; gap: 8px; }
    .role-badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
    .role-owner { background: #f3e5f5; color: #7b1fa2; }
    .role-admin { background: #e3f2fd; color: #1565c0; }
    .role-member { background: #e8f5e9; color: #2e7d32; }
    .role-viewer { background: #fff3e0; color: #ef6c00; }
  `],
})
export class OrganizationSettingsComponent implements OnInit {
  orgService = inject(OrganizationService);
  private notification = inject(NotificationService);

  members = signal<OrganizationMember[]>([]);
  loading = signal(true);
  inviteEmail = '';
  inviteRole = 'member';
  newOrgName = '';
  newOrgSlug = '';

  ngOnInit(): void {
    this.loadMembers();
  }

  loadMembers(): void {
    const org = this.orgService.currentOrganization();
    if (!org) return;
    this.orgService.getMembers(org.id).subscribe({
      next: (data) => { this.members.set(data); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  inviteMember(): void {
    const org = this.orgService.currentOrganization();
    if (!org || !this.inviteEmail) return;
    this.orgService.inviteMember(org.id, { email: this.inviteEmail, role: this.inviteRole }).subscribe({
      next: () => {
        this.notification.success('Member invited');
        this.inviteEmail = '';
        this.loadMembers();
      },
      error: () => this.notification.error('Failed to invite member'),
    });
  }

  removeMember(memberId: string): void {
    const org = this.orgService.currentOrganization();
    if (!org) return;
    this.orgService.removeMember(org.id, memberId).subscribe({
      next: () => { this.notification.success('Member removed'); this.loadMembers(); },
    });
  }

  createOrg(): void {
    if (!this.newOrgName || !this.newOrgSlug) return;
    this.orgService.createOrganization({ name: this.newOrgName, slug: this.newOrgSlug }).subscribe({
      next: () => {
        this.notification.success('Organization created');
        this.newOrgName = '';
        this.newOrgSlug = '';
      },
      error: () => this.notification.error('Failed to create organization'),
    });
  }
}
