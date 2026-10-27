package com.example.railway;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

import java.io.IOException;

public class DelaySummaryJob {
    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            System.err.println("Usage: DelaySummaryJob <input_dir> <output_dir>");
            System.exit(2);
        }

        Configuration conf = new Configuration();
        Job job = Job.getInstance(conf, "railway-delay-summary");
        job.setJarByClass(DelaySummaryJob.class);
        job.setMapperClass(DelaySummaryMapper.class);
        job.setReducerClass(DelaySummaryReducer.class);
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);

        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));

        boolean success = job.waitForCompletion(true);
        System.exit(success ? 0 : 1);
    }
}
