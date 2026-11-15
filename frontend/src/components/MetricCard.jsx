export default function MetricCard({
  title,
  value,
  change,
  icon: Icon,
  color,
  description
}) {
  return (
    <article className="metric-card">
      <div className="metric-top">
        <span>{title}</span>

        <div className={`metric-icon ${color}`}>
          <Icon size={19} />
        </div>
      </div>

      <h3>{value}</h3>

      <div className="metric-footer">
        <span className="metric-change">{change}</span>
        <span>{description}</span>
      </div>
    </article>
  );
}