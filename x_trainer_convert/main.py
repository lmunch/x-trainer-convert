#!/usr/bin/env python3
"""X-trainer convert

Convert indoor bike workout data from X-trainer CSV format to TCX

"""

import argparse
import csv
import datetime
import itertools
import math
import re
import sys
from collections import deque
from lxml import etree
from pytz import UTC
from garmin_uploader.workflow import Workflow

version_major = 0
version_minor = 0

xsi = "http://www.w3.org/2001/XMLSchema-instance"

namespaces = {
    None: "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",
    "ns2": "http://www.garmin.com/xmlschemas/UserProfile/v2",
    "ns3": "http://www.garmin.com/xmlschemas/ActivityExtension/v2",
    "ns4": "http://www.garmin.com/xmlschemas/ProfileExtension/v1",
    "ns5": "http://www.garmin.com/xmlschemas/ActivityGoals/v1",
    "xsi": xsi
}


schemalocation = "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2 " \
                 "http://www.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd"


def add_lap_extension(node, lap):
    NS3 = "{" + namespaces['ns3'] + "}"
    extnode = etree.SubElement(node, "Extensions")
    lxnode = etree.SubElement(extnode, NS3 + "LX")
    etree.SubElement(lxnode, NS3 + "AvgSpeed").text = \
        "{0:.4f}".format(lap.AvgSpeedMPS())
    etree.SubElement(lxnode, NS3 + "MaxBikeCadence").text = \
        "{}".format(lap.MaximumCadence())
    etree.SubElement(lxnode, NS3 + "AvgWatts").text = \
        "{}".format(lap.AvgWatts())
    etree.SubElement(lxnode, NS3 + "MaxWatts").text = \
        "{}".format(lap.MaximumWatts())


def add_trackpoint_extension(node, tp):
    NS3 = "{" + namespaces['ns3'] + "}"
    extnode = etree.SubElement(node, "Extensions")
    tpxnode = etree.SubElement(extnode, NS3 + "TPX")
    etree.SubElement(tpxnode, NS3 + "Speed").text = \
        "{0:.4f}".format(tp['km/t'] / 3.6)
    etree.SubElement(tpxnode, NS3 + "RunCadence").text = \
        "{}".format(tp['rpm'])
    etree.SubElement(tpxnode, NS3 + "Watts").text = \
        "{}".format(tp['watt'])


def add_trackpoints(node, lap):
    track = etree.SubElement(node, "Track")
    for tp in lap:
        trackpoint = etree.SubElement(track, "Trackpoint")
        etree.SubElement(trackpoint, "Time").text = \
            str((lap.TimeUTC(tp['time'])))
        etree.SubElement(trackpoint, "AltitudeMeters").text = \
            "{0:.4f}".format(tp['altitude'])
        etree.SubElement(trackpoint, "DistanceMeters").text = \
            "{0:.4f}".format(tp['distance'])

        if tp['pulse']:
            hrnode = etree.SubElement(trackpoint, "HeartRateBpm")
            etree.SubElement(hrnode, "Value").text = \
                "{}".format(tp['pulse'])

        etree.SubElement(trackpoint, "Cadence").text = \
            "{:.0f}".format(tp['rpm'])
        add_trackpoint_extension(trackpoint, tp)


def add_lap(node, lap):
    lapnode = etree.SubElement(node, "Lap", StartTime=str(lap.StartTimeUTC()))
    etree.SubElement(lapnode, "TotalTimeSeconds").text = \
        "{0:.1f}".format(lap.TotalTimeSeconds())
    etree.SubElement(lapnode, "DistanceMeters").text = \
        "{0:.1f}".format(lap.DistanceMeters())
    etree.SubElement(lapnode, "MaximumSpeed").text = \
        "{0:.4f}".format(lap.MaximumSpeedMPS())
    etree.SubElement(lapnode, "Calories").text = "0"

    if lap.AvgHeartRateBpm():
        hrnode = etree.SubElement(lapnode, "AverageHeartRateBpm")
        etree.SubElement(hrnode, "Value").text = \
            "{:.0f}".format(lap.AvgHeartRateBpm())

    if lap.MaximumHeartRateBpm():
        hrnode = etree.SubElement(lapnode, "MaximumHeartRateBpm")
        etree.SubElement(hrnode, "Value").text = \
            "{}".format(lap.MaximumHeartRateBpm())

    etree.SubElement(lapnode, "Intensity").text = \
        lap.Intensity()
    etree.SubElement(lapnode, "Cadence").text = \
        "{:.0f}".format(lap.AvgCadence())
    etree.SubElement(lapnode, "TriggerMethod").text = "Manual"

    add_trackpoints(lapnode, lap)
    add_lap_extension(lapnode, lap)


