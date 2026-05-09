import { Card, CardDescription, CardTitle } from "@biased/ui";

import { ForecastLab } from "@/components/forecast-lab";

export default function PlannerPage() {
  return (
    <div className="space-y-6">
      <Card className="space-y-3">
        <CardTitle className="text-3xl">
          Forecasting and scenario planning
        </CardTitle>
        <CardDescription className="max-w-3xl text-base leading-7">
          Build owner confidence with practical forecasts, fixed scenario
          templates, and scheduled daily briefs before making reorder or cash
          decisions.
        </CardDescription>
      </Card>

      <ForecastLab />
    </div>
  );
}
