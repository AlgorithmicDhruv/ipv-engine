import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';

interface IPVResult {
  result_id: number;
  valuation_id: number;
  trader_price: number;
  independent_price: number;
  variance_abs: number;
  variance_pct: number;
  breach_flag: boolean;
  threshold_pct: number;
  reconciled_at: string;
  reviewed_by: string | null;
}

interface BreachSummary {
  total_breaches: number;
  breaches: IPVResult[];
}

@Component({
  selector: 'app-ipv-dashboard',
  standalone: true,
  imports: [CommonModule, HttpClientModule],
  template: `
    <div class="dashboard">
      <header class="dashboard-header">
        <h1>IPV Dashboard — Valuation Control</h1>
        <div class="header-meta">
          <span class="breach-count" [class.has-breaches]="breachSummary?.total_breaches > 0">
            {{ breachSummary?.total_breaches ?? 0 }} Active Breaches
          </span>
          <button class="btn-refresh" (click)="loadData()">Refresh</button>
          <button class="btn-reconcile" (click)="reconcilePending()">Reconcile Pending</button>
        </div>
      </header>

      <section class="results-grid">
        <h2>Reconciliation Results</h2>

        <div class="loading" *ngIf="loading">Loading...</div>
        <div class="error-msg" *ngIf="error">{{ error }}</div>

        <table *ngIf="!loading && !error">
          <thead>
            <tr>
              <th>Result ID</th>
              <th>Valuation ID</th>
              <th>Trader Price</th>
              <th>Market Price</th>
              <th>Variance (Abs)</th>
              <th>Variance (%)</th>
              <th>Threshold (%)</th>
              <th>Status</th>
              <th>Reconciled At</th>
            </tr>
          </thead>
          <tbody>
            <tr
              *ngFor="let row of results"
              [class.row-breach]="row.breach_flag"
              [class.row-clean]="!row.breach_flag"
            >
              <td>{{ row.result_id }}</td>
              <td>{{ row.valuation_id }}</td>
              <td>{{ row.trader_price | number:'1.4-4' }}</td>
              <td>{{ row.independent_price | number:'1.4-4' }}</td>
              <td>{{ row.variance_abs | number:'1.4-4' }}</td>
              <td [class.variance-high]="row.breach_flag">
                {{ row.variance_pct | number:'1.4-4' }}%
              </td>
              <td>{{ row.threshold_pct | number:'1.2-2' }}%</td>
              <td>
                <span class="badge" [class.badge-breach]="row.breach_flag" [class.badge-ok]="!row.breach_flag">
                  {{ row.breach_flag ? 'BREACH' : 'VERIFIED' }}
                </span>
              </td>
              <td>{{ row.reconciled_at | date:'yyyy-MM-dd HH:mm' }}</td>
            </tr>
          </tbody>
        </table>

        <div *ngIf="!loading && results.length === 0 && !error" class="empty-state">
          No reconciliation results yet. Submit a valuation to begin.
        </div>
      </section>
    </div>
  `,
  styles: [`
    .dashboard {
      font-family: 'Segoe UI', sans-serif;
      padding: 24px;
      background: #f5f5f5;
      min-height: 100vh;
    }
    .dashboard-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
    }
    h1 { font-size: 20px; font-weight: 600; color: #1a1a2e; }
    h2 { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
    .header-meta { display: flex; align-items: center; gap: 12px; }
    .breach-count { font-size: 14px; font-weight: 600; color: #666; }
    .breach-count.has-breaches { color: #c0392b; }
    button { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }
    .btn-refresh { background: #2c3e50; color: #fff; }
    .btn-reconcile { background: #1a5276; color: #fff; }
    .results-grid { background: #fff; padding: 20px; border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th { text-align: left; padding: 10px 12px; background: #2c3e50; color: #fff; font-weight: 500; }
    td { padding: 9px 12px; border-bottom: 1px solid #eee; }
    .row-breach { background: #fdf2f2; }
    .row-clean { background: #fff; }
    .variance-high { color: #c0392b; font-weight: 600; }
    .badge { padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: 700; }
    .badge-breach { background: #f9ebea; color: #c0392b; }
    .badge-ok { background: #eafaf1; color: #1e8449; }
    .loading { color: #666; padding: 16px 0; }
    .error-msg { color: #c0392b; padding: 16px 0; }
    .empty-state { color: #999; padding: 24px 0; text-align: center; }
  `]
})
export class IPVDashboardComponent implements OnInit {
  results: IPVResult[] = [];
  breachSummary: BreachSummary | null = null;
  loading = false;
  error: string | null = null;

  private readonly API_BASE = 'http://localhost:5000/api/v1';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading = true;
    this.error = null;

    this.http.get<IPVResult[]>(`${this.API_BASE}/ipv/results`).subscribe({
      next: (data) => {
        this.results = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load IPV results. Is the backend running?';
        this.loading = false;
      }
    });

    this.http.get<BreachSummary>(`${this.API_BASE}/ipv/breaches`).subscribe({
      next: (data) => { this.breachSummary = data; },
      error: () => {}
    });
  }

  reconcilePending(): void {
    this.http.post(`${this.API_BASE}/ipv/reconcile/pending`, {}).subscribe({
      next: () => this.loadData(),
      error: () => { this.error = 'Reconciliation request failed.'; }
    });
  }
}
