const StatsCard = ({ label, value, icon: Icon, color, onClick }) => {
    return (
        <div className="stats-card" onClick={onClick} style={{ cursor: onClick ? 'pointer' : 'default' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <span className="stats-label">{label}</span>
                    <span className="stats-value">{value}</span>
                </div>
                <div style={{
                    background: `${color}15`,
                    padding: '0.75rem',
                    borderRadius: 'var(--radius-md)',
                    color: color,
                    border: `1px solid ${color}30`
                }}>
                    {Icon && <Icon size={22} />}
                </div>
            </div>
            <div style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                height: '3px',
                width: '100%',
                background: `linear-gradient(90deg, ${color}, transparent)`
            }} />
        </div>
    );
};

export default StatsCard;