def add_creator(node):
    XSI = "{" + namespaces['xsi'] + "}"
    creator = etree.SubElement(node, "Creator")
    creator.attrib[XSI + "type"] = "Device_t"
    etree.SubElement(creator, "Name").text = "X-Trainer Studio"
    etree.SubElement(creator, "UnitId").text = "0"
    etree.SubElement(creator, "ProductID").text = "0"
    version = etree.SubElement(creator, "Version")
    etree.SubElement(version, "VersionMajor").text = "1"
    etree.SubElement(version, "VersionMinor").text = "0"
    etree.SubElement(version, "BuildMajor").text = "1"
    etree.SubElement(version, "BuildMinor").text = "0"


def add_author(node):
    XSI = "{" + namespaces['xsi'] + "}"
    author = etree.SubElement(node, "Author")
    author.attrib[XSI + "type"] = "Application_t"
    etree.SubElement(author, "Name").text = "X-Trainer Convert"
    build = etree.SubElement(author, "Build")
    version = etree.SubElement(build, "Version")
    etree.SubElement(version, "VersionMajor").text = str(version_major)
    etree.SubElement(version, "VersionMinor").text = str(version_minor)
    etree.SubElement(version, "BuildMajor").text = "1"
    etree.SubElement(version, "BuildMinor").text = "0"
    etree.SubElement(author, "LangID").text = "en"
    etree.SubElement(author, "PartNumber").text = "XXX-XXXXX-XX"


def write_xml(laps):
    attrib = {"{" + xsi + "}schemaLocation": schemalocation}
    root = etree.Element("TrainingCenterDatabase",
                         attrib=attrib,
                         nsmap=namespaces)
    activities = etree.SubElement(root, "Activities")

    activity = etree.SubElement(activities, "Activity", Sport="Biking")
    etree.SubElement(activity, "Id").text = str(laps[0].StartTimeUTC())
    for lap in laps:
        add_lap(activity, lap)

    add_creator(activity)
    add_author(root)

    tree = etree.ElementTree(root)

    dateFormat = "%Y-%m-%d_%H:%M:%S.tcx"
    filename = laps[0].StartTime().strftime(dateFormat)
    print("Writing TCX file {}->{}: {}".format(laps[0].StartTime(),
                                               laps[-1].EndTime(),
                                               filename))
    tree.write(filename, encoding='utf-8',
               xml_declaration=True, method="xml", pretty_print=True)
    return filename


stat_keys = ['time', 'pulse', 'rpm', 'watt', 'climb%', 'km/t']


def row_is_header(row):
    # First line
    if row[0] == "ver":
        if row[1] != "4":
            raise KeyError("Error: unknown version header")
        return True
    # Second line (column info)
    if row[0] == "col":
        if row[1:] != stat_keys:
            raise KeyError("Error: unknown statistics header")
        return True
    return False


def row_is_totals(row):
    return row[0] == "tot"


def row_is_incomplete(row):
    return len(row) != 6


