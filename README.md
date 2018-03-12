# X-trainer Convert
Convert indoor bike workout data from X-trainer format to TCX.

X-trainer studio in Bagsværd, Denmark http://www.x-trainer-studio.dk/ uses the
X-Trainer bike computer on the Body Bikes for logging workout data. Workout
data is logged to the athletes SD card in a simple CSV format. This tool can
convert the logged data into TCX format which can be uploaded to Strava,
Garmin, Endomondo and more.

Note: When the time is stopped during rest periods in between intervals
nothing is logged. To compensate for for this dummy rest data is inserted. The
dummy rest data is 130BPM, 15KM/t, 100W and 70RPM. The heart rate is assumed
to drop 20 beats per minute while resting until reaching 130. This can cause a
slightly different training impulse score than the actual one.
