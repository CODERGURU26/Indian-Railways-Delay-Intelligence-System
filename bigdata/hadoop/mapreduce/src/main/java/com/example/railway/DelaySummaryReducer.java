package com.example.railway;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;

import java.io.IOException;

public class DelaySummaryReducer extends Reducer<Text, Text, Text, Text> {
    @Override
    protected void reduce(Text key, Iterable<Text> values, Context context)
            throws IOException, InterruptedException {
        long validDelayCount = 0L;
        double arrivalSum = 0.0;
        double departureSum = 0.0;
        double maxArrival = Double.NEGATIVE_INFINITY;
        double maxDeparture = Double.NEGATIVE_INFINITY;
        long reportedCount = 0L;
        long estimatedCount = 0L;

        for (Text value : values) {
            String[] parts = value.toString().split(",", -1);
            if (parts.length < 5) {
                continue;
            }

            double arrival = parseNullableDouble(parts[0]);
            double departure = parseNullableDouble(parts[1]);
            long reported = parseLong(parts[2]);
            long estimated = parseLong(parts[3]);
            long recordCount = parseLong(parts[4]);

            if (!Double.isNaN(arrival)) {
                validDelayCount += recordCount;
                arrivalSum += arrival;
                if (arrival > maxArrival) {
                    maxArrival = arrival;
                }
            }

            if (!Double.isNaN(departure)) {
                departureSum += departure;
                if (departure > maxDeparture) {
                    maxDeparture = departure;
                }
            }

            reportedCount += reported;
            estimatedCount += estimated;
        }

        double avgArrival = validDelayCount == 0 ? 0 : arrivalSum / validDelayCount;
        double avgDeparture = validDelayCount == 0 ? 0 : departureSum / validDelayCount;
        if (Double.isInfinite(maxArrival)) {
            maxArrival = 0.0;
        }
        if (Double.isInfinite(maxDeparture)) {
            maxDeparture = 0.0;
        }

        String output = String.format("%d,%.2f,%.2f,%.2f,%.2f,%d,%d",
                validDelayCount,
                avgArrival,
                maxArrival,
                avgDeparture,
                maxDeparture,
                reportedCount,
                estimatedCount);
        context.write(key, new Text(output));
    }

    private double parseNullableDouble(String value) {
        if (value == null || value.isBlank() || value.equalsIgnoreCase("null")) {
            return Double.NaN;
        }
        try {
            return Double.parseDouble(value);
        } catch (NumberFormatException ex) {
            return Double.NaN;
        }
    }

    private long parseLong(String value) {
        if (value == null || value.isBlank() || value.equalsIgnoreCase("null")) {
            return 0L;
        }
        try {
            return Long.parseLong(value);
        } catch (NumberFormatException ex) {
            return 0L;
        }
    }
}