class Lap(object):
    def __init__(self, starttime, active=True):
        self._starttime = starttime
        self._intensity = "Active" if active else "Resting"
        self._data = []

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        self._iteridx = -1
        return self

    def __next__(self):
        try:
            self._iteridx += 1
            return self._data[self._iteridx]
        except IndexError:
            raise StopIteration

    def _update_from_delta(self, start, key):
        if not self._data:
            return 0.0
        self._data[0][key] = start
        for i, d in enumerate(self._data[1:]):
            d[key] = self._data[i][key] + d[key + '_delta']
        return self._data[-1][key]

    def UpdateDistance(self, start=0.0):
        return self._update_from_delta(start, 'distance')

    def UpdateAltitude(self, start=0.0):
        return self._update_from_delta(start, 'altitude')

    def Intensity(self):
        return self._intensity

    def TimeUTC(self, dt):
        dateFormat = "%Y-%m-%dT%H:%M:%S.000Z"
        return dt.astimezone(UTC).strftime(dateFormat)

    def StartTime(self):
        return self._starttime

    def EndTime(self):
        return self._data[-1]['time'] if self._data else self._starttime

    def StartTimeUTC(self):
        return self.TimeUTC(self.StartTime())

    def EndTimeUTC(self):
        return self.TimeUTC(self.EndTime())

    def XTrainerSample(self, value):
        """Add sample from X-Trainer

        Notes:
          * Exactly one sample per second
          * Hill grade (climb%) is 10*grade
        """
        if self._data:
            onesec = datetime.timedelta(seconds=1)
            value['time'] = onesec + self._data[-1]['time']
        else:
            value['time'] = self._starttime
        distance = value['km/t'] / 3.6
        altitude = distance * math.sin(math.atan(value['climb%'] / 1000.0))
        value['distance_delta'] = distance
        value['altitude_delta'] = altitude
        self._data.append(value)

    def RestSample(self, endtime, pulse):
        if endtime - self.StartTime() > datetime.timedelta(minutes=20):
            raise Exception("Error: rest time greater than 20 minutes")
        while self.EndTime() <= endtime:
            sample = {'pulse': int(pulse), 'rpm': 70, 'watt': 100,
                      'climb%': 0, 'km/t': 15}
            # Assume heart rate drop 20 beats per minute while resting
            pulse = pulse-1/3 if pulse > 130 else 130
            self.XTrainerSample(sample)

    def Sum(self, idx):
        return sum([d[idx] for d in self._data])

    def Avg(self, idx):
        return sum([d[idx] for d in self._data])/float(len(self._data))

    def TotalTimeSeconds(self):
        return (self.EndTime() - self.StartTime()).total_seconds()

    def DistanceMeters(self):
        return self.Sum('distance_delta')

    def HeartRateBpm(self):
        return self._data[-1]['pulse']

    def Minimum(self, idx):
        return min([d[idx] for d in self._data])

    def MinimumAltitude(self):
        return self.Minimum('altitude')

    def Maximum(self, idx):
        return max([d[idx] for d in self._data])

    def MaximumSpeed(self):
        return self.Maximum('km/t')

    def MaximumSpeedMPS(self):
        return self.Maximum('km/t') / 3.6

    def MaximumWatts(self, s=1):
        if s == 1:
            return self.Maximum('watt')
        maxwatt = 0
        q = deque([], s)
        for d in self._data:
            q.append(d['watt'])
            maxwatt = max(maxwatt, sum(q) / s)
        return maxwatt

    def MaximumCadence(self):
        return self.Maximum('rpm')

    def MaximumHeartRateBpm(self):
        return self.Maximum('pulse')

    def AvgSpeed(self):
        return self.Avg('km/t')

    def AvgSpeedMPS(self):
        return self.Avg('km/t') / 3.6

    def AvgWatts(self):
        return self.Avg('watt')

    def AvgCadence(self):
        return self.Avg('rpm')

    def AvgHeartRateBpm(self):
        return self.Avg('pulse')


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


class CustomHelpFormatter(argparse.ArgumentDefaultsHelpFormatter,
                          argparse.RawDescriptionHelpFormatter):
    pass


