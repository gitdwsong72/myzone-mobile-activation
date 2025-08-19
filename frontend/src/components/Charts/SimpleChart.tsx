import React from 'react';
import './SimpleChart.css';

interface ChartData {
  label: string;
  value: number;
  color?: string;
}

interface SimpleChartProps {
  data: ChartData[];
  type: 'bar' | 'line' | 'pie';
  title?: string;
  height?: number;
  showValues?: boolean;
}

const SimpleChart: React.FC<SimpleChartProps> = ({
  data,
  type,
  title,
  height = 300,
  showValues = true
}) => {
  const maxValue = Math.max(...data.map(d => d.value));
  const colors = [
    '#667eea', '#764ba2', '#f093fb', '#f5576c',
    '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
    '#ffecd2', '#fcb69f', '#a8edea', '#fed6e3'
  ];

  const renderBarChart = () => (
    <div className="bar-chart" style={{ height }}>
      <div className="chart-bars">
        {data.map((item, index) => (
          <div key={index} className="bar-container">
            <div 
              className="bar"
              style={{
                height: `${(item.value / maxValue) * 80}%`,
                backgroundColor: item.color || colors[index % colors.length]
              }}
            >
              {showValues && (
                <span className="bar-value">{item.value.toLocaleString()}</span>
              )}
            </div>
            <span className="bar-label">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );

  const renderLineChart = () => {
    const points = data.map((item, index) => ({
      x: (index / (data.length - 1)) * 100,
      y: 100 - (item.value / maxValue) * 80
    }));

    const pathData = points.map((point, index) => 
      `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`
    ).join(' ');

    return (
      <div className="line-chart" style={{ height }}>
        <svg width="100%" height="80%" viewBox="0 0 100 100" preserveAspectRatio="none">
          <path
            d={pathData}
            fill="none"
            stroke={colors[0]}
            strokeWidth="2"
            vectorEffect="non-scaling-stroke"
          />
          {points.map((point, index) => (
            <circle
              key={index}
              cx={point.x}
              cy={point.y}
              r="3"
              fill={colors[0]}
              vectorEffect="non-scaling-stroke"
            />
          ))}
        </svg>
        <div className="line-labels">
          {data.map((item, index) => (
            <span key={index} className="line-label">
              {item.label}
            </span>
          ))}
        </div>
      </div>
    );
  };

  const renderPieChart = () => {
    const total = data.reduce((sum, item) => sum + item.value, 0);
    let currentAngle = 0;

    return (
      <div className="pie-chart" style={{ height }}>
        <div className="pie-container">
          <svg width="200" height="200" viewBox="0 0 200 200">
            {data.map((item, index) => {
              const percentage = (item.value / total) * 100;
              const angle = (item.value / total) * 360;
              const startAngle = currentAngle;
              const endAngle = currentAngle + angle;
              
              const x1 = 100 + 80 * Math.cos((startAngle - 90) * Math.PI / 180);
              const y1 = 100 + 80 * Math.sin((startAngle - 90) * Math.PI / 180);
              const x2 = 100 + 80 * Math.cos((endAngle - 90) * Math.PI / 180);
              const y2 = 100 + 80 * Math.sin((endAngle - 90) * Math.PI / 180);
              
              const largeArcFlag = angle > 180 ? 1 : 0;
              
              const pathData = [
                `M 100 100`,
                `L ${x1} ${y1}`,
                `A 80 80 0 ${largeArcFlag} 1 ${x2} ${y2}`,
                'Z'
              ].join(' ');
              
              currentAngle += angle;
              
              return (
                <path
                  key={index}
                  d={pathData}
                  fill={item.color || colors[index % colors.length]}
                  stroke="white"
                  strokeWidth="2"
                />
              );
            })}
          </svg>
        </div>
        <div className="pie-legend">
          {data.map((item, index) => (
            <div key={index} className="legend-item">
              <div 
                className="legend-color"
                style={{ backgroundColor: item.color || colors[index % colors.length] }}
              />
              <span className="legend-label">{item.label}</span>
              <span className="legend-value">
                {item.value.toLocaleString()} ({((item.value / total) * 100).toFixed(1)}%)
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="simple-chart">
      {title && <h3 className="chart-title">{title}</h3>}
      <div className="chart-content">
        {type === 'bar' && renderBarChart()}
        {type === 'line' && renderLineChart()}
        {type === 'pie' && renderPieChart()}
      </div>
    </div>
  );
};

export default SimpleChart;