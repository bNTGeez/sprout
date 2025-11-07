"use client";

import { useMemo, useState } from "react";
import {
  PieChart,
  Pie,
  Sector,
  Cell,
  ResponsiveContainer,
  Legend,
} from "recharts";
import Card from "@/app/components/Card";

interface SpendingItem {
  category: string;
  amount: number;
}

interface SpendingBreakdownProps {
  data: SpendingItem[];
}

const COLORS = [
  "#3B82F6",
  "#10B981",
  "#F59E0B",
  "#EF4444",
  "#8B5CF6",
  "#EC4899",
  "#06B6D4",
];

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
};

type ActiveShapeProps = {
  cx: number;
  cy: number;
  midAngle: number;
  innerRadius: number;
  outerRadius: number;
  startAngle: number;
  endAngle: number;
  fill: string;
  payload: any;
  percent: number;
  value: number;
};

const renderActiveShape = (props: ActiveShapeProps) => {
  const RAD = Math.PI / 180;
  const {
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    startAngle,
    endAngle,
    fill,
    payload,
    percent,
    value,
  } = props;

  const sin = Math.sin(-RAD * midAngle);
  const cos = Math.cos(-RAD * midAngle);
  const sx = cx + (outerRadius + 10) * cos;
  const sy = cy + (outerRadius + 10) * sin;
  const mx = cx + (outerRadius + 30) * cos;
  const my = cy + (outerRadius + 30) * sin;
  const ex = mx + (cos >= 0 ? 1 : -1) * 22;
  const ey = my;
  const textAnchor = cos >= 0 ? "start" : "end";

  return (
    <g>
      <text
        x={cx}
        y={cy}
        dy={8}
        textAnchor="middle"
        fill={fill}
        className="text-sm font-semibold"
      >
        {payload.name}
      </text>
      <Sector
        {...{ cx, cy, innerRadius, startAngle, endAngle }}
        outerRadius={outerRadius + 6}
        fill={fill}
      />
      <Sector
        {...{ cx, cy, startAngle, endAngle }}
        innerRadius={outerRadius + 6}
        outerRadius={outerRadius + 10}
        fill={fill}
        opacity={0.25}
      />
      <path
        d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`}
        stroke={fill}
        fill="none"
      />
      <circle cx={ex} cy={ey} r={2} fill={fill} />
      <text
        x={ex + (cos >= 0 ? 12 : -12)}
        y={ey}
        textAnchor={textAnchor}
        className="text-xs fill-neutral-800 font-semibold"
      >
        {formatCurrency(value)}
      </text>
      <text
        x={ex + (cos >= 0 ? 12 : -12)}
        y={ey}
        dy={16}
        textAnchor={textAnchor}
        className="text-[10px] fill-neutral-500"
      >
        {(percent * 100).toFixed(0)}%
      </text>
    </g>
  );
};

export default function SpendingBreakdown({ data }: SpendingBreakdownProps) {
  const [activeIndex, setActiveIndex] = useState<number>(-1);

  const currency = useMemo(
    () =>
      new Intl.NumberFormat(undefined, {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 0,
      }),
    []
  );

  const { chartData, total } = useMemo(() => {
    const total = data.reduce((s, d) => s + Math.max(0, d.amount), 0);
    const chartData = data.map((d, i) => {
      const value = Math.max(0, d.amount);
      return {
        name: d.category,
        value,
        pct: total ? (value / total) * 100 : 0,
        fill: COLORS[i % COLORS.length],
      };
    });
    return { chartData, total };
  }, [data]);

  if (!total) {
    return (
      <Card>
        <h2 className="text-lg font-bold text-gray-900 mb-2">
          Spending Breakdown
        </h2>
        <p className="text-sm text-gray-500">
          No spending data for this period.
        </p>
      </Card>
    );
  }

  return (
    <Card>
      <h2 className="text-lg font-bold text-gray-900 mb-4">
        Spending Breakdown
      </h2>
      <div className="w-full h-[320px] sm:h-[380px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={70}
              outerRadius={110}
              {...({
                activeIndex,
                activeShape: renderActiveShape,
              } as any)}
              onMouseEnter={(_, idx) => setActiveIndex(idx)}
              onMouseLeave={() => setActiveIndex(-1)}
              paddingAngle={3}
            >
              {chartData.map((d) => (
                <Cell key={d.name} fill={d.fill} />
              ))}
            </Pie>
            <Legend
              verticalAlign="bottom"
              height={36}
              formatter={(value: string, entry: any) => {
                const payload = entry?.payload as {
                  value: number;
                  pct: number;
                };
                return (
                  <span style={{ color: entry?.color || "#000" }}>
                    {value}: {currency.format(payload.value)} (
                    {payload.pct.toFixed(0)}%)
                  </span>
                );
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