def parse_arguments():
    description = __doc__.splitlines()[0]
    epilog = "\n".join(__doc__.splitlines()[1:])
    parser = argparse.ArgumentParser(description=description,
                                     epilog=epilog,
                                     formatter_class=CustomHelpFormatter)
    parser.add_argument('files', metavar='FILE', nargs='+',
                        help='CSV files to convert')
    parser.add_argument("-v", "--verbose", default=False, action="store_true",
                        help="verbose output")
    parser.add_argument("--upload", default=False, action="store_true",
                        help="upload to Garmin Connect")
    parser.add_argument("-u", "--username", default=None,
                        help="Garmin Connect user login")
    parser.add_argument("-p", "--password", default=None,
                        help="Garmin Connect user password")
    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()
    files = sorted(set(args.files))
    file_rex = re.compile(".*tr(\d{4})(\d{2})(\d{2})(\d{2})(\d{2}).csv",
                          re.IGNORECASE)
    laps = []
    lap = None
    for f in files:
        m = file_rex.match(f)
        if not m:
            raise KeyError("Error: unknown file naming format: {}".format(f))
        starttime = datetime.datetime(int(m.group(1)), int(m.group(2)),
                                      int(m.group(3)), int(m.group(4)),
                                      int(m.group(5)))

        # Collapse close (5sec) or overlapping laps
        if laps:
            tdelta = starttime - laps[-1].EndTime()
            lap = laps.pop() if tdelta.total_seconds() < 5 else None
        if not lap:
            lap = Lap(starttime)

        with open(f, newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            for row in reader:
                if row_is_header(row):
                    continue
                if row_is_totals(row):
                    break
                if row_is_incomplete(row):
                    continue
                values = dict(zip(stat_keys, [int(n) for n in row]))
                lap.XTrainerSample(values)

        # Use lap but only if it has data
        if len(lap):
            laps.append(lap)

    # Split into sessions (more than 20 minutes in between laps)
    lapsplit = [idx for idx, (l1, l2) in enumerate(pairwise(laps), 1)
                if l2.StartTime() - l1.EndTime() > datetime.timedelta(minutes=20)]
    lapsplit = [0] + lapsplit + [len(laps)]
    sessions = [laps[i:j] for i, j in pairwise(lapsplit)]

    tcx_files = []
    for laps in sessions:
        # Add rest laps
        restlaps = []
        for l1, l2 in pairwise(laps):
            restlap = Lap(l1.EndTime() + datetime.timedelta(seconds=1), False)
            restlap.RestSample(l2.StartTime() - datetime.timedelta(seconds=1),
                               l1.HeartRateBpm())
            restlaps.append(restlap)
        for idx, restlap in enumerate(restlaps, 1):
            laps.insert(idx*2-1, restlap)

        # Recalculate distance and altitude
        start_distance = start_altitude = 0.0
        for lap in laps:
            start_distance = lap.UpdateDistance(start_distance)
            start_altitude = lap.UpdateAltitude(start_altitude)

        # Garmin altitude graph does not like altitudes below -500m, hence
        # adjust altitude to have 10m as lowest point
        start_altitude = 10.0 - min([lap.MinimumAltitude() for lap in laps])
        for lap in laps:
            start_altitude = lap.UpdateAltitude(start_altitude)

        tcx_file = write_xml(laps)
        tcx_files.append(tcx_file)
        totsec = sum([l.TotalTimeSeconds() for l in laps])
        print("active time: {}".format(datetime.timedelta(seconds=totsec)))

        totdist = sum([l.DistanceMeters() for l in laps])
        print("total distance: {0:.2f}km".format(totdist/1000))

        totwatt = sum([l.Sum('watt') for l in laps])
        totlen = sum([len(l) for l in laps])
        print("avg watt: {0:.2f}W".format(totwatt/totlen))

        for i in [1, 10, 30, 60, 120]:
            print("max {}s watt: {:.0f}W".
                  format(i, max([l.MaximumWatts(i) for l in laps])))
        print("max speed: {}km/t".format(max([l.MaximumSpeed() for l in laps])))

    if args.upload and tcx_files:
        for tcx in tcx_files:
            try:
                workflow = Workflow([tcx], args.username, args.password,
                                    activity_type="indoor_cycling",
                                    activity_name="X-trainer indoor cycling",
                                    verbose=5 if args.verbose else 2)
                workflow.run()
            except Exception as e:
                print("Error: {}".format(str(e)))
                sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
