CREATE OR REFRESH STREAMING TABLE ${user_name}_eurex_daily_stats 
COMMENT "Raw Eurex daily stats data streamed in from CSV files."
AS SELECT * FROM 
  STREAM READ_FILES("/Volumes/${catalog}/${schema}/${volume}/*.csv", FORMAT => "csv");