import { useEffect, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const API_URL = (import.meta as ImportMeta & { env?: { VITE_API_BASE_URL?: string } }).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8001';

type SummaryRow = {
  label: string;
  value: number | null;
  departure_value?: number | null;
  count?: number;
  departure_count?: number;
  percentage?: number;
};

type AnalyticsPayload = {
  trains: SummaryRow[];
  stations: SummaryRow[];
  categories: SummaryRow[];
  monthly_trends: SummaryRow[];
  routes: SummaryRow[];
  sequence: SummaryRow[];
  delay_distribution: SummaryRow[];
  coverage: {
    arrival_reported_pct: number | null;
    departure_reported_pct: number | null;
    run_quality_avg: number | null;
  };
  kpis: {
    mean_arrival_delay_min: number | null;
    mean_departure_delay_min: number | null;
    severe_arrival_pct: number;
  };
  insights: { title: string; value: string; detail: string }[];
  quality: Record<string, string | number | null>;
  totals: {
    records: number;
    trains: number;
    stations: number;
    journeys: number;
    start_date: string | null;
    end_date: string | null;
  };
  data_source: string;
};

type StationInfo = {
  code: string;
  name: string | null;
  region: string | null;
  stop_records: number;
  arrival_observations: number;
  departure_observations: number;
  avg_arrival_delay_min: number | null;
  avg_departure_delay_min: number | null;
};

type StationDirectory = {
  stations: StationInfo[];
  total: number;
  mapped: number;
  unmapped: number;
  mapping_source: string;
};

const DELAY_COLORS: Record<string, string> = {
  'Early or on time': '#22c55e',
  '1-15 min': '#38bdf8',
  '16-60 min': '#f59e0b',
  'Over 60 min': '#ef4444',
};

const number = (value: number | null | undefined, digits = 2) =>
  value == null ? 'N/A' : value.toLocaleString(undefined, { maximumFractionDigits: digits });

export default function App() {
  const [data, setData] = useState<AnalyticsPayload | null>(null);
  const [stationDirectory, setStationDirectory] = useState<StationDirectory | null>(null);
  const [stationQuery, setStationQuery] = useState('');
  const [selectedStationCode, setSelectedStationCode] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const [summaryResponse, stationResponse] = await Promise.all([
          fetch(`${API_URL}/summary`),
          fetch(`${API_URL}/stations`),
        ]);
        if (!summaryResponse.ok || !stationResponse.ok) {
          throw new Error(`Analytics HTTP ${summaryResponse.status}; stations HTTP ${stationResponse.status}`);
        }
        const [summary, directory] = await Promise.all([
          summaryResponse.json(),
          stationResponse.json(),
        ]);
        setData(summary);
        setStationDirectory(directory);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load dashboard data');
      }
    };

    fetchSummary();
  }, []);

  const filteredStations = (stationDirectory?.stations ?? [])
    .filter((station) => {
      const query = stationQuery.trim().toLocaleUpperCase();
      return !query
        || station.code.toLocaleUpperCase().includes(query)
        || station.name?.toLocaleUpperCase().includes(query);
    })
    .slice(0, 12);
  const selectedStation = stationDirectory?.stations.find(
    (station) => station.code === selectedStationCode,
  ) ?? null;

  if (error) {
    return <div className="error">Unable to fetch analytics: {error}</div>;
  }

  if (!data) {
    return <div className="loading">Loading one-year railway delay analysis...</div>;
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Indian Railways Delay Intelligence</h1>
        <p>One-year delay analysis · {data.totals.start_date} to {data.totals.end_date}</p>
        <p className="data-source">Data source: {data.data_source}</p>
        <p className="chart-caption">
          All source rows are retained. Blank fields are normalized; missing delays are excluded from delay averages.
          Extreme delay values are not clipped.
        </p>
      </header>

      <section className="panel station-directory-panel station-directory-top">
        <div className="station-directory-heading">
          <div>
            <span className="section-eyebrow">Explore station performance</span>
            <h2>Station code directory</h2>
            <p className="chart-caption">
              Search for a station and select it to see its full name and one-year delay averages.
              Matched {stationDirectory?.mapped.toLocaleString()} of {stationDirectory?.total.toLocaleString()} dataset stations.
            </p>
          </div>
          <span className="station-directory-count">{stationDirectory?.total.toLocaleString()} stations</span>
        </div>
        <label className="station-search-label" htmlFor="station-search">Search by station code or name</label>
        <input
          id="station-search"
          className="station-search"
          type="search"
          value={stationQuery}
          onChange={(event) => {
            setStationQuery(event.target.value);
            setSelectedStationCode(null);
          }}
          placeholder="e.g. NDLS or New Delhi"
        />
        <ul className="station-results">
          {filteredStations.map((station) => (
            <li key={station.code}>
              <button
                type="button"
                className={`station-result${station.code === selectedStationCode ? ' station-result-selected' : ''}`}
                onClick={() => setSelectedStationCode(station.code)}
                aria-pressed={station.code === selectedStationCode}
              >
                <span className="station-result-code">{station.code}</span>
                <span className="station-result-name">{station.name ?? 'Station name not found in reference'}</span>
                <span className="station-result-delay">
                  {station.avg_arrival_delay_min == null ? 'N/A' : `${number(station.avg_arrival_delay_min)} min`}
                  <small>avg arrival</small>
                </span>
              </button>
            </li>
          ))}
          {filteredStations.length === 0 && (
            <li><span className="station-empty">No station codes or names match this search.</span></li>
          )}
        </ul>
        {selectedStation && (
          <div className="station-detail" aria-live="polite">
            <div className="station-detail-heading">
              <span className="station-detail-code">{selectedStation.code}</span>
              <div>
                <h3>{selectedStation.name ?? 'Station name unavailable'}</h3>
                <p>{selectedStation.region ? `Region ${selectedStation.region} · ` : ''}{selectedStation.stop_records.toLocaleString()} stop records in the year</p>
              </div>
            </div>
            <div className="station-detail-metrics">
              <div>
                <span>Average arrival delay</span>
                <strong>{selectedStation.avg_arrival_delay_min == null ? 'N/A' : `${number(selectedStation.avg_arrival_delay_min)} min`}</strong>
                <small>{selectedStation.arrival_observations.toLocaleString()} recorded arrivals</small>
              </div>
              <div>
                <span>Average departure delay</span>
                <strong>{selectedStation.avg_departure_delay_min == null ? 'N/A' : `${number(selectedStation.avg_departure_delay_min)} min`}</strong>
                <small>{selectedStation.departure_observations.toLocaleString()} recorded departures</small>
              </div>
            </div>
          </div>
        )}
        <p className="chart-caption station-source">
          Name reference: {stationDirectory?.mapping_source}. Unmatched codes are identified rather than guessed.
        </p>
      </section>

      <section className="stats-grid">
        <div className="card"><span>Stop records</span><strong>{data.totals.records.toLocaleString()}</strong></div>
        <div className="card"><span>Train journeys</span><strong>{data.totals.journeys.toLocaleString()}</strong></div>
        <div className="card"><span>Unique trains</span><strong>{data.totals.trains.toLocaleString()}</strong></div>
        <div className="card"><span>Unique stations</span><strong>{data.totals.stations.toLocaleString()}</strong></div>
        <div className="card"><span>Mean arrival delay / journey</span><strong>{number(data.kpis.mean_arrival_delay_min)} min</strong></div>
        <div className="card"><span>Mean departure delay / journey</span><strong>{number(data.kpis.mean_departure_delay_min)} min</strong></div>
        <div className="card"><span>Arrivals over 60 min late</span><strong>{number(data.kpis.severe_arrival_pct)}%</strong></div>
      </section>

      <section className="charts-grid">
        <div className="panel chart-panel">
          <h2>Highest-delay trains</h2>
          <p className="chart-caption">Average arrival delay per journey · only trains with at least 10 journeys</p>
          <ResponsiveContainer width="100%" height={380}>
            <BarChart data={data.trains} layout="vertical" margin={{ left: 12, right: 24 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" unit=" min" />
              <YAxis type="category" dataKey="label" width={76} />
              <Tooltip formatter={(value) => [`${number(Number(value))} min`, 'Mean arrival delay']} />
              <Bar dataKey="value" fill="#ef4444" barSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel chart-panel">
          <h2>Highest-delay stations</h2>
          <p className="chart-caption">Stop-level arrival and departure averages · at least 100 observations per station</p>
          <ResponsiveContainer width="100%" height={380}>
            <BarChart data={data.stations} layout="vertical" margin={{ left: 12, right: 24 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" unit=" min" />
              <YAxis type="category" dataKey="label" width={76} />
              <Tooltip formatter={(value) => [`${number(Number(value))} min`]} />
              <Legend />
              <Bar dataKey="value" name="Arrival" fill="#3b82f6" barSize={14} />
              <Bar dataKey="departure_value" name="Departure" fill="#22c55e" barSize={14} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel chart-panel chart-panel-wide">
          <h2>Monthly delay trend</h2>
          <p className="chart-caption">Journey-weighted mean station delay · each journey counts equally within its start month</p>
          <ResponsiveContainer width="100%" height={380}>
            <LineChart data={data.monthly_trends} margin={{ top: 12, right: 24, bottom: 8, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis unit=" min" />
              <Tooltip formatter={(value) => [`${number(Number(value))} min`]} />
              <Legend />
              <Line type="monotone" dataKey="value" name="Arrival" stroke="#f97316" strokeWidth={3} dot={{ r: 4 }} connectNulls />
              <Line type="monotone" dataKey="departure_value" name="Departure" stroke="#14b8a6" strokeWidth={3} dot={{ r: 4 }} connectNulls />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="panel chart-panel">
          <h2>Delay by train category</h2>
          <p className="chart-caption">Journey-weighted average delays by source category</p>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={data.categories}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis unit=" min" />
              <Tooltip formatter={(value) => [`${number(Number(value))} min`]} />
              <Legend />
              <Bar dataKey="value" name="Arrival" fill="#a78bfa" />
              <Bar dataKey="departure_value" name="Departure" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel chart-panel">
          <h2>Arrival delay bands</h2>
          <p className="chart-caption">Stop-level observations grouped by lateness; missing delays are excluded</p>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={data.delay_distribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" />
              <YAxis />
              <Tooltip formatter={(value, _name, item) => [
                `${Number(value).toLocaleString()} stops (${number(item.payload.percentage)}%)`,
                'Arrival observations',
              ]} />
              <Bar dataKey="count" name="Stop records">
                {data.delay_distribution.map((item) => (
                  <Cell key={item.label} fill={DELAY_COLORS[item.label] ?? '#64748b'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel chart-panel chart-panel-wide">
          <h2>Arrival delay by stop sequence</h2>
          <p className="chart-caption">Mean recorded stop arrival delay across the one-year period</p>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={data.sequence} margin={{ top: 12, right: 24, bottom: 8, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" label={{ value: 'Stop sequence', position: 'insideBottom', offset: -4 }} />
              <YAxis unit=" min" />
              <Tooltip formatter={(value) => [`${number(Number(value))} min`, 'Arrival delay']} />
              <Line type="monotone" dataKey="value" name="Arrival delay" stroke="#38bdf8" strokeWidth={3} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="list-grid">
        <div className="panel">
          <h2>Meaningful insights</h2>
          <ul>
            {data.insights.map((item) => (
              <li key={item.title}><span>{item.title}<small>{item.detail}</small></span><strong>{item.value}</strong></li>
            ))}
          </ul>
        </div>

        <div className="panel">
          <h2>Project Q&amp;A</h2>
          <ul>
            <li><span>Which train has the highest average arrival delay?<small>Only trains with at least 10 journeys are ranked.</small></span><strong>{data.trains[0]?.label ?? 'N/A'} · {number(data.trains[0]?.value)} min</strong></li>
            <li><span>Which station has the highest arrival delay?<small>Stations need at least 100 recorded arrivals.</small></span><strong>{data.stations[0]?.label ?? 'N/A'} · {number(data.stations[0]?.value)} min</strong></li>
            <li><span>Which month had the highest average delay?<small>Arrival delay averaged per journey.</small></span><strong>{data.insights.find((item) => item.title === 'Highest-delay month')?.value ?? 'N/A'}</strong></li>
            <li><span>What share of arrivals were over one hour late?<small>Calculated from non-missing stop arrival delays.</small></span><strong>{number(data.kpis.severe_arrival_pct)}%</strong></li>
            <li><span>What is the date range analyzed?<small>Historical config selected for this analysis.</small></span><strong>{data.totals.start_date} – {data.totals.end_date}</strong></li>
          </ul>
        </div>

        <div className="panel">
          <h2>Data quality &amp; coverage</h2>
          <ul>
            <li><span>Source rows retained</span><strong>{Number(data.quality.retained_rows ?? data.totals.records).toLocaleString()}</strong></li>
            <li><span>Rows missing train number</span><strong>{Number(data.quality.missing_train_number ?? 0).toLocaleString()}</strong></li>
            <li><span>Rows missing station code</span><strong>{Number(data.quality.missing_station_code ?? 0).toLocaleString()}</strong></li>
            <li><span>Negative arrival delay observations</span><strong>{Number(data.quality.negative_arrival_delays ?? 0).toLocaleString()}</strong></li>
            <li><span>Reported arrival coverage</span><strong>{number(data.coverage.arrival_reported_pct)}%</strong></li>
            <li><span>Reported departure coverage</span><strong>{number(data.coverage.departure_reported_pct)}%</strong></li>
          </ul>
          <p className="chart-caption">Quality anomalies are reported, not automatically discarded.</p>
        </div>

        <div className="panel">
          <h2>Most delayed recurring routes</h2>
          <p className="chart-caption">At least 20 matching journeys; journey averages weighted equally</p>
          <ul>
            {data.routes.map((item) => (
              <li key={item.label}><span>{item.label}<small>{item.count?.toLocaleString()} journeys</small></span><strong>{number(item.value)} min</strong></li>
            ))}
          </ul>
        </div>

      </section>
    </div>
  );
}
