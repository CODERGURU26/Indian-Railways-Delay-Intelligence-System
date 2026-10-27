import { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const API_URL = (import.meta as ImportMeta & { env?: { VITE_API_BASE_URL?: string } }).env?.VITE_API_BASE_URL || 'http://localhost:8000';

type SummaryRow = {
  label: string;
  value: number | null;
  departure_value?: number | null;
  count?: number;
};

type AnalyticsPayload = {
  trains: SummaryRow[];
  stations: SummaryRow[];
  categories: SummaryRow[];
  monthly_trends: SummaryRow[];
  statuses: SummaryRow[];
  routes: SummaryRow[];
  coverage: Record<string, number>;
  totals: {
    records: number;
    trains: number;
    stations: number;
    journeys: number;
  };
  data_source: string;
};

export default function App() {
  const [data, setData] = useState<AnalyticsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const response = await fetch(`${API_URL}/summary`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const payload = await response.json();
        setData(payload);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load dashboard data');
      }
    };

    fetchSummary();
  }, []);

  if (error) {
    return <div className="error">Unable to fetch analytics: {error}</div>;
  }

  if (!data) {
    return <div className="loading">Loading railway delay metrics...</div>;
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Indian Railways Delay Intelligence</h1>
        <p>Station-level delay and route quality monitoring.</p>
        <p className="data-source">Data source: {data.data_source}</p>
      </header>

      <section className="stats-grid">
        <div className="card">
          <span>Stop records</span>
          <strong>{data.totals.records.toLocaleString()}</strong>
        </div>
        <div className="card">
          <span>Unique trains</span>
          <strong>{data.totals.trains.toLocaleString()}</strong>
        </div>
        <div className="card">
          <span>Unique stations</span>
          <strong>{data.totals.stations.toLocaleString()}</strong>
        </div>
        <div className="card">
          <span>Train journeys</span>
          <strong>{data.totals.journeys.toLocaleString()}</strong>
        </div>
        <div className="card">
          <span>Reported arrival coverage</span>
          <strong>{data.coverage.reported ?? 0}%</strong>
        </div>
        <div className="card">
          <span>Reported departure coverage</span>
          <strong>{data.coverage.departure_reported_pct ?? 0}%</strong>
        </div>
        <div className="card">
          <span>Run quality avg</span>
          <strong>{data.coverage.run_quality_avg ?? 0}</strong>
        </div>
      </section>

      <section className="charts-grid">
        <div className="panel chart-panel">
          <h2>Top 10 train delays</h2>
          <p className="chart-caption">
            Average arrival delay · showing {Math.min(data.trains.length, 10)} unique trains
            {data.trains.length < 8 ? ' · import more data to reach 8 trains' : ''}
          </p>
          <ResponsiveContainer width="100%" height={Math.max(340, data.trains.length * 38)}>
            <BarChart data={data.trains.slice(0, 10)} layout="vertical" margin={{ left: 12, right: 24 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" unit=" min" />
              <YAxis type="category" dataKey="label" width={76} />
              <Tooltip formatter={(value) => [`${value} min`, 'Average arrival delay']} />
              <Bar dataKey="value" fill="#ef4444" barSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel chart-panel">
          <h2>Top 10 station delays</h2>
          <p className="chart-caption">
            Average arrival and departure delay · showing {Math.min(data.stations.length, 10)} unique stations
            {data.stations.length < 8 ? ' · import more data to reach 8 stations' : ''}
          </p>
          <ResponsiveContainer width="100%" height={Math.max(340, data.stations.length * 38)}>
            <BarChart data={data.stations.slice(0, 10)} layout="vertical" margin={{ left: 12, right: 24 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" unit=" min" />
              <YAxis type="category" dataKey="label" width={76} />
              <Tooltip formatter={(value) => [`${value ?? 'N/A'} min`]} />
              <Bar dataKey="value" name="Arrival" fill="#3b82f6" barSize={16} />
              <Bar dataKey="departure_value" name="Departure" fill="#22c55e" barSize={16} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel chart-panel chart-panel-wide">
          <h2>Monthly delay trend</h2>
          <p className="chart-caption">Average station arrival and departure delay by journey start month</p>
          <ResponsiveContainer width="100%" height={380}>
            <LineChart data={data.monthly_trends} margin={{ top: 12, right: 24, bottom: 8, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis unit=" min" />
              <Tooltip formatter={(value) => [`${value ?? 'N/A'} min`]} />
              <Line type="monotone" dataKey="value" name="Arrival" stroke="#f97316" strokeWidth={3} />
              <Line type="monotone" dataKey="departure_value" name="Departure" stroke="#14b8a6" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="panel chart-panel">
          <h2>Category delay averages</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.categories}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis unit=" min" />
              <Tooltip />
              <Bar dataKey="value" name="Arrival" fill="#a78bfa" />
              <Bar dataKey="departure_value" name="Departure" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>

      </section>

      <section className="list-grid">
        <div className="panel">
          <h2>Service status (journeys)</h2>
          <ul>
            {data.statuses.map((item) => (
              <li key={item.label}>
                <span>{item.label}</span><strong>{item.count?.toLocaleString()}</strong>
              </li>
            ))}
          </ul>
        </div>

        <div className="panel">
          <h2>Routes with highest average delay</h2>
          <ul>
            {data.routes.map((item) => (
              <li key={item.label}>
                <span>{item.label} · {item.count} journeys</span>
                <strong>{item.value ?? 'N/A'} min</strong>
              </li>
            ))}
          </ul>
        </div>

        <div className="panel">
          <h2>Reporting coverage</h2>
          <ul>
            <li><span>Reported arrivals</span><strong>{data.coverage.arrival_reported_pct ?? 0}%</strong></li>
            <li><span>Estimated arrivals</span><strong>{data.coverage.estimated ?? 0}%</strong></li>
            <li><span>Reported departures</span><strong>{data.coverage.departure_reported_pct ?? 0}%</strong></li>
            <li><span>Run quality avg</span><strong>{data.coverage.run_quality_avg ?? 0}</strong></li>
          </ul>
        </div>
      </section>
    </div>
  );
}
