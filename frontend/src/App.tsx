import { useEffect, useState } from 'react';
import { BarChart, Bar, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const API_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

type SummaryRow = {
  label: string;
  value: number;
  count?: number;
};

type AnalyticsPayload = {
  trains: SummaryRow[];
  stations: SummaryRow[];
  categories: SummaryRow[];
  coverage: Record<string, number>;
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
      </header>

      <section className="stats-grid">
        <div className="card">
          <span>Reported coverage</span>
          <strong>{data.coverage.reported ?? 0}%</strong>
        </div>
        <div className="card">
          <span>Estimated coverage</span>
          <strong>{data.coverage.estimated ?? 0}%</strong>
        </div>
        <div className="card">
          <span>Run quality avg</span>
          <strong>{data.coverage.run_quality_avg ?? 0}</strong>
        </div>
      </section>

      <section className="charts-grid">
        <div className="panel">
          <h2>Top train delays</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.trains}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <h2>Top station delays</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.stations}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="list-grid">
        <div className="panel">
          <h2>Category averages</h2>
          <ul>
            {data.categories.map((item) => (
              <li key={item.label}><span>{item.label}</span><strong>{item.value} min</strong></li>
            ))}
          </ul>
        </div>

        <div className="panel">
          <h2>Coverage notes</h2>
          <ul>
            <li><span>Reported</span><strong>{data.coverage.reported ?? 0}%</strong></li>
            <li><span>Estimated</span><strong>{data.coverage.estimated ?? 0}%</strong></li>
            <li><span>Run quality avg</span><strong>{data.coverage.run_quality_avg ?? 0}</strong></li>
          </ul>
        </div>
      </section>
    </div>
  );
}
