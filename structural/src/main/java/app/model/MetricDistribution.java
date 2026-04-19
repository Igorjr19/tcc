package app.model;

import java.util.Collections;
import java.util.List;

/**
 * Distribuição estatística de uma métrica numérica.
 */
public class MetricDistribution {
    private double min;
    private double max;
    private double mean;
    private double median;
    private double stddev;

    public MetricDistribution() {}

    public static MetricDistribution fromValues(List<Double> values) {
        MetricDistribution d = new MetricDistribution();
        if (values.isEmpty()) return d;

        Collections.sort(values);
        int n = values.size();

        d.min = values.get(0);
        d.max = values.get(n - 1);
        d.mean = values.stream().mapToDouble(Double::doubleValue).average().orElse(0);

        if (n % 2 == 0) {
            d.median = (values.get(n / 2 - 1) + values.get(n / 2)) / 2.0;
        } else {
            d.median = values.get(n / 2);
        }

        double sumSqDiff = values.stream()
                .mapToDouble(v -> Math.pow(v - d.mean, 2))
                .sum();
        d.stddev = Math.sqrt(sumSqDiff / n);

        // Arredonda para 2 casas
        d.min = round(d.min);
        d.max = round(d.max);
        d.mean = round(d.mean);
        d.median = round(d.median);
        d.stddev = round(d.stddev);

        return d;
    }

    private static double round(double value) {
        return Math.round(value * 100.0) / 100.0;
    }

    public double getMin() { return min; }
    public double getMax() { return max; }
    public double getMean() { return mean; }
    public double getMedian() { return median; }
    public double getStddev() { return stddev; }
}
