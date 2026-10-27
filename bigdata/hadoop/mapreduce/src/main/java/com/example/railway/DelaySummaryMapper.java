package com.example.railway;

import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;

public class DelaySummaryMapper extends Mapper<LongWritable, Text, Text, Text> {
    @Override
    protected void map(LongWritable key, Text value, Context context)
            throws IOException, InterruptedException {
        String line = value.toString().trim();
        if (line.isEmpty() || line.startsWith("train_number,")) {
            return;
        }

        String[] fields = line.split(",(?=(?:[^"]*\"[^"]*\")*[^"]*$)", -1);
        if (fields.length < 16) {
            return;
        }

        String trainNumber = fields[0].trim();
        String arrivalDelay = fields[12].trim();
        String departureDelay = fields[13].trim();
        String arrivalReported = fields[11].trim();
        String departureReported = fields[12].trim();

        if (trainNumber.isEmpty()) {
            return;
        }

        double arrival = parseNullableDouble(arrivalDelay);
        double departure = parseNullableDouble(departureDelay);
        int reported = parseBooleanFlag(arrivalReported) || parseBooleanFlag(departureReported) ? 1 : 0;
        int estimated = (!parseBooleanFlag(arrivalReported) && !parseBooleanFlag(departureReported)) ? 1 : 0;

        String payload = String.format("%s,%s,%s,%s,%s",
                Double.isNaN(arrival) ? "" : String.valueOf(arrival),
                Double.isNaN(departure) ? "" : String.valueOf(departure),
                reported,
                estimated,
                1);
        context.write(new Text(trainNumber), new Text(payload));
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

    private boolean parseBooleanFlag(String value) {
        if (value == null || value.isBlank() || value.equalsIgnoreCase("null")) {
            return false;
        }
        return Boolean.parseBoolean(value);
    }
}
